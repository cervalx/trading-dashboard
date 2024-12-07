from playwright.sync_api import sync_playwright
from credentials import get_credentials
from supabase import create_client
import datetime
import time
import re


# Run this class in a seperate thread
# Example:
# import threading
# scraper = Scraper()
# threading.Thread(target=scraper.run).start()


class Scraper:
    def __init__(self, url, polling_rate=60*5, update_rate=3600, lookback_days=3, headless=True, debug=False):
        self.url = url
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
        credentials = get_credentials()

        # Connect to Supabase
        try:
            self.supabase = create_client(credentials["supabase_url"], credentials["supabase_key"])
        except Exception as e:
            print(f"\033[1;31mError: {e}, could not create Supabase client.\033[0m")

        with sync_playwright() as p:            
            # Launch browser
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(user_agent="Chrome/91.0.4472.124")

            # Login and navigate to the desired url
            self.page = context.new_page()
            self.page.goto("https://tradingedge.club/sign_in", wait_until="networkidle")
            self.page.fill('input[name="email"]', credentials["email"])
            self.page.fill('input[name="password"]', credentials["password"])
            self.page.press('text="Sign In"', 'Enter')
            self.page.wait_for_url("https://tradingedge.club/spaces/**")
            self.page.goto(self.url, wait_until="networkidle")
            
            # Scroll down until the last post is older than the lookback_date
            self.load_all_posts()

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
            last_post_raw_date = last_post.query_selector('.feed-item-meta-location .feed-item-post-created-at').inner_text()

            # Parse the date
            match = re.match(r"Posted (\d+)([dwmy]) ago", last_post_raw_date)

            # If the date is not found (happens when the post is less than 24h old (hour, minute, second, now))
            if not match:
                continue
            
            value = int(match.group(1))
            unit = match.group(2)

            # Stop scrolling down if old enough post is found
            if unit == "d" and value > self.lookback_days:
                break

            # This will get triggered if the last post of the currently loaded feed is older than 7 days
            if unit in ["w", "m", "y"]:
                break

            # Scroll down
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(4) # Wait for the page to load (this could be optimized but 2 is too short)

            # Check if new posts were loaded, if not break the loop
            posts = self.page.query_selector_all("li.feed-item")
            post_count_after_scroll = len(posts)
            if post_count_before_scroll == post_count_after_scroll:
                break


    # This function scrapes the url and inserts the posts into the database
    def scrape_posts(self):        
        number_new_posts = 0
        number_updated_posts = 0

        posts = self.page.query_selector_all("li.feed-item")
        for post in posts:
            link = post.query_selector('.feed-item-post').get_attribute('href') if post.query_selector('.feed-item-post') else None
            author = post.query_selector('.mighty-attribution-name span').inner_text() if post.query_selector('.mighty-attribution-name span') else None
            title = post.query_selector('.feed-item-post-title h1').inner_text() if post.query_selector('.feed-item-post-title h1') else None
            description = post.query_selector('.feed-item-post-description').inner_text() if post.query_selector('.feed-item-post-description') else None
            likes = post.query_selector('.mighty-post-stat-cheer .mighty-post-stat-cheer-count').inner_text() if post.query_selector('.mighty-post-stat-cheer .mighty-post-stat-cheer-count') else "0"
            comments = post.query_selector('.mighty-post-stat-comment .mighty-post-stat-comment-count').inner_text() if post.query_selector('.mighty-post-stat-comment .mighty-post-stat-comment-count') else "0"

            # Check if post exists already
            post_exists = self.supabase.table("posts").select("link").eq("link", link).execute().data
            if post_exists:
                self.update_post(link, author, title, description, likes, comments)
                number_updated_posts += 1
            else:
                self.add_post(author, title, description, likes, comments, link)
                number_new_posts += 1

        print(f"Updated {number_new_posts} new posts.")
        print(f"Scraped {number_new_posts} new posts.")

    
    # We can't just update the post by opening it's link and extracting the data
    # because when opening the link it renders an offcanvas where data like likes and comments are missing
    def update_post(self, author, title, description, likes, comments, link):
        # Update the post in the database
        self.supabase.table("posts").update({
            "author": author, 
            "title": title, 
            "description": description, 
            "likes": int(likes), 
            "comments": int(comments)
        }).eq("link", link).execute()
        

    def add_post(self, author, title, description, likes, comments, link):
        # Insert the post to the database
        self.supabase.table("posts").insert([{
            "author": author, 
            "title": title, 
            "description": description, 
            # We do not use the posts date because it is not accurate (e.g. "Posted 1w ago")
            # This has the side effect that the posts will be inserted in the database with the current date even if they are older
            # But this is only a problem for the very first run of the scraper with an empyt database
            "date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "likes": int(likes), 
            "comments": int(comments), 
            "link": link}
        ]).execute()


class PostData:
    def __init__(self, author, title, description, date, likes, comments, link):
        self.author = author
        self.title = title
        self.description = description
        self.date = date
        self.likes = likes
        self.comments = comments
        self.link = link


URL_list = {
    "personal_feed": "https://tradingedge.club/feed?sort=newest",
    # A users activity doesn't show ALL posts they have posted, I'm only able to scroll down to a certain point before it stops loading more posts
    "tearrepresentative56_activity_feed": "https://tradingedge.club/members/29038203/feed"
}


if __name__ == "__main__":
    scraper = Scraper(url=URL_list["tearrepresentative56_activity_feed"], debug=True, headless=False)
    scraper.run()