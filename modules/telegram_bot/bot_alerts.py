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
            msg_data = []
            for id_, watched_tickers, title, link in unprocessed:
                repo.update_post_tags(id_)
                if len(watched_tickers.split(",")) > 0:
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
            msg_data = []
            for id_, watched_tickers, title, link in unprocessed:
                logger.info(f"Updating post {id_}")
                repo.update_post_tags(id_)
                if len(watched_tickers.split(",")) > 0:
                    msg_data.append(
                        {
                            "ticker": watched_tickers,
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
