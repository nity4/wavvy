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
    .cover-circle {border-radius: 50%; margin: 10px; width: 100px; height: 100px;}
    .cover-square {border-radius: 10px; margin: 10px; width: 100px; height: 100px;}
    .fun-insight-box {background: #333; color: white; padding: 15px; border-radius: 10px; margin-top: 20px; font-size: 1.2em; line-height: 1.5;}
    </style>
""", unsafe_allow_html=True)

# Refresh Token Function
def refresh_access_token():
    """
    Refresh the Spotify access token using the refresh token.
    """
    if "token_info" in st.session_state:
        try:
            token_info = sp_oauth.refresh_access_token(st.session_state["token_info"]["refresh_token"])
            st.session_state["token_info"] = token_info  # Update session state with new token info
            return token_info["access_token"]
        except Exception as e:
            st.error(f"Failed to refresh access token: {e}")
            return None
    else:
        st.error("No token info found. Please log in again.")
        return None

# Fetch Spotify Data Function
def fetch_spotify_data(sp_func, *args, retries=3, **kwargs):
    """
    Fetch data from the Spotify API with retries, exponential backoff, and token refresh.
    """
    delay = 1  # Start with a 1-second delay for retries
    for attempt in range(1, retries + 1):
        try:
            return sp_func(*args, **kwargs)
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 401:  # Unauthorized: Access token expired
                st.warning("Access token expired. Refreshing token...")
                new_token = refresh_access_token()
                if new_token:
                    global sp
                    sp = spotipy.Spotify(auth=new_token)  # Reinitialize Spotify client
                else:
                    st.error("Failed to refresh access token. Please log in again.")
                    return None
            elif "rate limit" in str(e).lower():
                st.warning(f"Rate limit hit. Retrying in {delay} seconds... (Attempt {attempt}/{retries})")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                st.warning(f"Attempt {attempt} failed: {e}")
                time.sleep(delay)
        delay *= 2  # Increase delay after each attempt

    st.error("Failed to fetch data after multiple retries. Please try again later.")
    return None

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
def fetch_liked_songs(sp):
    if "liked_songs" not in st.session_state:
        st.session_state["liked_songs"] = fetch_spotify_data(sp.current_user_saved_tracks, limit=50)
    return st.session_state["liked_songs"]

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

def fetch_top_data(sp):
    if "top_data" not in st.session_state:
        top_tracks = fetch_spotify_data(sp.current_user_top_tracks, limit=5, time_range="short_term")
        top_artists = fetch_spotify_data(sp.current_user_top_artists, limit=5, time_range="short_term")
        genres = [genre for artist in top_artists["items"] for genre in artist.get("genres", [])]
        st.session_state["top_data"] = (top_tracks, top_artists, genres)
    return st.session_state["top_data"]

def fetch_behavioral_data(sp):
    if "behavior_data" not in st.session_state:
        recent_plays = fetch_spotify_data(sp.current_user_recently_played, limit=50)
        hours = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ").hour for item in recent_plays["items"]]
        weekdays = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ").weekday() for item in recent_plays["items"]]
        st.session_state["behavior_data"] = (pd.Series(hours).value_counts(), pd.Series(weekdays).value_counts())
    return st.session_state["behavior_data"]

# Main App Logic
if authenticate_user():
    sp = spotipy.Spotify(auth=st.session_state["token_info"]["access_token"])

    # Display Brand Name
    st.markdown('<div class="brand">WVY</div>', unsafe_allow_html=True)

    # Navigation Menu
    page = st.radio("Navigate to:", ["Liked Songs and Recommendations", "Top Insights", "Behavior"])

    if page == "Liked Songs and Recommendations":
        st.title("Liked Songs and Recommendations")
        mood = st.selectbox("Choose Mood:", ["Happy", "Calm", "Energetic", "Sad"])
        intensity = st.slider("Select Intensity (1-5):", 1, 5, 3)
        feature = st.radio("What do you want to explore?", ["Liked Songs", "Discover New Songs"])

        if feature == "Liked Songs":
            st.header("Liked Songs")
            with st.spinner("Fetching your liked songs..."):
                liked_songs = fetch_liked_songs(sp)
            if liked_songs:
                for item in random.sample(liked_songs["items"], min(len(liked_songs["items"]), 10)):
                    track = item["track"]
                    st.markdown(f"""
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <img src="{track['album']['images'][0]['url']}" alt="Cover" class="cover-circle">
                            <div style="margin-left: 10px;">
                                <p><strong>{track['name']}</strong></p>
                                <p>by {track['artists'][0]['name']}</p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("Could not load your liked songs. Please try again later.")

        elif feature == "Discover New Songs":
            st.header("Discover New Songs")
            with st.spinner("Fetching recommendations..."):
                recommendations = fetch_recommendations(sp, mood, intensity)
            if recommendations:
                for track in recommendations["tracks"]:
                    st.markdown(f"""
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <img src="{track['album']['images'][0]['url']}" alt="Cover" class="cover-circle">
                            <div style="margin-left: 10px;">
                                <p><strong>{track['name']}</strong></p>
                                <p>by {track['artists'][0]['name']}</p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("No recommendations available. Try adjusting the mood or intensity.")

    elif page == "Top Insights":
        st.title("Your Top Insights (Last Month)")
        top_tracks, top_artists, genres = fetch_top_data(sp)

        st.header("Your Top Songs")
        for track in top_tracks["items"]:
            st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <img src="{track['album']['images'][0]['url']}" alt="Cover" class="cover-square">
                    <div style="margin-left: 10px;">
                        <p style="margin: 0;"><strong>{track['name']}</strong></p>
                        <p style="margin: 0;">by {track['artists'][0]['name']}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.header("Your Top Artists")
        for artist in top_artists["items"]:
            st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <img src="{artist['images'][0]['url']}" alt="Artist Cover" class="cover-circle" style="width: 80px; height: 80px;">
                    <div style="margin-left: 10px;">
                        <p style="margin: 0;"><strong>{artist['name']}</strong></p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

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

    elif page == "Behavior":
        st.title("Your Listening Behavior")
        listening_hours, listening_weekdays = fetch_behavioral_data(sp)

        st.header("Hourly Listening Trends")
        fig, ax = plt.subplots()
        listening_hours.sort_index().plot(kind="bar", ax=ax, color="#1DB954")
        ax.set_title("Hourly Listening Trends")
        ax.set_xlabel("Hour of the Day")
        ax.set_ylabel("Tracks Played")
        st.pyplot(fig)

        st.header("Weekly Listening Trends")
        fig, ax = plt.subplots()
        listening_weekdays.sort_index().plot(kind="bar", ax=ax, color="#1DB954")
        ax.set_title("Weekly Listening Trends")
        ax.set_xlabel("Day of the Week (0=Monday, 6=Sunday)")
        ax.set_ylabel("Tracks Played")
        st.pyplot(fig)

        st.header("Your Music Personality")
        if listening_hours.idxmax() >= 18:
            st.write("🎶 Night Owl: You love vibing late into the night!")
        elif listening_hours.idxmax() < 12:
            st.write("☀️ Morning Melodist: Your mornings are filled with rhythm!")
        else:
            st.write("🌇 Daytime Dreamer: You jam the most during the day.")
else:
    st.write("Please log in to access your Spotify data.")
