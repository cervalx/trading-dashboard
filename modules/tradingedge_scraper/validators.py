from inquirer.errors import ValidationError
from email_validator import validate_email, EmailNotValidError
from urllib.parse import urlparse


def validate_email_input(answers, current):
    try:
        validate_email(current)
        return True
    except EmailNotValidError as e:
        raise ValidationError(
            "",  # element name can be left blank
            reason=str(e),
        )


def validate_url(answers, current):
    """
    Custom validator using the standard library's `urllib.parse`
    to check if the user input is a valid URL-like string.
    """
    parsed_url = urlparse(current)
    # A minimal check: require at least a scheme and a netloc
    if not parsed_url.scheme or not parsed_url.netloc:
        raise ValidationError("", reason="Please enter a valid URL.")
    return True
