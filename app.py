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
    .fun-insight-box {background: #333; padding: 15px; border-radius: 10px; margin-top: 20px;}
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
                st.experimental_set_query_params()
                st.experimental_rerun()
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

# 1. Feature: Filtered Liked Songs and Discover New Songs
def filter_liked_songs(sp, mood, intensity):
    mood_map = {"Happy": (0.8, 0.7), "Calm": (0.3, 0.4), "Energetic": (0.9, 0.8), "Sad": (0.2, 0.3)}
    valence, energy = [val * intensity / 5 for val in mood_map[mood]]
    liked_songs = fetch_spotify_data(sp.current_user_saved_tracks, limit=20)
    return liked_songs

def discover_new_songs(sp, mood, intensity):
    mood_map = {"Happy": (0.8, 0.7), "Calm": (0.3, 0.4), "Energetic": (0.9, 0.8), "Sad": (0.2, 0.3)}
    valence, energy = [val * intensity / 5 for val in mood_map[mood]]
    recommendations = fetch_spotify_data(
        sp.recommendations,
        seed_tracks=[item["track"]["id"] for item in fetch_spotify_data(sp.current_user_saved_tracks, limit=5)["items"]],
        limit=10,
        target_valence=valence,
        target_energy=energy
    )
    return recommendations

# 2. Feature: Last Month's Top Data
def get_top_items(sp, time_range="short_term"):
    top_tracks = fetch_spotify_data(sp.current_user_top_tracks, limit=10, time_range=time_range)
    top_artists = fetch_spotify_data(sp.current_user_top_artists, limit=10, time_range=time_range)
    genres = [genre for artist in top_artists["items"] for genre in artist.get("genres", [])]
    return top_tracks, top_artists, genres

# 3. Feature: Behavioral Insights
def get_recently_played(sp):
    recent_plays = fetch_spotify_data(sp.current_user_recently_played, limit=50)
    hours = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ").hour for item in recent_plays["items"]]
    return pd.Series(hours).value_counts()

# Fun Personality Label
def get_personality_label(peak_hour):
    if 0 <= peak_hour <= 6:
        return "Night Owl", "Grooving in the quiet hours!"
    elif 7 <= peak_hour <= 12:
        return "Morning Motivator", "Getting inspired early in the day!"
    elif 13 <= peak_hour <= 18:
        return "Afternoon Explorer", "Discovering beats while staying productive."
    else:
        return "Evening Relaxer", "Unwinding with chill vibes."

# Main App Logic
if authenticate_user():
    sp = spotipy.Spotify(auth=st.session_state["token_info"]["access_token"])

    st.title("🎧 Wvvy - Your Personalized Music World")

    # Mood-Intensity Filter: Liked Songs
    st.header("🎵 Explore Your Liked Songs by Mood")
    mood = st.selectbox("Select Mood:", ["Happy", "Calm", "Energetic", "Sad"])
    intensity = st.slider("Select Intensity (1-5):", 1, 5, 3)
    liked_songs = filter_liked_songs(sp, mood, intensity)
    if liked_songs:
        st.write(f"### Liked Songs for Your {mood} Mood:")
        for item in random.sample(liked_songs["items"], min(len(liked_songs["items"]), 10)):
            track = item["track"]
            st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <img src="{track['album']['images'][0]['url']}" alt="Cover" width="80" height="80" class="cover">
                    <div style="margin-left: 10px;">
                        <p><b>{track['name']}</b><br><i>{track['artists'][0]['name']}</i></p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Discover New Songs
    st.header("🌟 Discover New Recommendations")
    recommendations = discover_new_songs(sp, mood, intensity)
    if recommendations:
        st.write("### Fresh Recommendations:")
        for track in recommendations["tracks"]:
            st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <img src="{track['album']['images'][0]['url']}" alt="Cover" width="80" height="80" class="cover">
                    <div style="margin-left: 10px;">
                        <p><b>{track['name']}</b><br><i>{track['artists'][0]['name']}</i></p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Last Month's Top Music
    st.header("🎶 Last Month's Top Music, Artists, and Genres")
    top_tracks, top_artists, genres = get_top_items(sp, "short_term")
    st.write("### Top Tracks:")
    for track in top_tracks["items"][:5]:
        st.write(f"**{track['name']}** by {track['artists'][0]['name']}")
    st.write("### Top Artists:")
    for artist in top_artists["items"][:5]:
        st.write(f"**{artist['name']}**")
    st.write("### Top Genres:")
    st.write(", ".join(set(genres[:5])))

    st.divider()

    # Fun Insight
    st.write("### 🎉 Fun Insight:")
    st.markdown("""
        <div class="fun-insight-box">
            <p>You've listened to more music than 90% of people in your region. You're a true audiophile!</p>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Listening Behavior
    st.header("📊 Your Listening Behavior")
    listening_hours = get_recently_played(sp)
    peak_hour = listening_hours.idxmax()
    personality, description = get_personality_label(peak_hour)

    # Plotting Listening Hours
    st.write("### Listening Patterns Throughout the Day")
    fig, ax = plt.subplots()
    listening_hours.sort_index().plot(kind="bar", ax=ax, color="#1DB954")
    ax.set_title("Listening Behavior")
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Tracks Played")
    st.pyplot(fig)

    # Personality Insight
    st.write("### Your Music Personality:")
    st.success(f"**{personality}:** {description}")

else:
    st.write("Please log in to access your Spotify data.")
