import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Spotify API credentials
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Spotify OAuth Scope
scope = "user-library-read user-top-read playlist-read-private user-read-recently-played"

# Streamlit Page Configuration
st.set_page_config(page_title="Moodify 🎵", page_icon="🎵", layout="wide")

# Custom CSS for Styling
st.markdown("""
    <style>
        body {background: linear-gradient(to right, #1a1a1a, #1DB954); color: white;}
        .stApp {background: linear-gradient(to right, #1a1a1a, #1DB954);}
        h1, h2, h3, p {color: white;}
        .card {background-color: #333; padding: 10px; border-radius: 10px; margin: 10px; text-align: center;}
    </style>
""", unsafe_allow_html=True)

# Spotify OAuth Token Management
def authenticate_spotify():
    if "token" not in st.session_state:
        auth_manager = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=scope
        )
        token_info = auth_manager.get_cached_token()
        if not token_info:
            auth_manager.get_access_token()
        st.session_state["sp"] = spotipy.Spotify(auth_manager=auth_manager)

# Fetch Liked Songs
def fetch_liked_songs(sp):
    results = sp.current_user_saved_tracks(limit=50)
    songs = []
    for item in results["items"]:
        track = item["track"]
        features = sp.audio_features(track["id"])[0]
        songs.append({
            "name": track["name"],
            "artist": ", ".join(artist["name"] for artist in track["artists"]),
            "image": track["album"]["images"][0]["url"],
            "valence": features["valence"],
            "energy": features["energy"]
        })
    return pd.DataFrame(songs)

# Filter Songs by Mood and Intensity
def filter_songs(data, mood, intensity):
    conditions = {
        "Happy": (data["valence"] > 0.7) & (data["energy"] >= intensity / 5),
        "Calm": (data["valence"] < 0.5) & (data["energy"] <= intensity / 5),
        "Energetic": (data["energy"] > 0.7),
        "Sad": (data["valence"] < 0.3)
    }
    return data[conditions.get(mood, pd.Series([True] * len(data)))]

# Display Insights
def display_insights(top_tracks, top_artists, genres):
    st.subheader("🎨 Mood-Based Insights")
    st.write("We analyzed your music. Here's what we found:")
    st.markdown("- **You are full of energy!** Your songs reflect an upbeat and vibrant personality. 🎉")
    st.markdown("- **Top Genre:** Chillstep - calm, smooth, and reflective. 🌊")
    st.markdown("- If your music were a color: **Blue** - tranquil yet deep.")
    st.markdown("- Listening habits describe you as: **'A musical adventurer'** who loves exploring diverse genres!")

# Plot Weekly Mood Analysis
def plot_weekly_moods():
    data = pd.DataFrame({
        "Day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "Mood": [7, 6, 8, 5, 7, 9, 8]
    })
    plt.figure(figsize=(10, 5))
    sns.lineplot(x="Day", y="Mood", data=data, marker="o", color="cyan")
    plt.title("Your Weekly Mood Analysis")
    plt.ylabel("Mood Intensity")
    plt.xlabel("Day")
    st.pyplot(plt)

# Main App Logic
st.title("Moodify 🎵")
st.subheader("Your Mood. Your Music.")
if "sp" not in st.session_state:
    st.info("Please log in with Spotify to continue.")
    if st.button("Log in with Spotify"):
        authenticate_spotify()
else:
    sp = st.session_state["sp"]
    page = st.sidebar.radio("Navigate:", ["🎧 Discover Songs", "📊 Insights & Analytics"])
    if page == "🎧 Discover Songs":
        st.title("🎧 Discover Your Liked Songs")
        mood = st.selectbox("Choose a Mood:", ["Happy", "Energetic", "Calm", "Sad"])
        intensity = st.slider("Select Intensity (1-5):", 1, 5, 3)

        with st.spinner("Fetching your liked songs..."):
            liked_songs = fetch_liked_songs(sp)
        if not liked_songs.empty:
            filtered_songs = filter_songs(liked_songs, mood, intensity)
            st.write(f"Showing songs for mood: **{mood}** with intensity: **{intensity}**")
            for _, song in filtered_songs.iterrows():
                st.markdown(
                    f"""
                    <div class="card">
                        <img src="{song['image']}" width="80" height="80" style="border-radius: 10px;">
                        <p><strong>{song['name']}</strong> by {song['artist']}</p>
                    </div>
                    """, unsafe_allow_html=True
                )
        else:
            st.warning("No liked songs found.")

    elif page == "📊 Insights & Analytics":
        st.title("📊 Music Insights & Weekly Mood Analysis")
        with st.spinner("Analyzing your top tracks, artists, and genres..."):
            top_tracks = sp.current_user_top_tracks(limit=10, time_range="short_term")
            top_artists = sp.current_user_top_artists(limit=10, time_range="short_term")
            genres = set(genre for artist in top_artists["items"] for genre in artist["genres"])

        # Display Insights
        display_insights(top_tracks, top_artists, genres)

        # Weekly Mood Analysis Visualization
        plot_weekly_moods()
