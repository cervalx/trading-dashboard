import streamlit as st
from modules.navigation import *
add_navigation()

st.title("Watchlists")

# PSEUDO CODE
# INPUT from user: watchlist name, watchlist tickers as comma separated: "COKE, ROOT,ZS, SMCI"
# input metadata: date watchlist created
# Cleanup list

#SAVE as json file .local/watchlists.json, populate with default values if local file does not exist

# EDIT to add/remove tickers from existing list

# ANALIZE
# Select a watchlist, show for eacth ticker pct. change since [timestamp watchlist created, timestamp ticker added to watchlist, custom timestamp input]
# Show graphs using yfinance for the moment
