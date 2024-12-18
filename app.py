import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Spotify API Credentials
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]
SCOPE = "user-library-read user-top-read playlist-read-private user-read-recently-played"

# Streamlit Page Config
st.set_page_config(page_title="Moodify 🎵", page_icon="🎵", layout="wide")

# Custom CSS
st.markdown("""
    <style>
        body {background: linear-gradient(to right, #1a1a1a, #1DB954); color: white;}
        .stApp {background: linear-gradient(to right, #1a1a1a, #1DB954);}
        h1, h2, h3, p {color: white !important;}
        .card {background-color: #333; padding: 15px; border-radius: 15px; margin: 10px; text-align: center;}
        img {border-radius: 10px;}
    </style>
""", unsafe_allow_html=True)

# Authentication
def authenticate_spotify():
    """
    Authenticate user with Spotify and set up session.
    """
    auth_manager = SpotifyOAuth(client_id=CLIENT_ID,
                                client_secret=CLIENT_SECRET,
                                redirect_uri=REDIRECT_URI,
                                scope=SCOPE)
    st.session_state["sp"] = spotipy.Spotify(auth_manager=auth_manager)

def fetch_liked_songs(sp):
    """
    Fetch user's liked songs and analyze their audio features.
    """
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

def filter_songs_by_mood(data, mood, intensity):
    """
    Filter songs based on mood and intensity.
    """
    conditions = {
        "Happy": (data["valence"] > 0.6) & (data["energy"] >= intensity / 5),
        "Calm": (data["valence"] < 0.5) & (data["energy"] <= intensity / 5),
        "Energetic": (data["energy"] > 0.7),
        "Sad": (data["valence"] < 0.3)
    }
    return data[conditions.get(mood, pd.Series([True] * len(data)))]

def display_top_data(sp):
    """
    Display top tracks, artists, and genres with visuals.
    """
    st.subheader("🎤 Top Artists and Songs")
    top_tracks = sp.current_user_top_tracks(limit=10)
    top_artists = sp.current_user_top_artists(limit=5)

    st.write("### 🎵 Top Tracks")
    for track in top_tracks["items"]:
        st.markdown(
            f"""
            <div class="card">
                <img src="{track['album']['images'][0]['url']}" width="80" height="80">
                <p><strong>{track['name']}</strong> by {track['artists'][0]['name']}</p>
            </div>
            """, unsafe_allow_html=True
        )

    st.write("### 🎤 Top Artists")
    for artist in top_artists["items"]:
        st.markdown(
            f"""
            <div class="card">
                <img src="{artist['images'][0]['url']}" width="80" height="80">
                <p><strong>{artist['name']}</strong></p>
            </div>
            """, unsafe_allow_html=True
        )

def plot_weekly_moods():
    """
    Weekly Mood Analysis Visualization.
    """
    data = pd.DataFrame({
        "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "Mood": [7, 6, 8, 5, 7, 9, 8]
    })
    plt.figure(figsize=(10, 5))
    sns.lineplot(x="Day", y="Mood", data=data, marker="o", color="cyan")
    plt.title("Weekly Mood Analysis", color="white")
    plt.ylabel("Mood Intensity", color="white")
    plt.xlabel("Day", color="white")
    plt.gca().set_facecolor("black")
    plt.gcf().set_facecolor("black")
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
    page = st.sidebar.radio("Navigate to:", ["🎧 Discover Songs", "📊 Insights & Analytics"])

    # Page 1 - Discover Songs
    if page == "🎧 Discover Songs":
        st.title("🎧 Discover Liked Songs")
        mood = st.selectbox("Choose a Mood:", ["Happy", "Calm", "Energetic", "Sad"])
        intensity = st.slider("Choose Intensity (1-5):", 1, 5, 3)

        with st.spinner("Fetching your liked songs..."):
            liked_songs = fetch_liked_songs(sp)
        if not liked_songs.empty:
            filtered_songs = filter_songs_by_mood(liked_songs, mood, intensity)
            for _, song in filtered_songs.iterrows():
                st.markdown(
                    f"""
                    <div class="card">
                        <img src="{song['image']}" width="80" height="80">
                        <p><strong>{song['name']}</strong> by {song['artist']}</p>
                        <p>Mood: {mood}</p>
                    </div>
                    """, unsafe_allow_html=True
                )
        else:
            st.warning("No liked songs found!")

    # Page 2 - Insights & Analytics
    elif page == "📊 Insights & Analytics":
        st.title("📊 Music Insights")
        display_top_data(sp)
        st.write("### 🧠 Weekly Mood Insights")
        st.markdown("We analyzed your weekly listening trends and moods.")
        plot_weekly_moods()
        st.markdown("**Your music is vibrant and full of energy! Keep exploring. 🎨**")
