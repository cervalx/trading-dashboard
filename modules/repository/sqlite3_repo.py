import datetime
import os
from loguru import logger
import sqlite3
from typing import List, NamedTuple, Optional
import inquirer
from colorama import Fore, init
from ..tradingedge_scraper.validators import validate_url
from .repository_interface import PostRepository, PostData

import sys
from collections import namedtuple
import pandas as pd


def get_credentials():
    # Get Supabase credentials
    sqlite3_prompts = [
        inquirer.Text("sqlite3_file", message="Enter the Sqlite DB path"),
    ]
    print(
        f"""{os.linesep}{Fore.YELLOW}
        To access the database you need to set a path for the file to be created.{os.linesep}
        {os.linesep}
        """
    )
    return inquirer.prompt(sqlite3_prompts)


class PrebuildHook(PostRepository, type):
    def __call__(cls, *args, **kwargs):
        logger.info("Pre-object build hook (metaclass) executing...")
        credentials = kwargs.get("preloaded_credentials", None)
        if credentials is None:
            credentials = get_credentials()
        storage = credentials["sqlite3_file"]

        instance = super().__call__(storage, *args, **kwargs)

        return instance


class Sqlite3Repository(metaclass=PrebuildHook):
    def __init__(self, storage, preloaded_credentials=None):
        self.db_path = storage
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id PRIMARY KEY,
                    author VARCHAR(255) NOT NULL,
                    title TEXT,
                    description TEXT,
                    posted_date TEXT,
                    date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    likes INTEGER NOT NULL DEFAULT 0,
                    comments INTEGER NOT NULL DEFAULT 0,
                    link TEXT NOT NULL,
                    category VARCHAR(255) NOT NULL,
                    content_parsed BOOLEAN NOT NULL DEFAULT FALSE,
                    ticker_notification_sent VARCHAR(100) DEFAULT NULL,
                    found_tickers TEXT DEFAULT NULL
                );""")
            conn.commit()

    def create_post(self, post: PostData):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            insert_data = {
                **post.__dict__,
                "date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            for field_name in [
                "content_parsed",
            ]:
                insert_data.pop(field_name)
            values_queries = ", ".join(["?"] * len(insert_data.keys()))
            query = f"""INSERT INTO POSTS ({', '.join(insert_data.keys())}) VALUES ({ values_queries } )"""
            try:
                cursor.execute(query, tuple([m for m in insert_data.values()]))
            except sqlite3.IntegrityError as e:
                logger.error(f"Error inserting post: {e}")
            conn.commit()

    def post_exists(self, id: int) -> bool:
        results = None
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT
                    author, title, description,
                    date, likes, comments, link, category
                FROM POSTS WHERE id = ?
            """
            params = (id,)
            results = pd.read_sql_query(query, conn, params=params)
        return not results.empty

    def get_feed(self) -> pd.DataFrame:
        results = None
        with sqlite3.connect(self.db_path) as conn:
            query = """SELECT 
                    author, title, description,
                    posted_date, likes, comments, link, category, ticker_notification_sent, found_tickers
            FROM posts"""
            results = pd.read_sql_query(query, conn)
            results.rename(
                {"ticker_notification_sent": "watched_tickers"}, axis=1, inplace=True
            )
            results["posted_date"] = pd.to_datetime(results["posted_date"])
        return results

    def update_post(self, post: PostData):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = """
                UPDATE posts
                SET title = ?,
                    description = ?,
                    likes = ?,
                    comments = ?
            WHERE id = ?"""
            cursor.execute(
                query,
                (post.title, post.description, post.likes, post.comments, post.id),
            )
            conn.commit()

    def get_unprocessed_posts(self) -> pd.DataFrame:
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT id, title, link, ticker_notification_sent FROM posts WHERE content_parsed = FALSE
            """
            results = pd.read_sql_query(query, conn)
        return results

    def update_post_tags(self, id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = """
                UPDATE posts
                SET content_parsed = TRUE
            WHERE id = ?"""
            cursor.execute(query, (id,))
            conn.commit()


if __name__ == "__main__":
    obj = Sqlite3Repository()
