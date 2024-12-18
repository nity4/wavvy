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
    .mood-card {border-radius: 10px; background-color: #444; padding: 10px; margin: 10px; text-align: center;}
    </style>
""", unsafe_allow_html=True)

# Spotify OAuth Helper Functions
def authenticate_spotify():
    try:
        auth_manager = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=scope,
            show_dialog=True
        )
        token = auth_manager.get_access_token(as_dict=True)
        st.session_state["sp"] = spotipy.Spotify(auth=token["access_token"])
        st.success("Authentication successful!")
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        st.stop()

def clear_session():
    if "sp" in st.session_state:
        del st.session_state["sp"]
    st.success("Logged out successfully!")

# Fetch Data
def fetch_liked_songs(sp):
    results = sp.current_user_saved_tracks(limit=50)
    songs = []
    for item in results['items']:
        track = item['track']
        features = sp.audio_features(track['id'])[0]
        songs.append({
            "name": track['name'],
            "artist": ", ".join(artist['name'] for artist in track['artists']),
            "mood": get_mood_from_features(features),
            "image": track['album']['images'][0]['url'] if track['album']['images'] else None
        })
    return pd.DataFrame(songs)

def get_mood_from_features(features):
    """
    Analyze audio features and map to a mood.
    """
    if features:
        if features['valence'] > 0.7 and features['energy'] > 0.6:
            return "Happy"
        elif features['energy'] > 0.7:
            return "Energetic"
        elif features['valence'] < 0.4:
            return "Sad"
        else:
            return "Calm"
    return "Unknown"

# Visualize Insights
def plot_mood_pie_chart(data):
    mood_counts = data['mood'].value_counts()
    plt.figure(figsize=(8, 8))
    plt.pie(mood_counts, labels=mood_counts.index, autopct="%1.1f%%", startangle=140, colors=["#FFD700", "#FF4500", "#1E90FF", "#4B0082"])
    plt.title("Distribution of Moods in Liked Songs", color="white")
    plt.gca().set_facecolor("black")
    st.pyplot(plt)

def display_mood_insights(data):
    st.subheader("🎨 Mood Insights")
    mood_summary = data['mood'].value_counts()
    st.write("Here's a breakdown of your liked songs by mood:")
    for mood, count in mood_summary.items():
        st.markdown(f"- **{mood}:** {count} songs")

    # Visualize as a pie chart
    plot_mood_pie_chart(data)

# Main App Logic
st.title("Moodify 🎵")
st.subheader("Your Mood. Your Music.")
st.markdown("Discover insights about your music and mood.")

# Authentication
if "sp" not in st.session_state:
    st.info("Log in to access your Spotify account.")
    if st.button("Log in with Spotify"):
        authenticate_spotify()
else:
    sp = st.session_state["sp"]
    st.sidebar.button("Logout", on_click=clear_session)

    # Navigation
    page = st.sidebar.radio("Navigate to:", ["🎧 Discover Liked Songs", "📊 Mood Insights"])

    # Discover Liked Songs - Page 1
    if page == "🎧 Discover Liked Songs":
        st.title("🎧 Discover Liked Songs Filtered by Mood")
        mood_filter = st.selectbox("Filter songs by mood:", ["All", "Happy", "Energetic", "Calm", "Sad"])
        
        with st.spinner("Fetching your liked songs..."):
            liked_songs = fetch_liked_songs(sp)

        if not liked_songs.empty:
            filtered_songs = liked_songs if mood_filter == "All" else liked_songs[liked_songs["mood"] == mood_filter]
            for _, song in filtered_songs.iterrows():
                st.markdown(
                    f"""
                    <div class="mood-card">
                        <img src="{song['image']}" width="80" height="80" style="border-radius: 10px; margin-bottom: 10px;">
                        <p><strong>{song['name']}</strong> by {song['artist']}</p>
                        <p>Mood: {song['mood']}</p>
                    </div>
                    """, unsafe_allow_html=True
                )
        else:
            st.warning("No liked songs found. Please add songs to your Spotify library!")

    # Mood Insights - Page 2
    elif page == "📊 Mood Insights":
        st.title("📊 Mood Insights and Visuals")
        with st.spinner("Analyzing your liked songs..."):
            liked_songs = fetch_liked_songs(sp)

        if not liked_songs.empty:
            display_mood_insights(liked_songs)
        else:
            st.warning("No liked songs found for mood insights. Please add songs to your Spotify library!")
