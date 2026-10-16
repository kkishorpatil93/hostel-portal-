"""Authentication routes: Login, Resident Login, Logout, Register, Password Reset."""

from datetime import UTC, datetime

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.auth import auth_bp
from app.extensions import db, limiter
from app.models.user import User, UserRole


def _is_safe_redirect(target):
    """Ensure redirect target is a safe internal relative path."""
    if not target:
        return False
    # Avoid protocol-relative urls '//evil.com' and external urls
    if target.startswith("//") or not target.startswith("/"):
        return False
    # Avoid redirect loops back to auth pages
    auth_prefixes = (
        "/auth/login",
        "/auth/resident-login",
        "/login",
        "/resident/login",
        "/owner/login",
    )
    return not any(target.startswith(p) for p in auth_prefixes)


@auth_bp.route("/owner/login", methods=["GET", "POST"])
@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    """Owner & general staff login with email and password."""
    if current_user.is_authenticated:
        if current_user.is_owner:
            return redirect(url_for("owner.dashboard"))
        if current_user.is_tenant:
            return redirect(url_for("tenant.dashboard"))
        return redirect(url_for("public.index"))

    next_page = request.args.get("next") or request.form.get("next")

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        if not email or not password:
            flash("Please enter both email address and password.", "danger")
            return render_template("auth/login.html", next_page=next_page), 400

        user = User.query.filter_by(email=email).first()

        # Generic enumeration-safe rejection
        if not user:
            flash("Invalid email address or password.", "danger")
            return render_template("auth/login.html", next_page=next_page), 401

        # Check account lockout
        if user.is_locked:
            flash(
                "Your account is temporarily locked due to multiple failed login attempts. "
                "Please try again after 15 minutes or reset your password.",
                "danger",
            )
            return render_template("auth/login.html", next_page=next_page), 403

        # Verify password
        if not user.check_password(password):
            user.record_failed_login()
            db.session.commit()
            if user.is_locked:
                flash(
                    "Account locked: 5 consecutive failed login attempts reached. "
                    "Please wait 15 minutes or use Forgot Password to regain access.",
                    "danger",
                )
            else:
                flash("Invalid email address or password.", "danger")
            return render_template("auth/login.html", next_page=next_page), 401

        # Check active status
        if not user.is_active:
            flash("Your account is currently inactive. Please contact the administrator.", "danger")
            return render_template("auth/login.html", next_page=next_page), 403

        # Successful authentication
        user.reset_failed_logins()
        user.last_login_at = datetime.now(UTC).replace(tzinfo=None)
        db.session.commit()

        login_user(user, remember=remember)
        flash(f"Welcome back, {user.full_name}!", "success")

        if _is_safe_redirect(next_page):
            return redirect(next_page)

        if user.is_owner:
            return redirect(url_for("owner.dashboard"))
        if user.is_tenant:
            return redirect(url_for("tenant.dashboard"))
        return redirect(url_for("public.index"))

    return render_template("auth/login.html", next_page=next_page)


@auth_bp.route("/resident-login", methods=["GET", "POST"])
@auth_bp.route("/resident/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def resident_login():
    """Resident / tenant portal login via 10-digit mobile number or email + password."""
    if current_user.is_authenticated:
        if current_user.is_tenant:
            return redirect(url_for("tenant.dashboard"))
        if current_user.is_owner:
            return redirect(url_for("owner.dashboard"))
        return redirect(url_for("public.index"))

    next_page = request.args.get("next") or request.form.get("next")

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        if not identifier or not password:
            flash("Please enter your registered mobile number or email and password.", "danger")
            return render_template("auth/resident_login.html", next_page=next_page), 400

        # Look up by email or phone
        if "@" in identifier:
            user = User.query.filter_by(email=identifier.lower()).first()
        else:
            digits = "".join(ch for ch in identifier if ch.isdigit())
            if len(digits) >= 10:
                user = User.query.filter(User.phone.like(f"%{digits[-10:]}%")).first()
            else:
                user = User.query.filter_by(phone=digits).first()

        # Generic enumeration-safe rejection
        if not user:
            flash("Invalid mobile number/email or password.", "danger")
            return render_template("auth/resident_login.html", next_page=next_page), 401

        # Check account lockout
        if user.is_locked:
            flash(
                "Your account is temporarily locked due to multiple failed login attempts. "
                "Please try again after 15 minutes or reset your password.",
                "danger",
            )
            return render_template("auth/resident_login.html", next_page=next_page), 403

        # Verify password
        if not user.check_password(password):
            user.record_failed_login()
            db.session.commit()
            if user.is_locked:
                flash(
                    "Account locked: 5 consecutive failed login attempts reached. "
                    "Please wait 15 minutes or use Forgot Password to regain access.",
                    "danger",
                )
            else:
                flash("Invalid mobile number/email or password.", "danger")
            return render_template("auth/resident_login.html", next_page=next_page), 401

        # Check active status
        if not user.is_active:
            flash("Your account is currently inactive. Please contact the administrator.", "danger")
            return render_template("auth/resident_login.html", next_page=next_page), 403

        # Successful authentication
        user.reset_failed_logins()
        user.last_login_at = datetime.now(UTC).replace(tzinfo=None)
        db.session.commit()

        login_user(user, remember=remember)
        flash(f"Welcome back, {user.full_name}!", "success")

        if _is_safe_redirect(next_page):
            return redirect(next_page)

        if user.is_tenant:
            return redirect(url_for("tenant.dashboard"))
        if user.is_owner:
            return redirect(url_for("owner.dashboard"))
        return redirect(url_for("public.index"))

    return render_template("auth/resident_login.html", next_page=next_page)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Register a new prospective tenant account."""
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not full_name or not email or not phone or not password:
            flash("All fields are required.", "danger")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return render_template("auth/register.html")

        new_user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            role=UserRole.TENANT,
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! You may now sign in.", "success")
        return redirect(url_for("auth.resident_login"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    """Sign out the currently authenticated user and terminate session."""
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("public.index"))


@auth_bp.route("/unauthorized")
def unauthorized():
    """Render friendly 403 Forbidden page."""
    return render_template("errors/403.html"), 403


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def forgot_password():
    """Initiate self-service password recovery with a time-limited token."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if not email:
            flash("Please enter your registered email address.", "warning")
            return render_template("auth/forgot_password.html"), 400

        user = User.query.filter_by(email=email).first()
        if user and user.is_active:
            serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
            token = serializer.dumps(
                {"user_id": user.id, "email": user.email},
                salt="password-reset-salt",
            )
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            current_app.logger.info(
                f"[PASSWORD RESET] Direct reset link for {user.email}: {reset_url}"
            )

        # Enumeration-safe generic feedback
        flash(
            "If your email is registered with StayNest, you will receive password reset instructions shortly.",
            "info",
        )
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def reset_password():
    """Validate time-limited single-use token and update password."""
    token = request.args.get("token") or request.form.get("token")
    if not token:
        flash("Password reset token is missing.", "danger")
        return redirect(url_for("auth.forgot_password"))

    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        data = serializer.loads(token, salt="password-reset-salt", max_age=1800)  # 30 minutes
        user_id = data.get("user_id")
        user = User.query.get(user_id)
        if not user or not user.is_active:
            flash("User account not found or is inactive.", "danger")
            return redirect(url_for("auth.forgot_password"))
    except SignatureExpired:
        flash("The password reset link has expired (valid for 30 minutes). Please request a new one.", "danger")
        return redirect(url_for("auth.forgot_password"))
    except BadSignature:
        flash("Invalid or corrupted password reset link.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not password or len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template("auth/reset_password.html", token=token), 400

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/reset_password.html", token=token), 400

        user.set_password(password)
        user.reset_failed_logins()
        db.session.commit()

        flash("Your password has been successfully reset! Please sign in with your new password.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)
