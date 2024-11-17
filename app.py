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
    .brand {position: absolute; top: 20px; left: 20px; font-size: 3.5em; font-weight: bold; color: white;}
    .tabs-container {display: flex; justify-content: center; gap: 20px; margin-top: 20px; margin-bottom: 30px;}
    .tab {color: white; padding: 10px 20px; cursor: pointer; border-radius: 10px; border: 2px solid #1DB954;}
    .tab:hover {background-color: #1DB954; color: black;}
    .active-tab {background-color: #1DB954; color: black; border: none;}
    .cover-circle {border-radius: 50%; margin: 10px; width: 100px; height: 100px;}
    .fun-insight-box {background: #333; color: white; padding: 15px; border-radius: 10px; margin-top: 20px;}
    .genre-box {display: flex; align-items: center; margin-bottom: 15px;}
    .genre-cover {border-radius: 10px; width: 80px; height: 80px; margin-right: 15px;}
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

    html = '<div class="tabs-container">'
    for tab in tabs:
        css_class = "tab active-tab" if tab == st.session_state["active_tab"] else "tab"
        html += f'<div class="{css_class}" onClick="window.location.href=\'?active_tab={tab}\'">{tab}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

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

# Main App Logic
if authenticate_user():
    sp = spotipy.Spotify(auth=st.session_state["token_info"]["access_token"])

    # Display Brand Name
    st.markdown('<div class="brand">WVY</div>', unsafe_allow_html=True)

    # Render Tabs
    active_tab = render_tabs()

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
                        <img src="{track['album']['images'][0]['url']}" alt="Cover" width="80" height="80" class="cover-circle">
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
            st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <img src="{track['album']['images'][0]['url']}" alt="Cover" class="cover-circle">
                    <p>{track['name']} by {track['artists'][0]['name']}</p>
                </div>
            """)

        st.header("Genres You Vibe With")
        st.write(", ".join(genres[:5]))

        st.header("Fun Insights")
        insights = [
            "Your music taste is elite...but like only 3 people agree.",
            "You're the main character, and your playlist is the plot twist.",
            "You have audaciously good taste...until someone asks for recommendations."
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

else:
    st.write("Please log in to access your Spotify data.")
