import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
from requests.exceptions import ReadTimeout

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

# Streamlit configuration
st.set_page_config(
    page_title="Wvvy",
    page_icon="〰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
    <style>
    body {background: linear-gradient(to right, black, #1DB954) !important;}
    .stApp {background: linear-gradient(to right, black, #1DB954) !important;}
    h1, h2, h3 {color: white !important;}
    .highlight {background-color: #1DB954; color: black; padding: 2px 6px; border-radius: 4px;}
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
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Authentication failed: {e}")
        else:
            auth_url = sp_oauth.get_authorize_url()
            st.markdown(f'<a href="{auth_url}" target="_self">**Login with Spotify**</a>', unsafe_allow_html=True)
    return "token_info" in st.session_state

# Function to refresh token if expired
def refresh_token():
    if "token_info" in st.session_state and sp_oauth.is_token_expired(st.session_state["token_info"]):
        st.session_state["token_info"] = sp_oauth.refresh_access_token(st.session_state["token_info"]["refresh_token"])

# Function to fetch user's Spotify data with error handling
def fetch_spotify_data(sp_func, *args, retries=5, **kwargs):
    for attempt in range(retries):
        try:
            return sp_func(*args, **kwargs)
        except (spotipy.exceptions.SpotifyException, ReadTimeout) as e:
            if isinstance(e, spotipy.exceptions.SpotifyException) and e.http_status == 429:
                retry_after = int(e.headers.get("Retry-After", 1))
                time.sleep(retry_after)
            else:
                time.sleep(2 ** attempt)
    return None

# Function to get liked songs
def get_liked_songs(sp):
    songs, offset = [], 0
    while True:
        results = fetch_spotify_data(sp.current_user_saved_tracks, limit=50, offset=offset)
        if not results or not results["items"]:
            break
        for item in results["items"]:
            track = item["track"]
            features = fetch_spotify_data(sp.audio_features, track["id"])[0]
            songs.append({
                "Name": track["name"],
                "Artist": track["artists"][0]["name"],
                "Energy": features["energy"],
                "Valence": features["valence"],
                "Popularity": track["popularity"]
            })
        offset += 50
    return pd.DataFrame(songs)

# Function to display insights
def display_insights(df):
    if df.empty:
        st.write("No data available.")
        return
    avg_energy = df["Energy"].mean()
    avg_valence = df["Valence"].mean()
    avg_popularity = df["Popularity"].mean()

    st.write("### Insights from Your Liked Songs")
    col1, col2, col3 = st.columns(3)
    col1.metric("Average Energy", f"{avg_energy:.2f}")
    col2.metric("Average Valence", f"{avg_valence:.2f}")
    col3.metric("Average Popularity", f"{avg_popularity:.1f}")

    st.write("#### Distribution of Energy and Valence")
    fig, ax = plt.subplots()
    df.plot.scatter(x="Energy", y="Valence", alpha=0.7, ax=ax)
    ax.set_title("Energy vs Valence")
    st.pyplot(fig)

# Function to recommend songs
def recommend_songs(sp, mood, intensity):
    top_tracks = fetch_spotify_data(sp.current_user_top_tracks, limit=10)
    if not top_tracks or not top_tracks["items"]:
        st.write("No sufficient data for recommendations.")
        return
    seed_tracks = [track["id"] for track in top_tracks["items"][:5]]
    mood_map = {"Happy": (0.8, 0.7), "Calm": (0.3, 0.4), "Energetic": (0.9, 0.8), "Sad": (0.2, 0.3)}
    valence, energy = [val * intensity / 5 for val in mood_map.get(mood, (0.5, 0.5))]

    recommendations = fetch_spotify_data(
        sp.recommendations,
        seed_tracks=seed_tracks,
        limit=10,
        target_valence=valence,
        target_energy=energy
    )
    if not recommendations or not recommendations["tracks"]:
        st.write("No recommendations available.")
        return
    st.write("### Recommended Songs")
    for rec in recommendations["tracks"]:
        st.write(f"**{rec['name']}** by {rec['artists'][0]['name']}")

# Main App Logic
if authenticate_user():
    refresh_token()
    sp = spotipy.Spotify(auth=st.session_state["token_info"]["access_token"])
    st.title("〰 Wvvy - Your Music Insights")

    tab1, tab2 = st.tabs(["Liked Songs Analysis", "Discover New Music"])
    with tab1:
        liked_songs_df = get_liked_songs(sp)
        if st.checkbox("Show Raw Data"):
            st.dataframe(liked_songs_df)
        display_insights(liked_songs_df)

    with tab2:
        mood = st.selectbox("Select Mood", ["Happy", "Calm", "Energetic", "Sad"])
        intensity = st.slider("Intensity", 1, 5, 3)
        recommend_songs(sp, mood, intensity)
else:
    st.write("Please log in to access your Spotify data.")
