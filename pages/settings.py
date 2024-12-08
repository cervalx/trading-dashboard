import streamlit as st
import json
import pytz
from modules.navigation import add_navigation

# Load existing settings from JSON file
try:
    with open("components/settings.json", "r") as f:
        settings = json.load(f)
except FileNotFoundError:
    settings = {
        "timezone": "UTC",
        "current_positions": [
            {"Ticker": "NVDA", "Quantity": 10, "AvgPrice": 100},
            {"Ticker": "TSLA", "Quantity": 20, "AvgPrice": 280},
            {"Ticker": "AAPL", "Quantity": 30, "AvgPrice": 220}
        ],
        "watchlist_positions": ["COKE", "ARM"],
        "previous_traded_positions": ["SMCI", "TSLA", "AAPL"]
    }

add_navigation()
st.title("Settings")

# Add a selectbox for the timezone (list all timezones)
timezone = st.selectbox("Select your timezone", pytz.all_timezones, 
                       index=pytz.all_timezones.index(settings["timezone"]))

st.divider()

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

# save everything to the settings.json file
with open("components/settings.json", "w") as f:
    json.dump({
        "timezone": timezone,
        "current_positions": current_positions,
        "watchlist_positions": watchlist_positions["Ticker"],
        "previous_traded_positions": previous_traded_positions["Ticker"]
    }, f, indent=2)

