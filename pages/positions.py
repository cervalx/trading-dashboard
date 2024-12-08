import streamlit as st
import yfinance as yf
import json
from datetime import datetime, timedelta
import plotly.graph_objects as go
from modules.navigation import add_navigation

add_navigation()
st.title("Positions")

current_positions = json.load(open("components/settings.json"))["current_positions"]
tickers = [position["Ticker"] for position in current_positions]
selected_position = st.selectbox("Select position", tickers)
position_data = next(pos for pos in current_positions if pos["Ticker"] == selected_position)

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

# draw horizontal line at the average price
fig.add_hline(y=position_data["AvgPrice"], line_dash="dash", line_color="green", line_width=1)

# Display the chart
st.plotly_chart(fig, use_container_width=True)

# TODO: add posts about ticker