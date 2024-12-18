import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

# Spotify API credentials
CLIENT_ID = "your-client-id"  # Replace with your actual Client ID
CLIENT_SECRET = "your-client-secret"  # Replace with your actual Client Secret
REDIRECT_URI = "http://localhost:8501"  # Ensure this matches the Spotify Developer Dashboard

# Spotify OAuth Scope
scope = "user-library-read user-top-read playlist-read-private user-read-recently-played"

# Streamlit Page Configuration
st.set_page_config(
    page_title="Moodify - Your Mood. Your Music.",
    page_icon="🎵",
    layout="wide"
)

# Spotify OAuth Helper
def authenticate_spotify():
    """
    Authenticate Spotify using OAuth and handle access/refresh tokens.
    """
    try:
        if "token_info" not in st.session_state:
            auth_manager = SpotifyOAuth(
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                redirect_uri=REDIRECT_URI,
                scope=scope,
                show_dialog=True
            )
            token_info = auth_manager.get_access_token(as_dict=True)
            st.session_state["token_info"] = token_info
            st.session_state["sp"] = spotipy.Spotify(auth=token_info["access_token"])
        else:
            auth_manager = SpotifyOAuth(
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                redirect_uri=REDIRECT_URI,
                scope=scope
            )
            token_info = auth_manager.refresh_access_token(st.session_state["token_info"]["refresh_token"])
            st.session_state["token_info"] = token_info
            st.session_state["sp"] = spotipy.Spotify(auth=token_info["access_token"])
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        st.stop()

# Logout function to clear session state
def logout():
    """
    Clears Spotify session state to allow re-login.
    """
    for key in ["token_info", "sp"]:
        if key in st.session_state:
            del st.session_state[key]
    st.success("Logged out successfully! Please refresh the page.")

# Display Top Tracks and Artists
def display_top_data():
    """
    Display user's top tracks and artists.
    """
    st.subheader("🎵 Your Top Tracks and Artists")

    # Fetch data
    sp = st.session_state["sp"]
    top_tracks = sp.current_user_top_tracks(limit=10, time_range="short_term")
    top_artists = sp.current_user_top_artists(limit=10, time_range="short_term")

    # Display Top Tracks
    st.write("**Top Tracks:**")
    for idx, item in enumerate(top_tracks['items']):
        st.markdown(f"**{idx+1}. {item['name']}** by {item['artists'][0]['name']}")

    # Display Top Artists
    st.write("**Top Artists:**")
    for idx, artist in enumerate(top_artists['items']):
        st.markdown(f"**{idx+1}. {artist['name']}**")

# Main App Logic
st.title("Moodify 🎵")
st.subheader("Your Mood. Your Music.")
st.markdown("Discover insights about your music habits and mood.")

if "sp" not in st.session_state:
    st.info("Please log in to Spotify to continue.")
    if st.button("Log in with Spotify"):
        authenticate_spotify()
else:
    st.sidebar.button("Logout", on_click=logout)
    st.success("Logged in successfully!")

    # Navigation
    page = st.radio("Navigate to:", ["Top Tracks & Artists", "Mood Insights"])

    if page == "Top Tracks & Artists":
        display_top_data()

    elif page == "Mood Insights":
        st.subheader("Coming Soon: Mood Analysis Insights 🎨")
