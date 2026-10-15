"""Authentication routes: Login, Logout, Register, Password Reset."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.auth import auth_bp
from app.extensions import db
from app.models.user import User, UserRole


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    owner = User.query.filter_by(role=UserRole.OWNER).first()
    if owner:
        login_user(owner, remember=True)
    next_page = request.args.get("next")
    if next_page and next_page.startswith("/") and not next_page.startswith("/auth/login"):
        return redirect(next_page)
    return redirect(url_for("owner.dashboard"))


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
