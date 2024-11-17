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
    page_title="Wvvy - Personalized Music Insights",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Black-Green Theme
st.markdown("""
    <style>
    body {background: linear-gradient(to right, black, #1DB954) !important; color: white;}
    .stApp {background: linear-gradient(to right, black, #1DB954) !important;}
    h1, h2, h3, p {color: white !important;}
    .cover {border-radius: 15px; margin: 5px;}
    .fun-insight-box {background: #333; color: white; padding: 15px; border-radius: 10px; margin-top: 20px;}
    .artist-box {display: flex; align-items: center; margin-bottom: 15px;}
    .artist-img {margin-right: 10px; border-radius: 50%; width: 60px; height: 60px;}
    </style>
""", unsafe_allow_html=True)

# Function to authenticate user
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

# Fetch data with retry logic
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

# Fetch Liked Songs
def fetch_liked_songs(sp, mood, intensity):
    mood_map = {"Happy": (0.8, 0.7), "Calm": (0.3, 0.4), "Energetic": (0.9, 0.8), "Sad": (0.2, 0.3)}
    valence, energy = [val * intensity / 5 for val in mood_map[mood]]
    liked_songs = fetch_spotify_data(sp.current_user_saved_tracks, limit=50)
    return liked_songs

# Fetch Top Data
def fetch_top_data(sp):
    top_tracks = fetch_spotify_data(sp.current_user_top_tracks, limit=5, time_range="medium_term")
    top_artists = fetch_spotify_data(sp.current_user_top_artists, limit=5, time_range="medium_term")
    genres = [genre for artist in top_artists["items"] for genre in artist.get("genres", [])]
    return top_tracks, top_artists, genres

# Fetch Behavioral Data
def fetch_behavioral_data(sp):
    recent_plays = fetch_spotify_data(sp.current_user_recently_played, limit=50)
    hours = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ").hour for item in recent_plays["items"]]
    weekdays = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ").weekday() for item in recent_plays["items"]]
    return pd.Series(hours).value_counts(), pd.Series(weekdays).value_counts()

# Fun Personality Label
def get_personality_label(peak_hour):
    if 0 <= peak_hour <= 6:
        return "Night Owl", "Grooving in the quiet hours."
    elif 7 <= peak_hour <= 12:
        return "Morning Motivator", "Getting inspired early in the day."
    elif 13 <= peak_hour <= 18:
        return "Afternoon Explorer", "Discovering beats while staying productive."
    else:
        return "Evening Relaxer", "Unwinding with chill vibes."

# Generate Fun Insights
def generate_funny_insights(top_artists, genres):
    artist_names = [artist["name"] for artist in top_artists["items"]]
    return f"""Your top artist is **{artist_names[0]}**—basically your soulmate.
               With genres like **{genres[0]}** and **{genres[1]}**, you're clearly out here making the cool kids jealous."""

# Main App Logic
if authenticate_user():
    sp = spotipy.Spotify(auth=st.session_state["token_info"]["access_token"])

    # Sidebar Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to:", ["Liked Songs", "Top Songs, Artists, and Genres", "Behavior and Insights"])

    if page == "Liked Songs":
        st.title("Shuffled Liked Songs")
        mood = st.selectbox("Select Mood:", ["Happy", "Calm", "Energetic", "Sad"])
        intensity = st.slider("Select Intensity (1-5):", 1, 5, 3)
        liked_songs = fetch_liked_songs(sp, mood, intensity)
        if liked_songs:
            shuffled = random.sample(liked_songs["items"], min(len(liked_songs["items"]), 10))
            for item in shuffled:
                track = item["track"]
                st.markdown(f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <img src="{track['album']['images'][0]['url']}" alt="Cover" width="80" height="80" class="cover">
                        <div style="margin-left: 10px;">
                            <p><b>{track['name']}</b><br><i>{track['artists'][0]['name']}</i></p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    elif page == "Top Songs, Artists, and Genres":
        st.title("Top Songs, Artists, and Genres (Last Month)")
        top_tracks, top_artists, genres = fetch_top_data(sp)

        st.header("Top Tracks")
        for track in top_tracks["items"]:
            album_cover = track["album"]["images"][0]["url"] if track["album"]["images"] else None
            st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <img src="{album_cover}" alt="Cover" width="80" height="80" class="cover">
                    <div style="margin-left: 10px;">
                        <p><b>{track['name']}</b><br><i>{track['artists'][0]['name']}</i></p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.header("Top Artists")
        for artist in top_artists["items"]:
            artist_image = artist["images"][0]["url"] if artist["images"] else None
            st.markdown(f"""
                <div class="artist-box">
                    <img src="{artist_image}" class="artist-img">
                    <p><b>{artist['name']}</b></p>
                </div>
            """, unsafe_allow_html=True)

        st.header("Top Genres")
        st.write(", ".join(set(genres[:5])))

        st.header("Fun Insights")
        st.markdown(f"""
            <div class="fun-insight-box">
                {generate_funny_insights(top_artists, genres)}
            </div>
        """, unsafe_allow_html=True)

    elif page == "Behavior and Insights":
        st.title("Your Listening Behavior and Insights")
        listening_hours, listening_weekdays = fetch_behavioral_data(sp)

        st.header("Listening Heatmap")
        fig, ax = plt.subplots()
        listening_hours.sort_index().plot(kind="bar", ax=ax, color="#1DB954", label="Hourly Listening")
        listening_weekdays.sort_index().plot(kind="bar", ax=ax, color="#FF5733", alpha=0.5, label="Weekly Listening")
        ax.set_title("Listening Behavior")
        ax.set_xlabel("Time/Day")
        ax.legend()
        st.pyplot(fig)

        peak_hour = listening_hours.idxmax()
        personality, description = get_personality_label(peak_hour)
        st.header("Your Music Personality")
        st.success(f"**{personality}:** {description}")
else:
    st.write("Please log in to access your Spotify data.")
