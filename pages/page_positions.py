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

logger.info(module_dir)

add_navigation()
st.title("Positions")

current_positions = json.load(open(f"{LOCAL_DIR}/settings.json"))["current_positions"]
tickers = [position["Ticker"] for position in current_positions]
selected_position = st.selectbox("Select position", tickers)
position_data = next(
    pos for pos in current_positions if pos["Ticker"] == selected_position
)

# Fetch NVDA stock data for the last year
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

df = yf.Ticker(selected_position).history(start=start_date, end=end_date)

# Create candlestick chart
fig = go.Figure(
    data=[
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
        )
    ]
)

fig.update_layout(
    title=f"{selected_position} Stock Price - Last 12 Months",
    yaxis_title="Stock Price (USD)",
    xaxis_title="Date",
    xaxis_rangeslider_visible=False,
)

# draw horizontal line at the average price
fig.add_hline(
    y=position_data["AvgPrice"], line_dash="dash", line_color="green", line_width=1
)

# Display the chart
st.plotly_chart(fig, use_container_width=True)

st.divider()
if not os.path.exists("./modules/tradingedge_scraper/credentials.json"):
    st.write("Scraper was not initialized. Please run the scraper first.")
else:
    config = json.load(open("./modules/tradingedge_scraper/credentials.json"))
    data = config.get("storage")
    engine = data.pop("storage_engine")
    repo = None
    feed = {}
    match engine:
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
    st.dataframe(feed_df)


st.divider()
st.subheader("Options Analysis")
# Link to https://mztrading.netlify.app/options/analyze/NVDA
st.write(f"Link to https://mztrading.netlify.app/options/analyze/{selected_position}")

st.divider()
# TODO: add posts about ticker
