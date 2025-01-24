import streamlit as st


def add_navigation():
    st.set_page_config(layout="wide")
    st.sidebar.title("Working pages")
    st.sidebar.page_link("pages/page_positions.py", label="Positions")
    st.sidebar.page_link("pages/page_watchlists.py", label="Watchlists")
    st.sidebar.page_link(
        "pages/page_tradingedege_scraper.py", label="Trading Edge Scraper"
    )
    st.sidebar.page_link("pages/page_settings.py", label="Settings")
