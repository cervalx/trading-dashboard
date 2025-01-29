import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from modules.navigation import *
from modules.watchlists import Watchlists

add_navigation()

st.title("Watchlists")
# watchlists = Watchlists.load_watchlists()

# PSEUDO CODE
# INPUT from user: watchlist name, watchlist tickers as comma separated: "COKE, ROOT,ZS, SMCI"
# input metadata: date watchlist created
# Cleanup list

# SAVE as json file .local/watchlists.json, populate with default values if local file does not exist

# EDIT to add/remove tickers from existing list

# ANALIZE
# Select a watchlist, show for eacth ticker pct. change since [timestamp watchlist created, custom timestamp input]
# Show graphs using yfinance for the moment

st.subheader("Manage Watchlists")

# Load existing watchlists
watchlists = Watchlists.load_watchlists()
watchlist_names = list(watchlists.keys())

# Edit watchlist names
edited_names = st.data_editor(
    {"Watchlists": watchlist_names}, num_rows="dynamic", key="watchlist_names"
)

# Update watchlist names
updated_watchlists = {}
for name in edited_names["Watchlists"]:
    if name:  # Skip empty names
        if name in watchlists:
            updated_watchlists[name] = watchlists[name]
        else:
            updated_watchlists[name] = []

# Select and edit specific watchlist
if updated_watchlists:
    selected_watchlist = st.selectbox(
        "Select watchlist to edit and analyze", options=list(updated_watchlists.keys())
    )

    if selected_watchlist:
        new_tickers = st.text_input('Enter tickers for the new watchlist (comma-separated)')
        if st.button('Add Tickers'):
            if new_tickers:
                tickers_list = [ticker.strip() for ticker in new_tickers.split(',')]
                updated_watchlists[selected_watchlist].extend(tickers_list)
                st.success('Tickers added to the watchlist!')
            else:
                st.warning('Please enter at least one ticker.')

        st.subheader(f"Edit tickers for watchlist: {selected_watchlist}")
        edited_tickers = st.data_editor(
            {"Tickers": updated_watchlists[selected_watchlist]},
            num_rows="dynamic",
            key="watchlist_tickers",
        )

        # Update the selected watchlist
        updated_watchlists[selected_watchlist] = [
            ticker for ticker in edited_tickers["Tickers"] if ticker
        ]

# Save changes
Watchlists.save_watchlists(updated_watchlists)

# ===============================================
# ANALYZE
# ===============================================

st.divider()
st.subheader("Watchlist Analysis")

col1, col2 = st.columns(2)

with col1:
    # default start date 1 year ago
    analysis_start_date = st.date_input(
        "Start Date", datetime.now().date() - timedelta(days=365)
    )
with col2:
    analysis_end_date = st.date_input("End Date")

tab1, tab2 = st.tabs(["Detailed Analysis", "Summary"])

summary_data = []

for each_ticker in updated_watchlists[selected_watchlist]:
    with tab1:
        df = yf.Ticker(each_ticker).history(
            start=analysis_start_date, end=analysis_end_date
        )

        # Create candlestick chart
        figCandle = go.Figure(
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
        figCandle.update_layout(
            title=f"{each_ticker} Stock Price",
            yaxis_title="Stock Price (USD)",
            xaxis_title="Date",
            xaxis_rangeslider_visible=False,
        )

        st.plotly_chart(figCandle, use_container_width=True, key=f"candlestick_{each_ticker}")


        st.write("Analysis for ticker: " + each_ticker)
        # percentage change
        ticker_pct_change = (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100
        ticker_minimum = df["Close"].min()
        ticker_maximum = df["Close"].max()
        list_price_close = df["Close"].tolist()
        ticker_row = [each_ticker, list_price_close, ticker_pct_change, ticker_minimum, ticker_maximum]
        summary_data.append(ticker_row)
        st.write("Percent change from start to end: ", ticker_pct_change, "%")
        # minimum and maximum
        st.write(
            "Minimum: ", ticker_minimum, "Maximum: ", ticker_maximum, " closing price."
        )
        st.divider()

with tab2:
    if summary_data:
        # add Ticker and pctChange as columns
        summary_df = pd.DataFrame(
            summary_data,
            columns=["Ticker", "Price Close [$]", "Percent Change [%]", "Minimum [$]", "Maximum [$]"],
        )
        # highlight row if Percent Change [%] is negative
        summary_df = summary_df.style.highlight_between(subset="Percent Change [%]", left=float("-inf"), right=0, color="darkred")
        # display the summary dataframe
        st.dataframe(summary_df, column_config={"Price Close [$]": st.column_config.AreaChartColumn(width="medium")})

