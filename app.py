# File: moodify_streamlit.py

import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

# Spotify API credentials
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Spotify OAuth Scope
scope = "user-library-read user-top-read playlist-read-private user-read-recently-played"

# Streamlit Page Configuration
st.set_page_config(
    page_title="Moodify - Your Mood. Your Music.",
    page_icon="🎵",
    layout="wide"
)

# CSS for Styling
st.markdown("""
    <style>
    body {background: linear-gradient(to right, #1a1a1a, #1DB954) !important; color: white;}
    .stApp {background: linear-gradient(to right, #1a1a1a, #1DB954) !important;}
    h1, h2, h3, p {color: white !important;}
    </style>
""", unsafe_allow_html=True)

# Spotify OAuth Helper Functions
def login_with_spotify():
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=scope,
        show_dialog=True
    )
    token = auth_manager.get_access_token()
    st.session_state["sp"] = spotipy.Spotify(auth=token)

def clear_session():
    if "sp" in st.session_state:
        del st.session_state["sp"]
        st.success("Logged out successfully!")

# Fetch Spotify Data
def fetch_spotify_data(sp_func, *args, **kwargs):
    try:
        return sp_func(*args, **kwargs)
    except Exception as e:
        st.error(f"Error fetching Spotify data: {e}")
        return None

# Mood Analysis and Insights
def display_mood_insights(data):
    st.subheader("🎨 Mood Insights")
    mood_colors = {
        "Happy": "#FFD700",
        "Energetic": "#FF4500",
        "Calm": "#1E90FF",
        "Sad": "#4B0082"
    }

    # Example Insights
    st.markdown(f"**Mood of the Week:**")
    st.markdown(f"- You mostly felt **Calm** this week (45%). 🌊")
    st.markdown(f"- Your top genre for the week is **Chillstep**. 🎶")
    st.markdown(f"- Moods mapped to food colors: Chocolate 🍫 for Sad mood.")

# Visualization of Moods
def plot_mood_chart(data):
    mood_counts = data["mood"].value_counts()
    plt.figure(figsize=(8, 6))
    mood_counts.plot(kind="bar", color=["#FFD700", "#FF4500", "#1E90FF", "#4B0082"])
    plt.title("Mood Distribution Over the Week", color="white")
    plt.xlabel("Mood", color="white")
    plt.ylabel("Count", color="white")
    plt.xticks(color="white")
    plt.yticks(color="white")
    plt.gca().set_facecolor("black")
    plt.gcf().set_facecolor("black")
    st.pyplot(plt)

# Main App Logic
if "sp" not in st.session_state:
    st.title("Moodify 🎵")
    st.subheader("Your Mood. Your Music.")
    st.markdown("Discover insights about your music and mood.")
    if st.button("Log in with Spotify"):
        login_with_spotify()
else:
    sp = st.session_state["sp"]
    st.sidebar.button("Logout", on_click=clear_session)
    page = st.sidebar.radio("Navigate to:", ["Discover Music", "Mood Insights"])

    if page == "Discover Music":
        st.title("🎧 Discover New & Liked Songs")
        mood = st.selectbox("Choose a Mood:", ["Happy", "Energetic", "Calm", "Sad"])
        feature = st.radio("Explore:", ["Liked Songs", "Discover New Songs"])

        if feature == "Liked Songs":
            liked_songs = fetch_spotify_data(sp.current_user_saved_tracks, limit=50)
            if liked_songs:
                for item in liked_songs["items"]:
                    st.markdown(
                        f"""
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <img src="{item['track']['album']['images'][0]['url']}" alt="Cover" style="width: 80px; height: 80px; border-radius: 10px;">
                            <div>
                                <p><strong>{item['track']['name']}</strong></p>
                                <p>by {', '.join(artist['name'] for artist in item['track']['artists'])}</p>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    elif page == "Mood Insights":
        st.title("📊 Mood Insights")
        # Example behavior data simulation
        behavior_data = pd.DataFrame({
            "mood": ["Happy", "Sad", "Calm", "Energetic", "Happy"],
            "count": [10, 7, 15, 5, 13]
        })
        display_mood_insights(behavior_data)
        plot_mood_chart(behavior_data)
