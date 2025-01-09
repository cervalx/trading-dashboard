from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from modules.settings import Settings
import asyncio
import json
from loguru import logger
import re
from jinja2 import Environment, FileSystemLoader
import pandas as pd
import sys

telegram_bot_token = Settings.get_setting("telegram_bot_token")
telegram_chat_id = Settings.get_setting("telegram_chat_id")
ticker_watchlist = Settings.get_setting("watchlist_positions") + ["BTC"]
# TODO: requires proper implementation
all_tickers_list = Settings.fetch_tickers_list() + ["BTC"]

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <cyan>{level: <8}</cyan> | <yellow>{name}:{function}:{line}</yellow> - {message}",
    colorize=True,
    level="DEBUG",
)


async def send_update(chat_id: str, context: ContextTypes.DEFAULT_TYPE, data) -> None:
    env = Environment(loader=FileSystemLoader(searchpath="."))
    # Load the HTML template that we created (styled_stocks.j2)
    template = env.get_template("./modules/telegram_bot/message_template.j2")

    # Render the template with our data
    message_text = template.render(posts=data)
    await context.bot.send_message(
        chat_id, text=message_text, parse_mode=ParseMode.HTML
    )


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


def process_row(row):
    id_ = row["id"]
    title = row.get("title", "") if pd.notna(row["title"]) else ""
    description = row.get("description", "") if pd.notna(row["description"]) else ""
    link = row["link"]

    all_text = " ".join([title, description])  # Combine title and description
    notifiable_tickers, found_tickers = find_tickers_in_text(all_text)

    return (id_, notifiable_tickers, found_tickers, title, link)


def parse_posts(dataframe):
    results = []
    for _index, row in dataframe.iterrows():
        procced = process_row(row)
        results.append(procced)
    return results


async def main():
    global telegram_chat_id
    global telegram_bot_token
    config = json.load(open("./modules/tradingedge_scraper/credentials.json"))
    data = config.get("storage")
    engine = data.pop("storage_engine")
    repo = None
    application = ApplicationBuilder().token(telegram_bot_token).build()
    match engine:
        case "supabase-local" | "supabase-remote":
            from modules.repository.supabase_repo import (
                SupabaseRepository,
            )

            repo = SupabaseRepository(preloaded_credentials=data)
            unprocessed = repo.get_unprocessed_posts()
            updateable = parse_posts(unprocessed)
            msg_data = []
            for id_, watched_tickers, found_tickers, title, link in updateable:
                logger.info(f"Updating post {id_}")
                repo.update_post_tags(id_, watched_tickers, found_tickers)
                if len(watched_tickers) > 0:
                    msg_data.append(
                        {
                            "ticker": watched_tickers,
                            "title": title,
                            "link": link,
                        },
                    )
            if len(msg_data) > 0:
                await send_update(telegram_chat_id, application, msg_data)
        case "sqlite3":
            from modules.repository.sqlite3_repo import (
                Sqlite3Repository,
            )

            repo = Sqlite3Repository(preloaded_credentials=data)
            unprocessed = repo.get_unprocessed_posts()
            updateable = parse_posts(unprocessed)
            msg_data = []
            for id_, watched_tickers, found_tickers, title, link in updateable:
                logger.info(f"Updating post {id_}")
                repo.update_post_tags(id_, watched_tickers, found_tickers)
                if len(watched_tickers) > 0:
                    msg_data.append(
                        {
                            "ticker": ", ".join(watched_tickers),
                            "title": title,
                            "link": link,
                        },
                    )
            if len(msg_data) > 0:
                await send_update(telegram_chat_id, application, msg_data)
        case _:
            logger.error(
                f"Storage choice {engine} not implemented, but this should never happen."
            )
            raise ValueError(f"Storage choice {engine} not implemented")


if __name__ == "__main__":
    asyncio.run(main())

    # run once
