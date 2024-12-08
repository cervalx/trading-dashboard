import streamlit as st
import json
import pytz
import pandas as pd
from modules.navigation import add_navigation

add_navigation()
st.title("Settings")

# Add a selectbox for the timezone (list all timezones)
timezone = st.selectbox("Select your timezone", pytz.all_timezones)

st.divider()

# organise in 3 columns, use with: st.
col1, col2, col3 = st.columns(3)

# Add a dataeditor for adding tickers, make it editable
with col1:
    st.write("Current positions")
    current_positions = st.data_editor(
    {"Ticker": ["NVDA", "TSLA", "AAPL"]},
        num_rows="dynamic"
    )

with col2:
    st.write("Watchlist positions")
    watchlist_positions = st.data_editor(
    {"Ticker": ["COKE", "ARM"]},
        num_rows="dynamic"
    )

with col3:
    st.write("Previous traded positions")
    previous_traded_positions = st.data_editor(
    {"Ticker": ["SMCI", "TSLA", "AAPL"]},
        num_rows="dynamic"
    )

st.divider()

# save everything to the settings.json file
with open("components/settings.json", "w") as f:
    json.dump({"timezone": timezone, "current_positions": current_positions["Ticker"], "watchlist_positions": watchlist_positions["Ticker"], "previous_traded_positions": previous_traded_positions["Ticker"]}, f)

