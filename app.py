import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import random
import time

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
    page_icon="🌊",
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
    .gift-box {background: #1DB954; color: black; padding: 20px; border-radius: 15px; margin-top: 20px; font-size: 2em; font-weight: bold; text-align: center;}
    .dramatic-box {background: linear-gradient(to right, #1DB954, black); padding: 40px; border-radius: 15px; color: white; text-align: center; font-size: 2.5em; font-family: 'Courier New', Courier, monospace;}
    .personalized-box {background: #444; color: white; padding: 20px; border-radius: 15px; margin-top: 10px; font-size: 1.3em; line-height: 1.6; text-align: center;}
    </style>
""", unsafe_allow_html=True)

# Refresh Token and Initialization
def refresh_access_token():
    try:
        if "token_info" in st.session_state and "refresh_token" in st.session_state["token_info"]:
            token_info = sp_oauth.refresh_access_token(st.session_state["token_info"]["refresh_token"])
            st.session_state["token_info"] = token_info  # Update session state
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

# Fetch Liked Songs
def fetch_liked_songs(sp):
    if "liked_songs" not in st.session_state:
        st.session_state["liked_songs"] = fetch_spotify_data(sp.current_user_saved_tracks, limit=50)
    return st.session_state["liked_songs"]

# Fetch Recommendations
def fetch_recommendations(sp, mood, intensity):
    mood_map = {"Happy": (0.8, 0.7), "Calm": (0.3, 0.4), "Energetic": (0.9, 0.8), "Sad": (0.2, 0.3)}
    valence, energy = [val * intensity / 5 for val in mood_map[mood]]
    seed_tracks = fetch_spotify_data(sp.current_user_saved_tracks, limit=5)
    if not seed_tracks:
        return None
    return fetch_spotify_data(
        sp.recommendations,
        seed_tracks=[item["track"]["id"] for item in seed_tracks["items"]],
        limit=10,
        target_valence=valence,
        target_energy=energy
    )

# Fetch Top Insights for Last Month
def fetch_top_data_month(sp):
    if "top_data_month" not in st.session_state:
        top_tracks = fetch_spotify_data(sp.current_user_top_tracks, limit=5, time_range="medium_term")
        top_artists = fetch_spotify_data(sp.current_user_top_artists, limit=5, time_range="medium_term")
        genres = [genre for artist in top_artists["items"] for genre in artist.get("genres", [])]
        st.session_state["top_data_month"] = (top_tracks, top_artists, genres)
    return st.session_state["top_data_month"]

# Fetch Behavioral Data
def fetch_behavioral_data_1month(sp):
    if "behavior_data_month" not in st.session_state:
        recent_plays = fetch_spotify_data(sp.current_user_recently_played, limit=50)
        timestamps = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ") for item in recent_plays["items"]]
        df = pd.DataFrame(timestamps, columns=["played_at"])
        df["hour"] = df["played_at"].dt.hour
        df["weekday"] = df["played_at"].dt.weekday
        st.session_state["behavior_data_month"] = df
    return st.session_state["behavior_data_month"]

# Fetch Spotify Data Function
def fetch_spotify_data(sp_func, *args, retries=3, **kwargs):
    delay = 1
    for attempt in range(retries):
        try:
            return sp_func(*args, **kwargs)
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
                return None
    st.error("Failed to fetch data after multiple retries. Please try again later.")
    return None

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
        mood = st.selectbox("Choose Mood:", ["Happy", "Calm", "Energetic", "Sad"])
        intensity = st.slider("Select Intensity (1-5):", 1, 5, 3)
        feature = st.radio("What do you want to explore?", ["Liked Songs", "Discover New Songs"])

        if feature == "Liked Songs":
            st.header("Liked Songs")
            liked_songs = fetch_liked_songs(sp)
            for item in random.sample(liked_songs["items"], min(len(liked_songs["items"]), 10)):
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

        elif feature == "Discover New Songs":
            st.header("Discover New Songs")
            recommendations = fetch_recommendations(sp, mood, intensity)
            if recommendations:
                for track in recommendations["tracks"]:
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
        peak_hour = behavior_data["hour"].mode()[0]
        personality_name = random.choice(["Night Vibes Architect", "Melodic Maestro", "Groove Guardian", "Harmony Weaver"])
        personality_desc = random.choice([
            "Your playlists shape your days with rich emotions and energy.",
            "Music fuels your world with rhythm and soul, day and night.",
            "Each track you play seems to tell a story of its own.",
        ])

        st.markdown(f"""
            <div class="dramatic-box">
                Welcome, {personality_name}!
            </div>
            <div class="personalized-box">
                {personality_desc}
            </div>
        """, unsafe_allow_html=True)

        # Fetch Top Data (Last Month)
        top_tracks, top_artists, genres = fetch_top_data_month(sp)

        # Top Songs Section (Square Covers)
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

        # Top Artists Section (Circular Covers)
        st.header("Your Top Artists")
        for artist in top_artists["items"]:
            st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <img src="{artist['images'][0]['url']}" alt="Artist Cover" class="cover-circle">
                    <div style="margin-left: 10px;">
                        <p><strong>{artist['name']}</strong></p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Genres Section
        st.header("Genres You Vibe With")
        st.write(", ".join(genres[:5]))

        # Fun Insights Section
        st.header("Fun Insights")
        total_top_songs = len(top_tracks["items"])
        total_top_artists = len(top_artists["items"])
        favorite_genre = random.choice(genres).capitalize() if genres else "Unknown"

        fun_insights = [
            f"🎧 Your top genre this month is: <strong>{favorite_genre}</strong>.",
            f"🎵 You've vibed with <strong>{total_top_songs} top songs</strong> this month.",
            f"🔥 You're enjoying <strong>{total_top_artists} amazing artists</strong> recently!"
        ]

        # Display Fun Insights in Boxes
        for insight in fun_insights:
            st.markdown(f"""
                <div class="fun-insight-box">
                    {insight}
                </div>
            """, unsafe_allow_html=True)

        # Behavioral Trends (Hourly and Weekly)
        st.header("Listening Trends Over the Month")
        fig, ax = plt.subplots(facecolor="black")
        behavior_data["hour"].value_counts().sort_index().plot(kind="bar", ax=ax, color="#1DB954")
        ax.set_title("Hourly Listening Trends", color="white")
        ax.set_xlabel("Hour of the Day", color="white")
        ax.set_ylabel("Tracks Played", color="white")
        ax.tick_params(colors="white")
        st.pyplot(fig)

        st.header("Weekly Listening Trends")
        fig, ax = plt.subplots(facecolor="black")
        behavior_data["weekday"].value_counts().sort_index().plot(kind="line", ax=ax, color="#1DB954", marker="o")
        ax.set_title("Weekly Listening Trends", color="white")
        ax.set_xlabel("Day of the Week (0=Monday, 6=Sunday)", color="white")
        ax.set_ylabel("Tracks Played", color="white")
        ax.tick_params(colors="white")
        st.pyplot(fig)

else:
    st.write("Please log in to access your Spotify data.")
