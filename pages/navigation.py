import streamlit as st


def add_navigation():
    st.set_page_config(layout='wide')
    st.sidebar.title("Working pages")
    st.sidebar.page_link("pages/positions.py", label="Positions")
    st.sidebar.page_link("pages/settings.py", label="Settings")
