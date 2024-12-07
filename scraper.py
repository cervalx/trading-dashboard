from playwright.sync_api import sync_playwright
from credentials import get_credentials
from supabase import create_client
import datetime
import time
import re


URL_list = {
    "personal_feed": "https://tradingedge.club/feed?sort=newest",
    # A users activity doesn't show ALL posts they have posted, I'm only able to scroll down to a certain point before it stops loading more posts
    # This also includes comments from the user, not just posts.
    "tearrepresentative56_activity_feed": "https://tradingedge.club/members/29038203/feed"
}

MIN_POLLING_RATE = 60 * 2 # 2 minutes is the minimum polling rate, this has to be high enough to find a post that is older than the lookback_days
MAX_LOOKBACK_DAYS = 6 # 7 is already considered a week, posts older than 6 days are obsolete anyway
MIN_LOOKBACK_DAYS = 1 


# This class scrapes the posts from the given url and inserts them into the database
# Run this class in a seperate thread or process
# Example:
# import threading
# scraper = Scraper()
# threading.Thread(target=scraper.run).start()
class Scraper:
    def __init__(self, url=URL_list["tearrepresentative56_activity_feed"], polling_rate=60*5, lookback_days=3, headless=True, debug=False):
        self.url = url
        self.polling_rate = max(MIN_POLLING_RATE, polling_rate) # 2 minutes is the minimum polling rate
        self.headless = headless
        self.lookback_days = max(MIN_LOOKBACK_DAYS, min(lookback_days, MAX_LOOKBACK_DAYS)) # 7 is already considered a week
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

            if match:
                value = int(match.group(1))
                unit = match.group(2)

                # Stop scrolling down if old enough post is found
                if unit == "d" and value > self.lookback_days or unit in ["w", "m", "y"]:
                    return posts

            # Scroll down
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(4) # Wait for the page to load (this could be optimized but 2 is too short)

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
            id = post.get_attribute('data-post-id')
            author = post.query_selector('.mighty-attribution-name span').inner_text() if post.query_selector('.mighty-attribution-name span') else None
            title = post.query_selector('.feed-item-post-title h1').inner_text() if post.query_selector('.feed-item-post-title h1') else None
            description = post.query_selector('.feed-item-post-description').inner_text() if post.query_selector('.feed-item-post-description') else None
            likes = post.query_selector('.mighty-post-stat-cheer .mighty-post-stat-cheer-count').inner_text() if post.query_selector('.mighty-post-stat-cheer .mighty-post-stat-cheer-count') else "0"
            comments = post.query_selector('.mighty-post-stat-comment .mighty-post-stat-comment-count').inner_text() if post.query_selector('.mighty-post-stat-comment .mighty-post-stat-comment-count') else "0"
            link = post.query_selector('.feed-item-post').get_attribute('href') if post.query_selector('.feed-item-post') else None
            category = category = post.query_selector('.post-tag-name').inner_text() if post.query_selector('.post-tag-name') else None

            # Check if post exists already
            post_exists = self.supabase.table("posts").select("id").eq("id", id).execute().data
            if post_exists:
                self.update_post(id, title, description, likes, comments, link)
                number_updated_posts += 1
            else:
                self.add_post(id, author, title, description, likes, comments, link, category)
                number_new_posts += 1

        print(f"Updated {number_updated_posts} posts.")
        print(f"Scraped {number_new_posts} new posts.")

    
    # We can't just update the post by opening it's link and extracting the data
    # because when opening the link it renders an offcanvas where data like likes and comments are missing
    def update_post(self, id, title, description, likes, comments):
        # Update the post in the database (only update the fields that can change)
        self.supabase.table("posts").update({
            "title": title, 
            "description": description, 
            "likes": int(likes), 
            "comments": int(comments),
        }).eq("id", id).execute()
        

    def add_post(self, id, author, title, description, likes, comments, link, category):
        # Insert the post to the database
        self.supabase.table("posts").insert([{
            "id": id,
            "author": author, 
            "title": title, 
            "description": description, 
            # We do not use the posts date because it is not accurate (e.g. "Posted 1w ago")
            # This has the side effect that the posts will be inserted in the database with the current date even if they are older
            # But this is only a problem for the very first run of the scraper with an empyt database
            "date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "likes": int(likes), 
            "comments": int(comments), 
            "link": link,
            "category": category
        }]).execute()


class PostData:
    def __init__(self, id, author, title, description, date, likes, comments, link):
        self.id = id
        self.author = author
        self.title = title
        self.description = description
        self.date = date
        self.likes = likes
        self.comments = comments
        self.link = link


if __name__ == "__main__":
    scraper = Scraper(debug=True, headless=False)
    scraper.run()