from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from modules.settings import Settings

telegram_bot_token = Settings.get_settings("telegram_bot_token")
# telegram_chat_id = Settings.get_settings("telegram_chat_id")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )
    due = 3
    context.job_queue.run_once(
        send_update,
        due,
        chat_id=update.effective_chat.id,
        name=str(update.effective_chat.id),
        data=due,
    )


async def send_update(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    await context.bot.send_message(job.chat_id, text="Unrequested Update")


if __name__ == "__main__":
    application = ApplicationBuilder().token(telegram_bot_token).build()

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)

    application.run_polling()

    # run once

