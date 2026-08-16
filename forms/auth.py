from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, Regexp, Optional
from forms.validators import SafeEmail
from wtforms import ValidationError

from models import User


class RegistrationForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField("Email", validators=[DataRequired(), SafeEmail(), Length(max=150)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    password = PasswordField("Password", validators=[
        DataRequired(),
        Length(min=8, max=128),
        Regexp(r"(?=.*[a-z])(?=.*[A-Z])(?=.*\d)", message="Password must contain uppercase, lowercase and a number."),
    ])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(), EqualTo("password", message="Passwords must match.")
    ])
    account_type = SelectField("Account Type", choices=[
        ("seeker", "Job Seeker"), ("employer", "Employer")
    ], validators=[DataRequired()])
    submit = SubmitField("Create Account")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError("An account with this email already exists.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), SafeEmail()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[
        DataRequired(), Length(min=8, max=128),
        Regexp(r"(?=.*[a-z])(?=.*[A-Z])(?=.*\d)", message="Password must contain uppercase, lowercase and a number."),
    ])
    confirm_password = PasswordField("Confirm New Password", validators=[
        DataRequired(), EqualTo("new_password", message="Passwords must match.")
    ])
    submit = SubmitField("Update Password")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), SafeEmail()])
    submit = SubmitField("Send Reset Link")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[
        DataRequired(), Length(min=8, max=128),
        Regexp(r"(?=.*[a-z])(?=.*[A-Z])(?=.*\d)", message="Password must contain uppercase, lowercase and a number."),
    ])
    confirm_password = PasswordField("Confirm New Password", validators=[
        DataRequired(), EqualTo("password", message="Passwords must match.")
    ])
    submit = SubmitField("Reset Password")
