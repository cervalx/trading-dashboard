import os
import json
from colorama import Fore, Style, Back, init
import inquirer


# Get the directory of the current Python file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def set_credentials():
    # Get tradingedge.club credentials
    trading_edge_prompts = [
        inquirer.Text("email", message="Enter your tradingedge.club email:"),
        inquirer.Password("password", message="Enter your tradingedge.club password:"),
    ]
    print(
        f"""{os.linesep}{Fore.YELLOW}
        To access the scraper service you need to set the email and password you used for tradingedge.club first.{os.linesep}
        The credentials will be saved to your local system and NOT be shared with anyone.{os.linesep}
        The service cannot be used when you are logging in by using your Google account, etc. You must be able to login via email and password.{os.linesep}
        The scraper currently only scrapes what is shown in the feed of the account logged in, so make sure to unsubscribe from unwanted channels.{os.linesep}
        {Style.RESET_ALL}{os.linesep}
        """
    )
    trading_edge_credentials = inquirer.prompt(trading_edge_prompts)

    # Get Supabase credentials
    supabase_prompts = [
        inquirer.Text("supabase_url", message="Enter the Supabase URL:"),
        inquirer.Text("supabase_api_key", message="Enter the Supabase API-Key:"),
    ]
    print(
        f"""{os.linesep}{Fore.YELLOW}
        To access the database you also need to set the Supabase URL and API-Key.{os.linesep}
        This is only available to developers of this projects, so ask them for access.{os.linesep}
        {Style.RESET_ALL}{os.linesep}
        """
    )
    supabase_credentials = inquirer.prompt(supabase_prompts)

    # Prepare credentials as dictionary
    credentials = {
        **trading_edge_credentials,
        **supabase_credentials,
    }

    # Save credentials
    credentials_path = os.path.join(CURRENT_DIR, "credentials.json")
    with open(credentials_path, "w") as credentials_file:
        json.dump(credentials, credentials_file, indent=4)


def get_credentials():
    # Check if credentials exist
    if not os.path.exists(os.path.join(CURRENT_DIR, "credentials.json")):
        print(
            "\033[1;31mError: No credentials found. Running set_credentials().\033[0m"
        )
        set_credentials()

    # Load credentials
    with open(os.path.join(CURRENT_DIR, "credentials.json"), "r") as credentials_file:
        credentials = json.load(credentials_file)
        return credentials


if __name__ == "__main__":
    set_credentials()
