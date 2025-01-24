import json
from typing import Dict, List
from config import LOCAL_DIR
from loguru import logger


class Watchlists:
    @staticmethod
    def load_watchlists() -> Dict[str, List[str]]:
        try:
            with open(f"{LOCAL_DIR}/watchlists.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # If the file does not exist, create a new one with default values
            default_watchlists = {
                "2024": ["AAPL", "GOOGL", "MSFT"],
                "CRYPTO-related": ["MSTR", "COIN", "RIOT"],
            }
            Watchlists.save_watchlists(default_watchlists)
            return default_watchlists

    @staticmethod
    def save_watchlists(watchlists: Dict[str, List[str]]) -> None:
        try:
            with open(f"{LOCAL_DIR}/watchlists.json", "w") as f:
                json.dump(watchlists, f, indent=2)
        except Exception as e:
            print(f"Error saving watchlists: {str(e)}")

    @staticmethod
    def update_watchlist(name: str, tickers: List[str]) -> None:
        watchlists = Watchlists.load_watchlists()
        watchlists[name] = tickers
        Watchlists.save_watchlists(watchlists)
