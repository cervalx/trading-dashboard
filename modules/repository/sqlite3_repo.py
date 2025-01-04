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
                    id SERIAL PRIMARY KEY,
                    author VARCHAR(255) NOT NULL,
                    title TEXT,
                    description TEXT,
                    date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    likes INTEGER NOT NULL DEFAULT 0,
                    comments INTEGER NOT NULL DEFAULT 0,
                    link TEXT NOT NULL,
                    category VARCHAR(255) NOT NULL
                );""")
            conn.commit()

    def create_post(self, post: PostData) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            insert_data = {
                **post.__dict__,
                "date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            values_queries = ", ".join(["?"] * len(insert_data.keys()))
            query = f"""INSERT INTO POSTS ({', '.join(insert_data.keys())}) VALUES ({ values_queries } )"""
            cursor.execute(query, tuple([m for m in insert_data.values()]))
            conn.commit()

    def get_post_by_id(self, id: int) -> Optional[dict]:
        results = None
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = """SELECT * FROM POSTS WHERE id = ?"""
            results = cursor.execute(query, (id,))
            conn.commit()
        return results.fetchone()

        # return self.supabase.table("posts").select("id").eq("id", id).execute().data

    def get_post(self, title: str) -> Optional[dict]:
        pass

    def get_all_posts(self) -> List[dict]:
        pass

    def update_post(
        self, id: str, title: str, description: str, likes: int, comments: int
    ) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = """
                UPDATE posts
                SET title = ?,
                    description = ?,
                    likes = ?,
                    comments = ?
            WHERE id = ?"""
            cursor.execute(query, (title, description, likes, comments, id))
            conn.commit()

    def delete_post(self, title: str) -> bool:
        pass


if __name__ == "__main__":
    obj = Sqlite3Repository()
