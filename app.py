import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import random
import logging
from requests.exceptions import ConnectionError

# Configure logging
logging.basicConfig(level=logging.INFO)

# Spotify API credentials
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Spotify OAuth Scope
scope = "user-library-read user-top-read playlist-read-private user-read-recently-played"

# Spotify OAuth Setup
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=scope
)

# Streamlit Page Configuration
st.set_page_config(
    page_title="WVY - Your Spotify Companion",
    page_icon="🎧",
    layout="wide"
)

# CSS for Styling
st.markdown("""
    <style>
    body {background: linear-gradient(to right, black, #1DB954) !important; color: white;}
    .stApp {background: linear-gradient(to right, black, #1DB954) !important;}
    h1, h2, h3, p {color: white !important;}
    .brand {position: absolute; top: 20px; left: 20px; font-size: 3.5em; font-weight: bold; color: white;}
    .cover-circle {border-radius: 50%; margin: 10px; width: 120px; height: 120px;}
    .cover-square {border-radius: 10px; margin: 10px; width: 120px; height: 120px;}
    .fun-insight-box {background: #333; color: white; padding: 15px; border-radius: 10px; margin-top: 20px; font-size: 1.2em; line-height: 1.5; text-align: center;}
    .dramatic-box {background: linear-gradient(to right, #1DB954, black); padding: 40px; border-radius: 15px; color: white; text-align: center; font-size: 2.5em; font-family: 'Courier New', Courier, monospace;}
    .personalized-box {background: #444; color: white; padding: 20px; border-radius: 15px; margin-top: 10px; font-size: 1.3em; line-height: 1.6; text-align: center;}
    </style>
""", unsafe_allow_html=True)

# Refresh Token and Initialization
def refresh_access_token():
    try:
        if "token_info" in st.session_state and "refresh_token" in st.session_state["token_info"]:
            token_info = sp_oauth.refresh_access_token(st.session_state["token_info"]["refresh_token"])
            st.session_state["token_info"] = token_info
            return token_info["access_token"]
        else:
            st.error("No refresh token available. Please log in again.")
            return None
    except Exception as e:
        st.error(f"Failed to refresh access token: {e}")
        return None

def initialize_spotify():
    if "token_info" in st.session_state:
        access_token = st.session_state["token_info"]["access_token"]
        return spotipy.Spotify(auth=access_token)
    return None

# Authentication
def authenticate_user():
    if "token_info" not in st.session_state:
        query_params = st.experimental_get_query_params()
        if "code" in query_params:
            try:
                token_info = sp_oauth.get_access_token(query_params["code"][0])
                st.session_state["token_info"] = token_info
                st.experimental_set_query_params()
                st.success("Authentication successful! Refresh the page to continue.")
            except Exception as e:
                st.error(f"Authentication failed: {e}")
        else:
            auth_url = sp_oauth.get_authorize_url()
            st.markdown(f'<a href="{auth_url}" target="_self" style="color: white; text-decoration: none; background-color: #1DB954; padding: 10px 20px; border-radius: 5px;">Login with Spotify</a>', unsafe_allow_html=True)
    return "token_info" in st.session_state

# Fetch Spotify Data Function
def fetch_spotify_data(sp_func, *args, retries=3, **kwargs):
    for attempt in range(retries):
        try:
            logging.info(f"Attempt {attempt + 1}: Fetching data from Spotify.")
            return sp_func(*args, **kwargs)
        except ConnectionError as e:
            st.error("Connection error occurred. Please check your internet connection.")
            logging.error(f"Connection error: {e}")
            return None
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 401:  # Token expired
                st.warning("Access token expired. Attempting to refresh...")
                new_token = refresh_access_token()
                if new_token:
                    st.session_state["sp"] = initialize_spotify()  # Reinitialize Spotify client
                else:
                    st.error("Failed to refresh access token. Please log in again.")
                    return None
            else:
                st.error(f"Spotify API error: {e}")
                logging.error(f"Spotify API error: {e}")
                return None
    st.error("Failed to fetch data after multiple retries. Please try again later.")
    return None

# Fetch Data
def fetch_liked_songs(sp):
    return fetch_spotify_data(sp.current_user_saved_tracks, limit=50)

def fetch_top_data_month(sp):
    top_tracks = fetch_spotify_data(sp.current_user_top_tracks, limit=5, time_range="medium_term")
    top_artists = fetch_spotify_data(sp.current_user_top_artists, limit=5, time_range="medium_term")
    genres = [genre for artist in top_artists["items"] for genre in artist.get("genres", [])]
    return top_tracks, top_artists, genres

def fetch_behavioral_data_1month(sp):
    recent_plays = fetch_spotify_data(sp.current_user_recently_played, limit=50)
    if not recent_plays:
        st.warning("No recent plays data available. Try again later.")
        return pd.DataFrame()  # Return an empty DataFrame to avoid errors
    timestamps = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ") for item in recent_plays["items"]]
    df = pd.DataFrame(timestamps, columns=["played_at"])
    df["hour"] = df["played_at"].dt.hour
    df["weekday"] = df["played_at"].dt.weekday
    return df

# Main App Logic
if authenticate_user():
    if "sp" not in st.session_state:
        st.session_state["sp"] = initialize_spotify()

    sp = st.session_state["sp"]
    st.markdown('<div class="brand">WVY</div>', unsafe_allow_html=True)

    page = st.radio("Navigate to:", ["Liked Songs & Discover New", "Insights & Behavior"])

    # Page: Liked Songs & Discover New
    if page == "Liked Songs & Discover New":
        st.title("Liked Songs & Discover New")
        liked_songs = fetch_liked_songs(sp)
        for item in liked_songs["items"]:
            track = item["track"]
            st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <img src="{track['album']['images'][0]['url']}" alt="Cover" class="cover-square">
                    <div style="margin-left: 10px;">
                        <p><strong>{track['name']}</strong></p>
                        <p>by {track['artists'][0]['name']}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # Page: Insights & Behavior (Last Month)
    elif page == "Insights & Behavior":
        st.title("Insights & Behavior (Last Month)")

        # Fun Music Personality
        behavior_data = fetch_behavioral_data_1month(sp)
        if not behavior_data.empty:
            peak_hour = behavior_data["hour"].mode()[0]
            personality_name = random.choice(["Vibe Dealer", "Groove Goblin", "Harmony Hustler"])
            personality_desc = f"You vibe hardest at {peak_hour}:00 hrs. Iconic!"

            st.markdown(f"""
                <div class="dramatic-box">
                    Welcome, {personality_name}!
                </div>
                <div class="personalized-box">
                    {personality_desc}
                </div>
            """, unsafe_allow_html=True)

        # Top Songs Section
        top_tracks, top_artists, genres = fetch_top_data_month(sp)
        st.header("Your Top Songs")
        for track in top_tracks["items"]:
            st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <img src="{track['album']['images'][0]['url']}" alt="Cover" class="cover-square">
                    <div style="margin-left: 10px;">
                        <p><strong>{track['name']}</strong></p>
                        <p>by {track['artists'][0]['name']}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Funniest Insights
        favorite_genre = random.choice(genres).capitalize() if genres else "Unknown"
        st.header("Fun Insights")
        funny_insights = [
            f"🎤 Most played genre: {favorite_genre}.",
            f"🌙 You vibe hardest around {peak_hour}:00 hrs."
        ]
        for insight in funny_insights:
            st.markdown(f"""
                <div class="fun-insight-box">
                    {insight}
                </div>
            """, unsafe_allow_html=True)

        # Behavioral Trends Heatmap
        if not behavior_data.empty:
            st.header("Listening Trends: When You’re the Main Character 🎭")
            heatmap_data = behavior_data.groupby(['hour', 'weekday']).size().unstack(fill_value=0)
            fig, ax = plt.subplots(figsize=(10, 6))
            im = ax.imshow(heatmap_data, cmap='viridis')
            ax.set_title("Your Listening Hours Heatmap 🌈")
            ax.set_xlabel("Day of the Week")
            ax.set_ylabel("Hour (24hr)")
            plt.colorbar(im, orientation='vertical', ax=ax, label="Songs Played")
            st.pyplot(fig)
else:
    st.write("Please log in to access your Spotify data.")
