import datetime
import os
from loguru import logger
from typing import List, NamedTuple, Optional
import inquirer
from colorama import Fore, init
from ..tradingedge_scraper.validators import validate_url
from .repository_interface import PostRepository, PostData
from supabase import create_client
import sys
from collections import namedtuple


init(autoreset=True)


async def create_table_if_not_exists(table_name, columns_definition, engine):
    """
    Creates a table in Supabase.

    Args:
        table_name: The name of the table to create.
        columns_definition: A dictionary where keys are column names and values are SQL column definitions.
    """
    try:
        # Construct the SQL CREATE TABLE statement
        columns_sql = ", ".join(
            [f"{name} {definition}" for name, definition in columns_definition.items()]
        )
        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql})"

        # Execute the SQL statement using the Supabase API (as a raw SQL query)
        response = engine.rpc("executesql", {"sql": create_table_sql}).execute()

        if response.status_code == 200:
            logger.info(f"Table '{table_name}' created successfully!")
        else:
            logger.error(f"Error creating table '{table_name}':")
            logger.error(response.data)  # Print the error details from Supabase

    except Exception as e:
        print(f"An error occurred: {e}")


def get_credentials():
    # Get Supabase credentials
    supabase_prompts = [
        inquirer.Text(
            "supabase_url", message="Enter the Supabase URL", validate=validate_url
        ),
        inquirer.Text("supabase_api_key", message="Enter the Supabase API-Key"),
    ]
    print(
        f"""{os.linesep}{Fore.YELLOW}
        To access the database you also need to set the Supabase URL and API-Key.{os.linesep}
        This is only available to developers of this projects, so ask them for access.{os.linesep}
        {os.linesep}
        """
    )
    return inquirer.prompt(supabase_prompts)


class PrebuildHook(PostRepository, type):
    def __call__(cls, *args, **kwargs):
        logger.info("Pre-object build hook (metaclass) executing...")
        credentials = kwargs.get("preloaded_credentials", None)
        if credentials is None:
            credentials = get_credentials()
        storage = create_client(
            credentials["supabase_url"], credentials["supabase_api_key"]
        )
        nt = namedtuple("Creds", credentials.keys())
        creds = nt(**credentials)

        instance = super().__call__(storage, creds, *args, **kwargs)

        return instance


class SupabaseRepository(metaclass=PrebuildHook):
    def __init__(self, storage, creds, preloaded_credentials=None):
        self.supabase = storage
        self.creds = creds

    def create_post(self, post: PostData) -> bool:
        self.supabase.table("posts").insert(
            [
                {
                    **post.__dict__,
                    "date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                }
            ]
        ).execute()

    def get_post_by_id(self, id: int) -> Optional[dict]:
        return self.supabase.table("posts").select("id").eq("id", id).execute().data

    def get_post(self, title: str) -> Optional[dict]:
        pass

    def get_feed(self) -> List[dict]:
        return self.supabase.table("posts").select("*").execute()

    def update_post(self, post: PostData) -> bool:
        self.supabase.table("posts").update(
            {
                "title": post.title,
                "description": post.description,
                "likes": int(post.likes),
                "comments": int(post.comments),
            }
        ).eq("id", id).execute()

    def delete_post(self, title: str) -> bool:
        pass


if __name__ == "__main__":
    obj = SupabaseRepository(preloaded_credentials={})
