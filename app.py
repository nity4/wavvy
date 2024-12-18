import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- Spotify API Credentials ---
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]
SCOPE = "user-library-read user-top-read playlist-read-private user-read-recently-played"

# --- Streamlit Page Config ---
st.set_page_config(page_title="MusoMood 🎼", page_icon="🎼", layout="wide")

# --- Custom CSS ---
st.markdown("""
    <style>
        body {background: linear-gradient(to right, #1a1a1a, #1DB954);}
        .stApp {background: linear-gradient(to right, #1a1a1a, #1DB954);}
        h1, h2, h3, p {color: white;}
        .card {
            background-color: #333;
            padding: 15px;
            border-radius: 10px;
            margin: 10px;
            text-align: center;
            color: white;
        }
        img {border-radius: 10px; margin-bottom: 10px;}
    </style>
""", unsafe_allow_html=True)

# --- Spotify Authentication ---
def authenticate_spotify():
    """
    Authenticate with Spotify and store the Spotify client in session state.
    """
    if "sp" not in st.session_state:
        auth_manager = SpotifyOAuth(client_id=CLIENT_ID,
                                    client_secret=CLIENT_SECRET,
                                    redirect_uri=REDIRECT_URI,
                                    scope=SCOPE)
        st.session_state["sp"] = spotipy.Spotify(auth_manager=auth_manager)

# --- Fetch Data ---
def fetch_liked_songs(sp):
    """
    Fetch user's liked songs and analyze audio features.
    """
    results = sp.current_user_saved_tracks(limit=50)
    songs = []
    for item in results['items']:
        track = item['track']
        features = sp.audio_features(track['id'])[0]
        songs.append({
            "name": track['name'],
            "artist": ", ".join(artist['name'] for artist in track['artists']),
            "image": track['album']['images'][0]['url'],
            "valence": features['valence'],
            "energy": features['energy'],
            "danceability": features['danceability']
        })
    return pd.DataFrame(songs)

def fetch_recently_played(sp):
    """
    Fetch user's recently played tracks and analyze audio features.
    """
    results = sp.current_user_recently_played(limit=50)
    songs = []
    for item in results['items']:
        track = item['track']
        features = sp.audio_features(track['id'])[0]
        songs.append({
            "name": track['name'],
            "artist": ", ".join(artist['name'] for artist in track['artists']),
            "image": track['album']['images'][0]['url'],
            "played_at": item['played_at'],
            "valence": features['valence'],
            "energy": features['energy']
        })
    return pd.DataFrame(songs)

# --- Filter Songs by Mood and Intensity ---
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
    filtered = data[conditions.get(mood, pd.Series([True] * len(data)))]
    return filtered

# --- Display Filtered Songs ---
def display_filtered_songs(data, mood):
    st.subheader(f"🎵 Songs Filtered for Mood: {mood}")
    for _, song in data.iterrows():
        st.markdown(
            f"""
            <div class="card">
                <img src="{song['image']}" width="150" height="150">
                <p><strong>{song['name']}</strong></p>
                <p>by {song['artist']}</p>
                <p>Valence: {song['valence']:.2f} | Energy: {song['energy']:.2f}</p>
            </div>
            """, unsafe_allow_html=True
        )

# --- Main App ---
st.title("MusoMood 🎼")
st.subheader("Discover Your Music. Explore Your Moods.")

authenticate_spotify()
sp = st.session_state["sp"]

# --- Fetch Data ---
st.write("Fetching your liked songs and recently played tracks...")
liked_songs = fetch_liked_songs(sp)
recently_played = fetch_recently_played(sp)

# --- Mood and Intensity Input ---
st.sidebar.subheader("🎚️ Mood and Intensity Filter")
selected_data = st.sidebar.radio("Select Data Source:", ["Liked Songs", "Recently Played"])
selected_mood = st.sidebar.selectbox("Choose a Mood:", ["Happy", "Calm", "Energetic", "Sad"])
selected_intensity = st.sidebar.slider("Select Intensity (1-5):", 1, 5, 3)

# Filter Songs
data = liked_songs if selected_data == "Liked Songs" else recently_played
filtered_songs = filter_songs_by_mood(data, selected_mood, selected_intensity)

# Display Filtered Songs
if not filtered_songs.empty:
    display_filtered_songs(filtered_songs, selected_mood)
else:
    st.warning(f"No songs found for mood: {selected_mood} with intensity level {selected_intensity}.")
