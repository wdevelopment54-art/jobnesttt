"""Custom validators for forms."""
from wtforms.validators import Email, ValidationError
from email_validator import validate_email, EmailNotValidError


class SafeEmail(Email):
    """Email validator that does not perform DNS deliverability checks.

    WTForms' default Email validator relies on the email_validator package
    which, by default, performs DNS lookups and rejects reserved/special-use
    domains (e.g. .test, .example, .localhost). For a job portal we only need
    syntactic validation, so we disable deliverability checks and allow
    test environments.

    NOTE: WTForms only treats `wtforms.validators.ValidationError` as a field
    validation failure. Raising any other exception (e.g. ValueError) makes
    the error propagate as an unhandled 500, so we raise ValidationError here.
    """

    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        value = field.data or ""
        if not value:
            # Let DataRequired handle empty values.
            return
        try:
            validate_email(
                value,
                check_deliverability=False,
                test_environment=True,
            )
        except EmailNotValidError as e:
            message = self.message or field.gettext("Invalid email address.")
            raise ValidationError(message) from e
