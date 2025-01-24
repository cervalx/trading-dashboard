import streamlit as st
import json
import requests
import pytz
from loguru import logger
from modules.navigation import add_navigation
from config import LOCAL_DIR
from modules.settings import Settings

# Load existing settings from JSON file
settings = Settings.load_settings()

add_navigation()
st.title("Settings")

st.subheader("Global Settings")
# Add a selectbox for the timezone (list all timezones)
timezone = st.selectbox(
    "Select your timezone",
    pytz.all_timezones,
    index=pytz.all_timezones.index(settings["timezone"]),
)

st.divider()
st.subheader("Main page")
# add messages for every day of the week
messages_day = st.data_editor(settings["messages_day"], num_rows=7)


st.divider()
st.subheader("Positions")
# organise in 3 columns, use with: st.
col1, col2, col3 = st.columns(3)

# Add a dataeditor for adding tickers, make it editable
with col1:
    st.write("Current positions")
    current_positions = st.data_editor(
        settings["current_positions"], num_rows="dynamic"
    )

with col2:
    st.write("Watchlist positions (and Telegram alerts)")
    watchlist_positions = st.data_editor(
        {"Ticker": settings["watchlist_positions"]}, num_rows="dynamic"
    )

with col3:
    st.write("Previous traded positions")
    previous_traded_positions = st.data_editor(
        {"Ticker": settings["previous_traded_positions"]}, num_rows="dynamic"
    )

st.divider()
st.subheader("Telegram Bot")
telegram_bot_token = st.text_input(
    "Enter your Telegram Bot Token",
    value=settings["telegram_bot_token"],
    type="password",
)

if settings.get("telegram_chat_id") is None or settings["telegram_chat_id"] == "":
    telegram_chat_id = ""

    if st.button("Get Telegram Bot Chat ID"):

        def get_telegram_bot_chat_id(token):
            # access https://api.telegram.org/bot{our_bot_token}/getUpdates, get chat id
            chat_id = ""
            try:
                response = requests.get(
                    f"https://api.telegram.org/bot{token}/getUpdates"
                )
                data = json.loads(response.text)
                chat_id = data["result"][0]["message"]["chat"]["id"]
                # make chat_id a string
                chat_id = str(chat_id)
            except Exception as e:
                logger.error(e)
            return chat_id

        telegram_chat_id = get_telegram_bot_chat_id(telegram_bot_token)
        st.write(f"Telegram chat id: {telegram_chat_id}")
else:
    telegram_chat_id = st.text_input(
        "Telegram Chat ID", value=settings["telegram_chat_id"]
    )
    st.rerun()

st.divider()

# save everything to the settings.json file
Settings.save_settings(
    {
        "timezone": timezone,
        "current_positions": current_positions,
        "watchlist_positions": watchlist_positions["Ticker"],
        "previous_traded_positions": previous_traded_positions["Ticker"],
        "messages_day": messages_day,
        "telegram_bot_token": telegram_bot_token,
        "telegram_chat_id": telegram_chat_id,
    }
)
