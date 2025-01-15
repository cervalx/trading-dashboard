from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from modules.repository.sqlite3_repo import Sqlite3Repository
from modules.settings import Settings
import asyncio
import json
from loguru import logger
from jinja2 import Environment, FileSystemLoader
import pandas as pd
import sys
from colorama import Fore
import inquirer
import os

from modules.repository.sqlite3_repo import (
    Sqlite3Repository,
)
from modules.repository.supabase_repo import (
    SupabaseRepository,
)


def get_credentials() -> dict | None:
    telegram_bot_config = [
        inquirer.Text(
            "telegram_bot_token",
            message="Enter the Telegram Bot Token",
        ),
        inquirer.Text(
            "chat_id",
            message="You need to set up a chat id where you want to send the messages",
        ),
    ]
    print(
        f"""{os.linesep}{Fore.YELLOW}
        In order to be able to receive alerts you need to set up and configure a telegram group{os.linesep}
        and a telegram bot for that group. You and the bot should join the same group and the messages{os.linesep}
        will be posted in there.
        Creating a bot: https://www.directual.com/lesson-library/how-to-create-a-telegram-bot{os.linesep}
        The relevant section is "How to create a Telegram bot"{os.linesep}

        Get the chat_id: Once you have the bot token, make a request to https://api.telegram.org/bot<YourBotToken>/getUpdates{os.linesep}
        something like this:
        curl -X GET https://api.telegram.org/bot<YourBotToken>/getUpdates{os.linesep}

        You should see a JSON response that contains information about the most recent messages received by your bot.{os.linesep}
        Look for the "chat" object in the response, which contains details about the chat your bot is part of.{os.linesep}
        The "id" field within the "chat" object corresponds to the chat ID of the group or channel. Make note of{os.linesep}
        this chat ID; you will need it to send messages to the chat.
        {os.linesep}
        """
    )
    return inquirer.prompt(telegram_bot_config)


telegram_bot_token = Settings.get_setting("telegram_bot_token")
telegram_chat_id = Settings.get_setting("telegram_chat_id")

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <cyan>{level: <8}</cyan> | <yellow>{name}:{function}:{line}</yellow> - {message}",
    colorize=True,
    level="DEBUG",
)


async def send_update(chat_id: str, context: ContextTypes.DEFAULT_TYPE, data):
    env = Environment(loader=FileSystemLoader(searchpath="."))
    # Load the HTML template that we created (styled_stocks.j2)
    template = env.get_template("./modules/telegram_bot/message_template.j2")

    # Render the template with our data
    message_text = template.render(posts=data)
    await context.bot.send_message(
        chat_id, text=message_text, parse_mode=ParseMode.HTML
    )


def compile_message_datalist(
    unprocessed: pd.DataFrame, repo: Sqlite3Repository | SupabaseRepository
) -> list:
    msg_data = []
    for idx, row in unprocessed.iterrows():
        id_, title, link, watched_tickers = tuple(row)
        repo.update_post_tags(id_)
        if (
            len([ticker for ticker in watched_tickers.split(",") if len(ticker) > 0])
            > 0
        ):
            msg_data.append(
                {
                    "ticker": watched_tickers,
                    "title": title,
                    "link": link,
                },
            )
    return msg_data


async def main():
    global telegram_chat_id
    global telegram_bot_token
    # Check if the bot token and chat id are both set, othwerwise ask for them
    if len(telegram_chat_id) == 0 or len(telegram_bot_token) == 0:
        credentials = get_credentials()
        if credentials is None:
            logger.error("No credentials provided, exiting...")
        telegram_chat_id = credentials["telegram_chat_id"]
        telegram_bot_token = credentials["telegram_bot_token"]
        settings = Settings.load_settings()
        settings["telegram_chat_id"] = telegram_chat_id
        settings["telegram_bot_token"] = telegram_bot_token
        Settings.save_settings(settings)
    config = json.load(open("./modules/tradingedge_scraper/credentials.json"))
    data = config.get("storage")
    engine = data.pop("storage_engine")
    repo = None
    application = ApplicationBuilder().token(telegram_bot_token).build()
    match engine:
        case "supabase-local" | "supabase-remote":
            repo = SupabaseRepository(preloaded_credentials=data)
            unprocessed = repo.get_unprocessed_posts()
            msg_data = compile_message_datalist(unprocessed, repo)
            if len(msg_data) > 0:
                await send_update(telegram_chat_id, application, msg_data)
        case "sqlite3":
            repo = Sqlite3Repository(preloaded_credentials=data)
            unprocessed = repo.get_unprocessed_posts()
            msg_data = compile_message_datalist(unprocessed, repo)
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
