import json
import csv
from config import LOCAL_DIR
from loguru import logger


class Settings:
    @staticmethod
    def fetch_tickers_list() -> list[str]:
        # read list from static csv file 'static/nasdaq_screener_1736874960864.csv', column Symbol
        tickers_list = []
        with open("static/nasdaq_screener_1736874960864.csv", mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                tickers_list.append(row["Symbol"])
        # return ["AAPL", "TSLA", "NVDA", "AMD", "COKE", "ARM", "F"]  # Example list
        return tickers_list

    @staticmethod
    def get_setting(setting_name) -> str | list[str] | dict:
        settings = Settings.load_settings()
        return settings.get(setting_name, "")

    @staticmethod
    def load_settings() -> dict:
        # Load existing settings from JSON file
        try:
            with open(f"{LOCAL_DIR}/settings.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # If the file does not exist, create a new one with default values
            default_settings = {
                "timezone": "UTC",
                "current_positions": [
                    {"Ticker": "NVDA", "Quantity": 10, "AvgPrice": 100},
                    {"Ticker": "TSLA", "Quantity": 20, "AvgPrice": 280},
                    {"Ticker": "AAPL", "Quantity": 30, "AvgPrice": 220},
                ],
                "watchlist_positions": ["COKE", "ARM"],
                "previous_traded_positions": ["SMCI", "TSLA", "AAPL"],
                "messages_day": [
                    {
                        "day": "Monday",
                        "message": "Price usually go up after the weekend.",
                    },
                    {"day": "Tuesday", "message": "Do not trade in first 30 min"},
                    {"day": "Wednesday", "message": "Do not trade in first 30 min"},
                    {"day": "Thursday", "message": "Do not trade in first 30 min"},
                    {
                        "day": "Friday",
                        "message": "Mostly a selling day, look to buy towards the end of the day! Have patience.",
                    },
                    {"day": "Saturday", "message": "Market closed. Server Maintenance"},
                    {"day": "Sunday", "message": "Market closed."},
                ],
            }
            Settings.save_settings(default_settings)
            return default_settings

    @staticmethod
    def save_settings(settings):
        try:
            with open(f"{LOCAL_DIR}/settings.json", "w") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {str(e)}")
