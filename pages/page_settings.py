import streamlit as st
import json
import pytz
from modules.navigation import add_navigation
from config import LOCAL_DIR
from modules.settings import Settings

# Load existing settings from JSON file
settings = Settings.load_settings()

add_navigation()
st.title("Settings")

st.subheader("Global Settings")
# Add a selectbox for the timezone (list all timezones)
timezone = st.selectbox("Select your timezone", pytz.all_timezones, 
                       index=pytz.all_timezones.index(settings["timezone"]))

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
        settings["current_positions"],
        num_rows="dynamic"
    )

with col2:
    st.write("Watchlist positions")
    watchlist_positions = st.data_editor(
        {"Ticker": settings["watchlist_positions"]},
        num_rows="dynamic"
    )

with col3:
    st.write("Previous traded positions")
    previous_traded_positions = st.data_editor(
        {"Ticker": settings["previous_traded_positions"]},
        num_rows="dynamic"
    )

st.divider()
st.subheader("Telegram Bot")
telegram_bot_token = st.text_input("Enter your Telegram Bot Token", type="password")
telegram_chat_id = st.text_input("Enter your Telegram Chat ID")

st.divider()

# save everything to the settings.json file
Settings.save_settings({
    "timezone": timezone,
    "current_positions": current_positions,
    "watchlist_positions": watchlist_positions["Ticker"],
    "previous_traded_positions": previous_traded_positions["Ticker"],
    "messages_day": messages_day,
    "telegram_bot_token": telegram_bot_token,
    "telegram_chat_id": telegram_chat_id
})

