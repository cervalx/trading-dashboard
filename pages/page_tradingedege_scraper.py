import os
import streamlit as st
import yfinance as yf
import json
from datetime import datetime, timedelta
import plotly.graph_objects as go
from modules.navigation import add_navigation
from config import LOCAL_DIR
from loguru import logger
import pandas as pd
import sys

module_dir = os.path.abspath("modules")
sys.path.append(module_dir)

add_navigation()
st.title("Trading Edge Scraper")
st.subheader("All recent posts")

if not os.path.exists("./modules/tradingedge_scraper/credentials.json"):
    st.write("Scraper was not initialized. Please run the scraper first.")
else:
    config = json.load(open("./modules/tradingedge_scraper/credentials.json"))
    data = config.get("storage")
    engine = data.pop("storage_engine")
    repo = None
    feed = {}
    match engine:
        case "supabase-local" | "supabase-remote":
            from modules.repository.supabase_repo import (
                SupabaseRepository,
            )

            repo = SupabaseRepository(preloaded_credentials=data)
            feed = repo.get_feed()
        case "sqlite3":
            from modules.repository.sqlite3_repo import (
                Sqlite3Repository,
            )

            repo = Sqlite3Repository(preloaded_credentials=data)
            feed = repo.get_feed()
        case _:
            logger.error(
                f"Storage choice {engine} not implemented, but this should never happen."
            )
            raise ValueError(f"Storage choice {engine} not implemented")
    feed_df = pd.DataFrame(feed)

    # organise columns first: title, author, link
    first_columns = ["title", "description", "link"]
    feed_df = feed_df[first_columns + [col for col in feed_df.columns if col not in first_columns]]
    # sort by date newest
    feed_df = feed_df.sort_values(by="date", ascending=False)
    # display df, format link column
    st.dataframe(feed_df, column_config={"link": st.column_config.LinkColumn()})

st.divider()