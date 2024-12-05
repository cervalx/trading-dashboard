from playwright.sync_api import sync_playwright
from credentials import get_credentials
from supabase import create_client
import time


# Run this class in a seperate thread
# Example:
# import threading
# scraper = Scraper()
# threading.Thread(target=scraper.run).start()


class Scraper:
    def __init__(self, polling_rate=60, update_rate=3600, lookback_days=3, headless=True, debug=False):
        self.polling_rate = polling_rate
        self.headless = headless
        self.update_rate = update_rate
        self.lookback_days = lookback_days
        self.debug = debug
        self.isRunning = True
        self.page = None
        self.data = None
        self.supabase = None


    def run(self):
        with sync_playwright() as p:
            credentials = get_credentials()

            # Connect to Supabase
            try:
                self.supabase = create_client(credentials["supabase_url"], credentials["supabase_key"])
            except Exception as e:
                print(f"\033[1;31mError: {e}, could not create Supabase client.\033[0m")
            
            # Launch browser
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(user_agent="Chrome/91.0.4472.124")

            # Login and navigate to the feed
            self.page = context.new_page()
            self.page.goto("https://tradingedge.club/sign_in", wait_until="networkidle")
            self.page.fill('input[name="email"]', credentials["email"])
            self.page.fill('input[name="password"]', credentials["password"])
            self.page.press('text="Sign In"', 'Enter')
            self.page.wait_for_selector("div.vV80o7KrqoUYRdQUwRYY")  # Wait for the div showing the welcome message to appear so we know the login was successful
            self.page.goto("https://tradingedge.club/feed?sort=newest", wait_until="networkidle")

            # Start the scraping loop
            while self.isRunning:
                self.scrape_feed()
                time.sleep(self.polling_rate)
                self.page.reload(wait_until="networkidle")

            browser.close()


    def scrape_feed(self):        
        posts = self.page.query_selector_all("li.feed-item")

        for post in posts:
            link = post.query_selector('.feed-item-post').get_attribute('href') if post.query_selector('.feed-item-post') else None

            # Check if post exists already
            post_exists = self.supabase.table("posts").select("link").eq("link", link).execute().data
            if post_exists:
                continue

            author = post.query_selector('.mighty-attribution-name span').inner_text() if post.query_selector('.mighty-attribution-name span') else None
            title = post.query_selector('.feed-item-post-title h1').inner_text() if post.query_selector('.feed-item-post-title h1') else None
            description = post.query_selector('.feed-item-post-description').inner_text() if post.query_selector('.feed-item-post-description') else None
            date = post.query_selector('.feed-item-meta-location .feed-item-post-created-at').inner_text() if post.query_selector('.feed-item-meta-location .feed-item-post-created-at') else None
            likes = post.query_selector('.mighty-post-stat-cheer .mighty-post-stat-cheer-count').inner_text() if post.query_selector('.mighty-post-stat-cheer .mighty-post-stat-cheer-count') else "0"
            comments = post.query_selector('.mighty-post-stat-comment .mighty-post-stat-comment-count').inner_text() if post.query_selector('.mighty-post-stat-comment .mighty-post-stat-comment-count') else "0"

            # Insert the post data to the database
            self.supabase.table("posts").insert([{
                "author": author, 
                "title": title, 
                "description": description, 
                "date": date, 
                "likes": int(likes), 
                "comments": int(comments), 
                "link": link}
            ]).execute()

    
    def scrape_post(self, link):
        # TODO: Implement this function
        pass


    def update_database(self):
        # TODO: Implement this function
        # Open new page
        # Get all posts from the database that were created after now - lookback_days
        # For each post call scrape_post
        # Update the post in the database
        # Close the page
        pass


class PostData:
    def __init__(self, author, title, description, date, likes, comments, link):
        self.author = author
        self.title = title
        self.description = description
        self.date = date
        self.likes = likes
        self.comments = comments
        self.link = link


if __name__ == "__main__":
    scraper = Scraper()
    scraper.run()