import os
import json
from colorama import Fore, Style, Back, init
import inquirer
from inquirer.errors import ValidationError
from email_validator import validate_email, EmailNotValidError
from urllib.parse import urlparse
from loguru import logger


init(autoreset=True)
# Get the directory of the current Python file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


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


def get_supabase_credentials():
    # Get Supabase credentials
    supabase_prompts = [
        inquirer.Text(
            "supabase_url", message="Enter the Supabase URL", validate=validate_url
        ),
        inquirer.Text("supabase_api_key", message="Enter the Supabase API-Key"),
    ]
    print(
        f"""{os.linesep}{Fore.YELLOW}
        To access the database you also need to set the Supabase URL and API-Key.{os.linesep}
        This is only available to developers of this projects, so ask them for access.{os.linesep}
        {os.linesep}
        """
    )
    return inquirer.prompt(supabase_prompts)


def set_credentials():
    # Get tradingedge.club credentials
    trading_edge_prompts = [
        inquirer.Text(
            "email",
            message="Enter your tradingedge.club email",
            validate=validate_email_input,
        ),
        inquirer.Password("password", message="Enter your tradingedge.club password"),
    ]
    print(
        f"""{os.linesep}{Fore.YELLOW}
        To access the scraper service you need to set the email and password you used for tradingedge.club first.{os.linesep}
        The credentials will be saved to your local system and NOT be shared with anyone.{os.linesep}
        The service cannot be used when you are logging in by using your Google account, etc. You must be able to login via email and password.{os.linesep}
        The scraper currently only scrapes what is shown in the feed of the account logged in, so make sure to unsubscribe from unwanted channels.{os.linesep}
        {os.linesep}
        """
    )
    trading_edge_credentials = inquirer.prompt(trading_edge_prompts)

    storage_questions = [
        inquirer.List(
            "storage",
            message="Where do you want to store the scraped data?",
            choices=[
                ("Supabase", "supabase-remote"),
                ("Supabase Local via Docker", "supabase-local"),
                ("Parquet(Binary Files)", "parquet"),
            ],
        )
    ]

    storage_choice = inquirer.prompt(storage_questions)["storage"]

    storage_credentials = {}

    if storage_choice == "supabase-remote":
        storage_credentials = get_supabase_credentials()
    elif storage_choice == "supabase-local":
        # TODO: it's probably a good idea to spin up a docker container before we get the credentials
        storage_credentials = get_supabase_credentials()
    if storage_choice == "parquet":
        # TODO: using parquet for storage does not require any credentials so it's fine to not get any
        pass

    # Prepare credentials as dictionary
    if all([trading_edge_credentials, storage_credentials]):
        credentials = {
            **trading_edge_credentials,
            **storage_credentials,
        }

        # Save credentials
        credentials_path = os.path.join(CURRENT_DIR, "credentials.json")
        with open(credentials_path, "w") as credentials_file:
            json.dump(credentials, credentials_file, indent=4)
    else:
        logger.warning("No credentials could be stored")


def get_credentials():
    # Check if credentials exist
    if not os.path.exists(os.path.join(CURRENT_DIR, "credentials.json")):
        print(f"{Fore.RED}Error: No credentials found. Running set_credentials().")
        set_credentials()

    # Load credentials
    with open(os.path.join(CURRENT_DIR, "credentials.json"), "r") as credentials_file:
        credentials = json.load(credentials_file)
        return credentials


if __name__ == "__main__":
    set_credentials()
