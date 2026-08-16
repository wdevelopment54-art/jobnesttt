from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db
from models import User, UserProfile, Notification
from forms.auth import (RegistrationForm, LoginForm, ChangePasswordForm,
                        ForgotPasswordForm, ResetPasswordForm)
from utils import create_notification, log_audit

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("public.home"))
    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User(
            full_name=form.full_name.data.strip(),
            email=email,
            phone=form.phone.data,
            role=form.account_type.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()
        # Create empty profile for seekers
        if user.role == "seeker":
            db.session.add(UserProfile(user_id=user.id))
        db.session.commit()

        # Notify admins
        from models import User as U
        admins = U.query.filter_by(role="admin").all()
        for admin in admins:
            create_notification(
                admin.id,
                "New Registration",
                f"{user.full_name} registered as a {user.role}.",
                link=url_for("admin.users"),
                ntype="user",
            )
        log_audit(None, "user_register", "user", user.id, f"{user.email} registered as {user.role}")

        login_user(user)
        flash("Welcome! Your account has been created successfully.", "success")
        if user.role == "employer":
            return redirect(url_for("employer.dashboard"))
        return redirect(url_for("seeker.dashboard"))
    return render_template("auth/register.html", form=form, title="Register")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash("Your account has been deactivated. Please contact support.", "danger")
                return render_template("auth/login.html", form=form, title="Login")
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            flash("You have been logged in successfully.", "success")
            if user.role == "admin":
                return redirect(next_page or url_for("admin.dashboard"))
            if user.role == "employer":
                return redirect(next_page or url_for("employer.dashboard"))
            return redirect(next_page or url_for("seeker.dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("auth/login.html", form=form, title="Login")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("public.home"))


@bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash("Your password has been updated.", "success")
            return redirect(url_for("public.home"))
    return render_template("auth/change_password.html", form=form, title="Change Password")


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("public.home"))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        # Always show generic message to avoid account enumeration
        if user:
            # Configurable SMTP: if not configured, we cannot send email.
            if current_app.config.get("MAIL_SERVER"):
                # Placeholder for SMTP integration
                pass
            flash("If an account exists for that email, a reset link has been sent. "
                  "Email sending is not configured on this server yet.", "info")
        else:
            flash("If an account exists for that email, a reset link has been sent.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html", form=form, title="Forgot Password")


@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    # Reset mechanism is configurable for future SMTP integration.
    flash("Password reset is not enabled because email is not configured.", "info")
    return redirect(url_for("auth.login"))
