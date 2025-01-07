import os
import json
from colorama import Fore, Style, Back, init
import inquirer
from loguru import logger
from .validators import validate_email_input, validate_url


init(autoreset=True)
# Get the directory of the current Python file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def trading_edge_credentials_prompt():
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
    return inquirer.prompt(trading_edge_prompts)


def set_credentials(website_credentials, storage_credentials):
    # Prepare credentials as dictionary
    if all([website_credentials, storage_credentials]):
        credentials = {
            **website_credentials,
            **storage_credentials,
        }

        # Save credentials
        credentials_path = os.path.join(CURRENT_DIR, "credentials.json")
        with open(credentials_path, "a") as credentials_file:
            json.dump(credentials, credentials_file, indent=4)
    else:
        logger.warning("No credentials could be stored")


def get_scraper_credentials():
    # Check if credentials exist
    if not os.path.exists(os.path.join(CURRENT_DIR, "credentials.json")):
        print(f"{Fore.RED}Error: No credentials found. Running set_credentials().")
        # Run the prompt for getting website credentials, will continue with db credentials
        return trading_edge_credentials_prompt()
    # Load credentials
    with open(os.path.join(CURRENT_DIR, "credentials.json"), "r") as credentials_file:
        credentials = json.load(credentials_file)
        if "website" in credentials and "storage" in credentials:
            return credentials
        return trading_edge_credentials_prompt()


if __name__ == "__main__":
    set_credentials()
