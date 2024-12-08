import streamlit as st
import yfinance as yf
import json
from datetime import datetime, timedelta
import plotly.graph_objects as go
from modules.navigation import add_navigation

add_navigation()
st.title("Positions")

list_positions = json.load(open("components/settings.json"))["current_positions"]
selected_position = st.selectbox("Select position", list_positions)

# Fetch NVDA stock data for the last year
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

df = yf.Ticker(selected_position).history(start=start_date, end=end_date)

# Create candlestick chart
fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'])])

fig.update_layout(
    title=f'{selected_position} Stock Price - Last 12 Months',
    yaxis_title='Stock Price (USD)',
    xaxis_title='Date',
    xaxis_rangeslider_visible=False
)

# Display the chart
st.plotly_chart(fig, use_container_width=True)

# TODO: add posts about ticker