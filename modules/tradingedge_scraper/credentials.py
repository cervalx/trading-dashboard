import os
import json
from colorama import Fore, Style, Back, init
import inquirer


# Get the directory of the current Python file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def set_credentials():
    # Get tradingedge.club credentials
    print(
        f"""{os.linesep}{Fore.YELLOW}
        To access the scraper service you need to set the email and password you used for tradingedge.club first.{os.linesep}
        The credentials will be saved to your local system and NOT be shared with anyone.{os.linesep}
        The service cannot be used when you are logging in by using your Google account, etc. You must be able to login via email and password.{os.linesep}
        The scraper currently only scrapes what is shown in the feed of the account logged in, so make sure to unsubscribe from unwanted channels.{os.linesep}
        {Style.RESET_ALL}{os.linesep}
        """
    )
    tradingedge_email = input("Enter your tradingedge.club email : ")
    tradingedge_password = input("Enter your tradingedge.club password: ")

    # Get Supabase credentials
    print(
        f"""{os.linesep}{Fore.YELLOW}
        To access the database you also need to set the Supabase URL and API-Key.{os.linesep}
        This is only available to developers of this projects, so ask them for access.{os.linesep}
        {Style.RESET_ALL}{os.linesep}
        """
    )
    supabase_url = input("Enter the Supabase URL: ")
    supabase_api_key = input("Enter the Supabase API-Key: ")

    # Prepare credentials as dictionary
    credentials = {
        "email": tradingedge_email,
        "password": tradingedge_password,
        "supabase_url": supabase_url,
        "supabase_key": supabase_api_key,
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


def tester_inq():
    questions = [
        inquirer.List(
            "theme",
            message=f"{Fore.CYAN}Choose a theme:",
            choices=[
                f"{Fore.BLUE}Dark Blue",
                f"{Fore.GREEN}Forest Green",
                f"{Fore.YELLOW}Bright Yellow",
            ],
        ),
        inquirer.Confirm(
            "confirmation",
            message=f"{Fore.MAGENTA}{Back.WHITE}Are you sure?{Style.RESET_ALL}",
        ),
    ]

    answers = inquirer.prompt(questions)

    print(f"Theme: {answers['theme']}")
    print(f"Confirmation: {answers['confirmation']}")


if __name__ == "__main__":
    # set_credentials()
    tester_inq()
