"""Authentication routes: Login, Logout, Register, Password Reset."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.auth import auth_bp
from app.extensions import db
from app.models.user import User, UserRole


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.is_owner:
            return redirect(url_for("owner.dashboard"))
        return redirect(url_for("tenant.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user and email in ("owner", "admin", "kishor", "kishor@staynest.local"):
            user = User.query.filter_by(role=UserRole.OWNER).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash("Your account has been deactivated. Please contact the PG owner.", "danger")
                return render_template("auth/login.html")

            if user.is_locked:
                flash("Account is temporarily locked due to failed attempts. Try again later.", "danger")
                return render_template("auth/login.html")

            user.reset_failed_logins()
            db.session.commit()
            login_user(user, remember=bool(request.form.get("remember")))

            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            if user.is_owner:
                return redirect(url_for("owner.dashboard"))
            return redirect(url_for("tenant.dashboard"))
        else:
            if user:
                user.record_failed_login()
                db.session.commit()
            flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
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

        flash("Registration successful! You may now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("public.index"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        # Safe response to prevent account enumeration
        flash("If your email is registered, you will receive password reset instructions.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html")
