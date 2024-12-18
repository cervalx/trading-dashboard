import os
import json


# Get the directory of the current Python file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def set_credentials():
    # Get tradingedge.club credentials
    print()
    print(
        "\033[1;33mTo access the scraper service you need to set the email and password you used for tradingedge.club first.\033[0m"
    )
    print(
        "\033[1;33mThe credentials will be saved to your local system and NOT be shared with anyone.\033[0m"
    )
    print(
        "\033[1;33mThe service cannot be used when you are logging in by using your Google account, etc. You must be able to login via email and password.\033[0m"
    )
    print(
        "\033[1;33mThe scraper currently only scrapes what is shown in the feed of the account logged in, so make sure to unsubscribe from unwanted channels.\033[0m"
    )
    print()
    tradingedge_email = input("Enter your tradingedge.club email : ")
    tradingedge_password = input("Enter your tradingedge.club password: ")
    print()

    # Get Supabase credentials
    print(
        "\033[1;33mTo access the database you also need to set the Supabase URL and API-Key.\033[0m"
    )
    print(
        "\033[1;33mThis is only available to developers of this projects, so ask them for access.\033[0m"
    )
    print()
    supabase_url = input("Enter the Supabase URL: ")
    supabase_api_key = input("Enter the Supabase API-Key: ")
    print()

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


if __name__ == "__main__":
    set_credentials()

