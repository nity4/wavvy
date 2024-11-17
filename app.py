import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import random
import time

# Spotify API credentials from Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Define the required scope for Spotify access
scope = "user-library-read user-top-read playlist-read-private user-read-recently-played"

# Initialize Spotify OAuth
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=scope
)

# Set up Streamlit app
st.set_page_config(
    page_title="WVY - Your Spotify Companion",
    page_icon="🌊",
    layout="wide"
)

# Custom CSS for Styling
st.markdown("""
    <style>
    body {background: linear-gradient(to right, black, #1DB954) !important; color: white;}
    .stApp {background: linear-gradient(to right, black, #1DB954) !important;}
    h1, h2, h3, p {color: white !important;}
    .brand {font-size: 3em; font-weight: bold; color: white; margin-bottom: 0; padding: 20px 0;}
    .tagline {font-size: 1.2em; margin-bottom: 20px; color: white;}
    .tabs-container {display: flex; justify-content: center; gap: 30px; margin-top: 20px; margin-bottom: 30px;}
    .tab {color: white; padding: 10px 20px; cursor: pointer; border-radius: 10px; background-color: #1DB954; font-weight: bold;}
    .tab:hover {background-color: #16a34a;}
    .active-tab {background-color: #14a047; color: black;}
    .cover-square {border-radius: 5px; margin-right: 10px; width: 80px; height: 80px; object-fit: cover;}
    .cover-circle {border-radius: 50%; margin-right: 10px; width: 60px; height: 60px; object-fit: cover;}
    .loading {text-align: center; font-size: 1.5em; margin-top: 20px;}
    .insight-box {background: #333; color: white; padding: 15px; border-radius: 10px; margin-top: 20px;}
    </style>
""", unsafe_allow_html=True)

# Authentication
def authenticate_user():
    if "token_info" not in st.session_state:
        query_params = st.experimental_get_query_params()
        if "code" in query_params:
            try:
                token_info = sp_oauth.get_access_token(query_params["code"][0])
                st.session_state["token_info"] = token_info
                st.experimental_set_query_params()  # Clear query params
                st.success("Authentication successful! Refresh the page to continue.")
            except Exception as e:
                st.error(f"Authentication failed: {e}")
        else:
            auth_url = sp_oauth.get_authorize_url()
            st.markdown(f'<a href="{auth_url}" target="_self" style="color: white; text-decoration: none; background-color: #1DB954; padding: 10px 20px; border-radius: 5px;">Login with Spotify</a>', unsafe_allow_html=True)
    return "token_info" in st.session_state

# Navigation Tabs
def render_tabs():
    tabs = ["Liked & Discover", "Top Insights", "Behavior"]
    if "active_tab" not in st.session_state:
        st.session_state["active_tab"] = tabs[0]

    selected_tab = st.session_state["active_tab"]

    html = '<div class="tabs-container">'
    for tab in tabs:
        css_class = "tab active-tab" if tab == selected_tab else "tab"
        action = f"window.location.href='?active_tab={tab}'"
        html += f'<div class="{css_class}" onClick="{action}">{tab}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    # Read active tab from query params
    active_tab = st.experimental_get_query_params().get("active_tab", [st.session_state["active_tab"]])[0]
    st.session_state["active_tab"] = active_tab

    return active_tab

# Data Fetch Functions
def fetch_spotify_data(sp_func, *args, retries=3, **kwargs):
    for attempt in range(retries):
        try:
            return sp_func(*args, **kwargs)
        except Exception as e:
            if "rate limit" in str(e).lower():
                time.sleep(2 ** attempt)
            else:
                st.warning(f"Attempt {attempt + 1} failed. Retrying...")
    return None

# Helper Functions for Data Visualization
def visualize_genre_breakdown(genres):
    genre_counts = pd.Series(genres).value_counts()
    fig, ax = plt.subplots(figsize=(6, 6))
    genre_counts.plot(kind="pie", ax=ax, autopct="%1.1f%%", startangle=90)
    ax.set_ylabel("")
    ax.set_title("Your Genre Breakdown")
    return fig

def visualize_day_night_listening(hours):
    day_hours = [hour for hour in hours if 6 <= hour < 18]
    night_hours = [hour for hour in hours if hour < 6 or hour >= 18]
    fig, ax = plt.subplots()
    ax.bar(["Day", "Night"], [len(day_hours), len(night_hours)], color=["#FFA500", "#1DB954"])
    ax.set_title("Day vs Night Listening")
    return fig

# Main App Logic
if authenticate_user():
    sp = spotipy.Spotify(auth=st.session_state["token_info"]["access_token"])

    # Brand Name and Tagline
    st.markdown('<div class="brand">WVY</div>', unsafe_allow_html=True)
    st.markdown('<div class="tagline">Explore your Spotify insights: your top songs, artists, behavior patterns, and more!</div>', unsafe_allow_html=True)

    # Render Tabs
    active_tab = render_tabs()

    if active_tab == "Liked & Discover":
        st.title("Liked Songs and Recommendations")
        mood = st.selectbox("Choose Mood:", ["Happy", "Calm", "Energetic", "Sad"])
        intensity = st.slider("Select Intensity (1-5):", 1, 5, 3)
        feature = st.radio("What do you want to explore?", ["Liked Songs", "Discover New Songs"])

        if feature == "Liked Songs":
            st.header("Liked Songs")
            with st.spinner("Loading your liked songs..."):
                liked_songs = fetch_spotify_data(sp.current_user_saved_tracks, limit=50)
                for item in random.sample(liked_songs["items"], min(len(liked_songs["items"]), 10)):
                    track = item["track"]
                    st.markdown(f"""
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <img src="{track['album']['images'][0]['url']}" alt="Cover" class="cover-square">
                            <div>
                                <p>{track['name']} by {track['artists'][0]['name']}</p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

        elif feature == "Discover New Songs":
            st.header("Discover New Songs")
            with st.spinner("Finding songs you'll love..."):
                recommendations = fetch_spotify_data(
                    sp.recommendations,
                    seed_tracks=["3n3Ppam7vgaVa1iaRUc9Lp"],  # Example track IDs for testing
                    limit=10
                )
                for track in recommendations["tracks"]:
                    st.markdown(f"""
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <img src="{track['album']['images'][0]['url']}" alt="Cover" class="cover-square">
                            <div>
                                <p>{track['name']} by {track['artists'][0]['name']}</p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

    elif active_tab == "Top Insights":
        st.title("Your Top Insights (Last Month)")
        with st.spinner("Fetching insights..."):
            top_tracks, top_artists, genres = fetch_spotify_data(sp.current_user_top_tracks, limit=5), fetch_spotify_data(sp.current_user_top_artists, limit=5), ["Pop", "Indie"]
            st.header("Your Top Songs")
            for track in top_tracks["items"]:
                st.markdown(f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <img src="{track['album']['images'][0]['url']}" alt="Cover" class="cover-square">
                        <div>{track['name']} by {track['artists'][0]['name']}</div>
                    </div>
                """, unsafe_allow_html=True)

            st.header("Your Top Artists")
            for artist in top_artists["items"]:
                st.markdown(f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <img src="{artist['images'][0]['url']}" alt="Cover" class="cover-circle">
                        <div>{artist['name']}</div>
                    </div>
                """, unsafe_allow_html=True)

            st.header("Genres You Vibe With")
            st.pyplot(visualize_genre_breakdown(genres))

    elif active_tab == "Behavior":
        st.title("Your Listening Behavior")
        with st.spinner("Analyzing your behavior..."):
            recent_plays = fetch_spotify_data(sp.current_user_recently_played, limit=50)
            hours = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ").hour for item in recent_plays["items"]]

            st.header("Listening Trends")
            st.pyplot(visualize_day_night_listening(hours))

else:
    st.write("Please log in to access your Spotify data.")
