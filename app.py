import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
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
    .brand {text-align: center; font-size: 4em; font-weight: bold; color: white; margin-top: 10px;}
    .description {text-align: center; font-size: 1.5em; color: white; margin-top: -10px; margin-bottom: 20px;}
    .tabs-container {display: flex; justify-content: center; gap: 20px; margin-top: 20px; margin-bottom: 30px;}
    .tab {color: white; padding: 10px 20px; cursor: pointer; border-radius: 10px; border: 2px solid #1DB954;}
    .tab:hover {background-color: #1DB954; color: black;}
    .active-tab {background-color: #1DB954; color: black; border: none;}
    .cover-square {width: 80px; height: 80px; border-radius: 10px; margin-right: 10px;}
    .cover-circle {width: 80px; height: 80px; border-radius: 50%; margin-right: 10px;}
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
            st.markdown('<div class="brand">WVY</div>', unsafe_allow_html=True)
            st.markdown('<div class="description">Discover your Spotify listening habits, top songs, and behavioral patterns with WVY.</div>', unsafe_allow_html=True)
            auth_url = sp_oauth.get_authorize_url()
            st.markdown(f'<a href="{auth_url}" target="_self" style="color: white; text-decoration: none; background-color: #1DB954; padding: 10px 20px; border-radius: 5px;">Login with Spotify</a>', unsafe_allow_html=True)
    return "token_info" in st.session_state

# Navigation
def render_tabs():
    tabs = ["Liked Songs and Recommendations", "Top Insights", "Behavior"]
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

def fetch_liked_songs(sp):
    return fetch_spotify_data(sp.current_user_saved_tracks, limit=50)

def fetch_recommendations(sp):
    seed_tracks = fetch_spotify_data(sp.current_user_saved_tracks, limit=5)
    if not seed_tracks:
        return None
    return fetch_spotify_data(sp.recommendations, seed_tracks=[item["track"]["id"] for item in seed_tracks["items"]], limit=10)

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

# Main App Logic
if authenticate_user():
    sp = spotipy.Spotify(auth=st.session_state["token_info"]["access_token"])

    # Render Tabs
    active_tab = render_tabs()

    if active_tab == "Liked Songs and Recommendations":
        st.title("Liked Songs and Recommendations")
        feature = st.radio("What do you want to explore?", ["Liked Songs", "Discover New Songs"])

        if feature == "Liked Songs":
            st.header("Your Liked Songs")
            with st.spinner("Loading your liked songs..."):
                liked_songs = fetch_liked_songs(sp)
                for item in random.sample(liked_songs["items"], min(len(liked_songs["items"]), 10)):
                    track = item["track"]
                    st.markdown(f"""
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <img src="{track['album']['images'][0]['url']}" class="cover-square">
                            <p>{track['name']} by {track['artists'][0]['name']}</p>
                        </div>
                    """, unsafe_allow_html=True)

        elif feature == "Discover New Songs":
            st.header("Recommended for You")
            with st.spinner("Finding songs you'll love..."):
                recommendations = fetch_recommendations(sp)
                for track in recommendations["tracks"]:
                    st.markdown(f"""
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <img src="{track['album']['images'][0]['url']}" class="cover-square">
                            <p>{track['name']} by {track['artists'][0]['name']}</p>
                        </div>
                    """, unsafe_allow_html=True)

    elif active_tab == "Top Insights":
        st.title("Your Top Insights")
        with st.spinner("Fetching your top tracks and artists..."):
            top_tracks, top_artists, genres = fetch_top_data(sp)

            st.header("Top Tracks")
            for track in top_tracks["items"]:
                st.markdown(f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <img src="{track['album']['images'][0]['url']}" class="cover-square">
                        <p>{track['name']} by {track['artists'][0]['name']}</p>
                    </div>
                """, unsafe_allow_html=True)

            st.header("Top Artists")
            for artist in top_artists["items"]:
                st.markdown(f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <img src="{artist['images'][0]['url']}" class="cover-circle">
                        <p>{artist['name']}</p>
                    </div>
                """, unsafe_allow_html=True)

            st.header("Genres You Vibe With")
            st.write(", ".join(genres[:5]))

    elif active_tab == "Behavior":
        st.title("Your Listening Behavior")
        with st.spinner("Analyzing your behavior..."):
            listening_hours, listening_weekdays = fetch_behavioral_data(sp)

            st.header("Your Listening Hours")
            fig, ax = plt.subplots()
            listening_hours.sort_index().plot(kind="bar", ax=ax, color="#1DB954")
            ax.set_title("Hourly Listening Trends")
            ax.set_xlabel("Hour of the Day")
            ax.set_ylabel("Tracks Played")
            st.pyplot(fig)

            st.header("Genre Affinity")
            genre_counts = pd.Series(["Pop", "Rock", "Indie", "Electronic", "Hip-Hop"]).value_counts()
            fig, ax = plt.subplots()
            genre_counts.plot(kind="pie", ax=ax, autopct="%1.1f%%", startangle=90, colors=["#FF5733", "#33FF57", "#3357FF", "#FFC300", "#C70039"])
            ax.set_ylabel("")
            st.pyplot(fig)

else:
    st.write("Please log in to access your Spotify data.")
