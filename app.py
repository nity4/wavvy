import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time
import random

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

st.set_page_config(
    page_title="WVY - Your Spotify Companion",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Theme
st.markdown("""
    <style>
    body {background: linear-gradient(to right, black, #1DB954) !important; color: white;}
    .stApp {background: linear-gradient(to right, black, #1DB954) !important;}
    h1, h2, h3, p {color: white !important;}
    .cover {border-radius: 15px; margin: 5px;}
    .fun-insight-box {background: #333; color: white; padding: 15px; border-radius: 10px; margin-top: 20px;}
    .insight-header {font-size: 1.2em; margin-top: 15px;}
    .artist-box {display: flex; align-items: center; margin-bottom: 15px;}
    .artist-img {margin-right: 10px; border-radius: 50%; width: 60px; height: 60px;}
    .tabs-container {display: flex; justify-content: center; gap: 20px; margin-top: 10px; margin-bottom: 20px;}
    .tab {color: white; padding: 10px 15px; cursor: pointer; border-radius: 5px;}
    .tab:hover {background-color: #1DB954;}
    .active-tab {background-color: #1DB954;}
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

def fetch_liked_songs(sp):
    return fetch_spotify_data(sp.current_user_saved_tracks, limit=50)

def fetch_recommendations(sp):
    seed_tracks = fetch_spotify_data(sp.current_user_saved_tracks, limit=5)
    if not seed_tracks:
        return None
    return fetch_spotify_data(
        sp.recommendations,
        seed_tracks=[item["track"]["id"] for item in seed_tracks["items"]],
        limit=10
    )

def fetch_top_data(sp):
    top_tracks = fetch_spotify_data(sp.current_user_top_tracks, limit=5, time_range="short_term")
    top_artists = fetch_spotify_data(sp.current_user_top_artists, limit=5, time_range="short_term")
    genres = [genre for artist in top_artists["items"] for genre in artist.get("genres", [])]
    return top_tracks, top_artists, genres

def fetch_behavioral_data(sp):
    recent_plays = fetch_spotify_data(sp.current_user_recently_played, limit=50)
    hours = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ").hour for item in recent_plays["items"]]
    weekdays = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ").weekday() for item in recent_plays["items"]]
    return pd.Series(hours).value_counts(), pd.Series(weekdays).value_counts()

# Helper Functions
def render_tabs(selected_tab):
    tabs = ["Liked & Discover", "Top Insights", "Behavior"]
    html = '<div class="tabs-container">'
    for tab in tabs:
        css_class = "tab active-tab" if tab == selected_tab else "tab"
        html += f'<span class="{css_class}">{tab}</span>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
    return st.session_state.get("active_tab", tabs[0])

# Active Tab State
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "Liked & Discover"

# Main App Logic
if authenticate_user():
    sp = spotipy.Spotify(auth=st.session_state["token_info"]["access_token"])

    # Top Tabs
    active_tab = render_tabs(st.session_state["active_tab"])

    if active_tab == "Liked & Discover":
        st.title("Liked Songs and Recommendations")
        feature = st.radio("What do you want to explore?", ["Liked Songs", "Discover New Songs"])

        if feature == "Liked Songs":
            st.header("Liked Songs")
            liked_songs = fetch_liked_songs(sp)
            for item in random.sample(liked_songs["items"], min(len(liked_songs["items"]), 10)):
                track = item["track"]
                st.markdown(f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <img src="{track['album']['images'][0]['url']}" alt="Cover" width="80" height="80" class="cover">
                        <div style="margin-left: 10px;">
                            <p>{track['name']} by {track['artists'][0]['name']}</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        elif feature == "Discover New Songs":
            st.header("Discover New Songs")
            recommendations = fetch_recommendations(sp)
            for track in recommendations["tracks"]:
                st.markdown(f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <img src="{track['album']['images'][0]['url']}" alt="Cover" width="80" height="80" class="cover">
                        <div style="margin-left: 10px;">
                            <p>{track['name']} by {track['artists'][0]['name']}</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    elif active_tab == "Top Insights":
        st.title("Your Top Insights (Last Month)")
        top_tracks, top_artists, genres = fetch_top_data(sp)

        st.header("Your Top Songs")
        for track in top_tracks["items"]:
            st.write(f"{track['name']} by {track['artists'][0]['name']}")

        st.header("Your Top Artists")
        for artist in top_artists["items"]:
            st.write(artist["name"])

        st.header("Genres You Vibe With")
        st.write(", ".join(genres[:5]))

        st.header("Some Fun Thoughts on Your Taste")
        insights = [
            "You're like the curator of vibes.",
            "You have the audacity to listen to amazing music, but no one's watching.",
            "Your playlist might be cooler than 90% of people... or so we think."
        ]
        for insight in insights:
            st.markdown(f"""
                <div class="fun-insight-box">
                    {insight}
                </div>
            """)

    elif active_tab == "Behavior":
        st.title("Your Listening Behavior")
        listening_hours, listening_weekdays = fetch_behavioral_data(sp)

        st.header("Your Listening Hours")
        fig, ax = plt.subplots()
        listening_hours.sort_index().plot(kind="bar", ax=ax, color="#1DB954")
        ax.set_title("Hourly Listening Trends")
        ax.set_xlabel("Hour of the Day")
        ax.set_ylabel("Tracks Played")
        st.pyplot(fig)

        st.header("Genres You Lean Toward")
        genre_counts = pd.Series(["Pop", "Rock", "Indie", "Electronic"]).sample(frac=1).reset_index(drop=True)
        fig, ax = plt.subplots()
        genre_counts.plot(kind="pie", autopct="%1.1f%%", ax=ax, colors=["#FF5733", "#33FF57", "#3357FF", "#FF33A1"])
        ax.set_title("Genre Distribution")
        st.pyplot(fig)

else:
    st.write("Please log in to access your Spotify data.")
