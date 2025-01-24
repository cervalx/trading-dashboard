from playwright.sync_api import sync_playwright
from supabase import create_client
import time
import re
from colorama import init, Fore
import asyncio
from loguru import logger
from ..repository.supabase_repo import SupabaseRepository
from ..repository.repository_interface import PostData
from .credentials import get_scraper_credentials, set_credentials
import inquirer
from modules.settings import Settings
import pandas as pd
import sys
from datetime import datetime

init(autoreset=True)

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <cyan>{level: <8}</cyan> | <yellow>{name}:{function}:{line}</yellow> - {message}",
    colorize=True,
    level="DEBUG",
)

URL_LIST = {
    "personal_feed": "https://tradingedge.club/feed?sort=newest",
    # A users activity doesn't show ALL posts they have posted, I'm only able to scroll down to a certain point before it stops loading more posts
    # This also includes comments from the user, not just posts.
    "tearrepresentative56_activity_feed": "https://tradingedge.club/members/29038203/feed",
}

MIN_POLLING_RATE = (
    60 * 2
)  # 2 minutes is the minimum polling rate, this has to be high enough to find a post that is older than the lookback_days
MAX_LOOKBACK_DAYS = (
    6  # 7 is already considered a week, posts older than 6 days are obsolete anyway
)
MIN_LOOKBACK_DAYS = 1

TIMEOUT_SLIDE_ANIMATION = 2 # seconds


ticker_watchlist = Settings.get_setting("watchlist_positions")
all_tickers_list = Settings.fetch_tickers_list()


def find_tickers_in_text(
    article_text, valid_tickers=all_tickers_list, watchlist_positions=ticker_watchlist
):
    # Basic uppercase pattern (1-5 letters)
    possible_tickers = re.findall(r"(?:^|\b)[A-Z]{1,7}(?:\b|$)", article_text)

    # Filter by known valid tickers
    found = [t for t in possible_tickers if t in valid_tickers]
    watched = [t for t in found if t in watchlist_positions]
    return list(set(watched)), list(set(found))
    # remove duplicates if needed


# This class scrapes the posts from the given url and inserts them into the database
# Run this class in a seperate thread or process
# Example:
# import threading
# scraper = Scraper()
# threading.Thread(target=scraper.run).start()
class Scraper:
    def __init__(
        self,
        storage,
        url=URL_LIST["tearrepresentative56_activity_feed"],
        polling_rate=60 * 5,
        lookback_days=3,
        headless=True,
        debug=False,
    ):
        self.url = url
        self.polling_rate = max(
            MIN_POLLING_RATE, polling_rate
        )  # 2 minutes is the minimum polling rate
        self.headless = headless
        self.lookback_days = max(
            MIN_LOOKBACK_DAYS, min(lookback_days, MAX_LOOKBACK_DAYS)
        )  # 7 is already considered a week
        self.debug = debug
        self.isRunning = True
        self.page = None
        self.data = None
        self.storage = None
        self.website_credentials = {}

    def build(self):
        preloaded = False
        scraper_credentials = get_scraper_credentials()
        if "storage" in scraper_credentials and "website" in scraper_credentials:
            preloaded = True
            # This means that the json file was found and credentials for the storage
            # and website were found. If there was an old version of the config file
            # we prompt again
            storage_credentials = scraper_credentials["storage"]
            storage_choice = storage_credentials.pop("storage_engine", None)
            self.website_credentials = scraper_credentials.get("website")
        else:
            # credentials.json was not found so we need to initialize
            self.website_credentials = scraper_credentials
            storage_questions = [
                inquirer.List(
                    "storage",
                    message="Where do you want to store the scraped data?",
                    choices=[
                        ("Supabase", "supabase-remote"),
                        ("Supabase Local via Docker", "supabase-local"),
                        ("Postgres Local", "postgres-local"),
                        ("Parquet(Binary Files)", "parquet"),
                        ("Sqlite3", "sqlite3"),
                    ],
                )
            ]
            storage_choice = inquirer.prompt(storage_questions)["storage"]
        storage_config = {}
        match storage_choice:
            case "supabase-remote":
                from ..repository.supabase_repo import SupabaseRepository

                if preloaded:
                    self.storage = SupabaseRepository(
                        preloaded_credentials=storage_credentials
                    )
                    return
                else:
                    self.storage = SupabaseRepository()
                    storage_config = {
                        "storage": {
                            "storage_engine": "supabase-remote",
                            "supabase_url": self.storage.creds.supabase_url,
                            "supabase_api_key": self.storage.creds.supabase_api_key,
                        }
                    }

            case "supabase-local":
                from ..repository.supabase_repo import SupabaseRepository

                if preloaded:
                    self.storage = SupabaseRepository(
                        preloaded_credentials=storage_credentials
                    )
                    return
                else:
                    self.storage = SupabaseRepository()
                    storage_config = {
                        "storage": {
                            "storage_engine": "supabase-local",
                            "supabase_url": self.storage.creds.supabase_url,
                            "supabase_api_key": self.storage.creds.supabase_api_key,
                        }
                    }

                # TODO: it's probably a good idea to spin up a docker container before we get the credentials
            case "sqlite3":
                # TODO: implement sqlite3 storage
                from ..repository.sqlite3_repo import Sqlite3Repository

                if preloaded:
                    self.storage = Sqlite3Repository(
                        preloaded_credentials=storage_credentials
                    )
                    return
                else:
                    self.storage = Sqlite3Repository()
                    storage_config = {
                        "storage": {
                            "storage_engine": "sqlite3",
                            "sqlite3_file": self.storage.db_path,
                        }
                    }
                pass
            case _:
                logger.error(
                    f"Storage choice {storage_choice} not implemented, but this should never happen."
                )
                raise ValueError(f"Storage choice {storage_choice} not implemented")
        set_credentials({"website": self.website_credentials}, storage_config)

    def run(self):
        # Connect to Supabase

        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(user_agent="Chrome/91.0.4472.124")

            # Login and navigate to the desired url
            self.page = context.new_page()
            self.page.goto("https://tradingedge.club/sign_in", wait_until="networkidle")
            self.page.fill('input[name="email"]', self.website_credentials["email"])
            self.page.fill(
                'input[name="password"]', self.website_credentials["password"]
            )
            self.page.press('text="Sign In"', "Enter")
            self.page.wait_for_url("https://tradingedge.club/spaces/**")
            self.page.goto(self.url, wait_until="networkidle")

            # Start the scraping loop
            while self.isRunning:
                self.scrape_posts()
                time.sleep(self.polling_rate)
                self.page.reload(wait_until="networkidle")

            browser.close()

    # This function scrolls down the page until the last post is older than the lookback_days or no new posts are loaded
    def load_all_posts(self):
        while True:
            posts = self.page.query_selector_all("li.feed-item")
            post_count_before_scroll = len(posts)

            last_post = posts[-1]
            last_post_raw_date = last_post.query_selector(
                ".feed-item-meta-location .feed-item-post-created-at"
            ).inner_text()

            # Parse the date
            match = re.match(r"Posted (\d+)([dwmy]) ago", last_post_raw_date)

            if match:
                value = int(match.group(1))
                unit = match.group(2)

                # Stop scrolling down if old enough post is found
                if (
                    unit == "d"
                    and value > self.lookback_days
                    or unit in ["w", "m", "y"]
                ):
                    return posts

            # Scroll down
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(
                4
            )  # Wait for the page to load (this could be optimized but 2 is too short)

            # Check if new posts were loaded, if not break the loop
            posts = self.page.query_selector_all("li.feed-item")
            post_count_after_scroll = len(posts)
            if post_count_before_scroll == post_count_after_scroll:
                return posts

    # This function scrapes the url and inserts the posts into the database
    def scrape_posts(self):
        number_new_posts = 0
        number_updated_posts = 0

        posts = self.load_all_posts()
        for post in posts:

            id = post.get_attribute("data-post-id")
            author = (
                post.query_selector(".mighty-attribution-name span").inner_text()
                if post.query_selector(".mighty-attribution-name span")
                else None
            )
            title = (
                post.query_selector(".feed-item-post-title h1").inner_text()
                if post.query_selector(".feed-item-post-title h1")
                else None
            )
            # Handle long / short description
            # Check if post has long description
            if post.query_selector(".mighty-wysiwyg-content-show-more"):
                logger.info("Post has long description")
                post.query_selector(".mighty-wysiwyg-content-show-more").click()
                # after click, wait to load the new page
                time.sleep(TIMEOUT_SLIDE_ANIMATION)
                # get long description
                description = (
                    self.page.query_selector(".detail-layout-description").inner_text()
                    if self.page.query_selector(".detail-layout-description")
                    else None
                )
                # close the post
                self.page.query_selector(".btn-close").click()
                time.sleep(TIMEOUT_SLIDE_ANIMATION)
            else:
                # get short description
                description = (
                    post.query_selector(".feed-item-post-description").inner_text()
                    if post.query_selector(".feed-item-post-description")
                    else None
                )

            likes = (
                post.query_selector(
                    ".mighty-post-stat-cheer .mighty-post-stat-cheer-count"
                ).inner_text()
                if post.query_selector(
                    ".mighty-post-stat-cheer .mighty-post-stat-cheer-count"
                )
                else "0"
            )
            comments = (
                post.query_selector(
                    ".mighty-post-stat-comment .mighty-post-stat-comment-count"
                ).inner_text()
                if post.query_selector(
                    ".mighty-post-stat-comment .mighty-post-stat-comment-count"
                )
                else "0"
            )
            link = (
                post.query_selector(".feed-item-post").get_attribute("href")
                if post.query_selector(".feed-item-post")
                else None
            )
            if link is None:
                continue
            category = (
                post.query_selector(".post-tag-name").inner_text()
                if post.query_selector(".post-tag-name")
                else None
            )

            posted_date = (
                post.query_selector(".feed-item-post-created-at").get_attribute("title")
                if post.query_selector(".feed-item-post-created-at")
                else None
            )

            posted_time = None
            if posted_date is not None:
                posted_time = datetime.strptime(posted_date, "%a, %B %d, %Y, %I:%M%p")
                posted_time = posted_time.strftime("%Y-%m-%d %H:%M:%S")

            title_str = title if title else ""
            description_str = description if description else ""
            watched_tickers, found_tickers = find_tickers_in_text(
                f"{title_str} {description_str}"
            )
            # Check if post exists already
            post_exists = self.storage.post_exists(id)
            if post_exists:
                self.storage.update_post(
                    PostData(
                        id=id,
                        title=title,
                        description=description,
                        likes=int(likes),
                        comments=int(comments),
                        posted_date=posted_time,
                        date=posted_time,
                        ticker_notification_sent=", ".join(watched_tickers),
                        found_tickers=", ".join(found_tickers),
                    )
                )
                number_updated_posts += 1
            else:
                self.storage.create_post(
                    PostData(
                        id=id,
                        author=author,
                        title=title,
                        description=description,
                        likes=int(likes),
                        comments=int(comments),
                        posted_date=posted_time,
                        date=posted_time,
                        link=link,
                        category=category,
                        ticker_notification_sent=", ".join(watched_tickers),
                        found_tickers=", ".join(found_tickers),
                    )
                )
                number_new_posts += 1

        print(f"Updated {number_updated_posts} posts.")
        print(f"Scraped {number_new_posts} new posts.")

    # We can't just update the post by opening it's link and extracting the data
    # because when opening the link it renders an offcanvas where data like likes and comments are missing


if __name__ == "__main__":
    scraper = Scraper(SupabaseRepository, debug=True, headless=True)
    scraper.build()
    scraper.run()
