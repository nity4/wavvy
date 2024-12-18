import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# --- Spotify API Credentials ---
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]
SCOPE = "user-library-read user-top-read playlist-read-private user-read-recently-played"

# --- Streamlit Page Config ---
st.set_page_config(page_title="MusoMood - Music Meets Mood", page_icon="🎼", layout="wide")

# --- Custom CSS ---
st.markdown("""
    <style>
        body {background: linear-gradient(to right, #1a1a1a, #1DB954);}
        .stApp {background: linear-gradient(to right, #1a1a1a, #1DB954);}
        h1, h2, h3, p {color: white;}
        .card {background-color: #333; padding: 15px; border-radius: 10px; margin: 10px;}
    </style>
""", unsafe_allow_html=True)

# --- Spotify Authentication ---
def authenticate_spotify():
    if "sp" not in st.session_state:
        auth_manager = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                                    redirect_uri=REDIRECT_URI, scope=SCOPE)
        st.session_state["sp"] = spotipy.Spotify(auth_manager=auth_manager)

# --- Fetch Data ---
def fetch_liked_songs(sp):
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
    results = sp.current_user_recently_played(limit=50)
    songs = []
    for item in results['items']:
        track = item['track']
        features = sp.audio_features(track['id'])[0]
        songs.append({
            "name": track['name'],
            "artist": ", ".join(artist['name'] for artist in track['artists']),
            "played_at": item['played_at'],
            "valence": features['valence'],
            "energy": features['energy'],
            "danceability": features['danceability']
        })
    return pd.DataFrame(songs)

# --- Mood Analysis ---
def analyze_mood(data):
    st.subheader("Mood Analysis")
    mood_bins = {
        "Happy": (data['valence'] > 0.6) & (data['energy'] > 0.6),
        "Calm": (data['valence'] < 0.5) & (data['energy'] < 0.5),
        "Energetic": (data['energy'] > 0.7),
        "Sad": (data['valence'] < 0.3)
    }
    data['mood'] = 'Neutral'
    for mood, condition in mood_bins.items():
        data.loc[condition, 'mood'] = mood
    
    mood_count = data['mood'].value_counts()
    fig, ax = plt.subplots(figsize=(8, 5))
    mood_count.plot(kind='bar', color=["#FFD700", "#FF4500", "#1E90FF", "#4B0082"], ax=ax)
    plt.title("Mood Distribution of Your Songs", color="white")
    plt.xticks(color="white")
    plt.yticks(color="white")
    st.pyplot(fig)

    st.write(data.groupby('mood')[['valence', 'energy']].mean())

# --- Scatter Plot ---
def scatter_energy_valence(data):
    st.subheader("Energy vs Valence")
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.scatterplot(x='valence', y='energy', hue='mood', data=data, palette='deep', ax=ax)
    plt.title("Energy vs Valence Analysis", color="white")
    plt.xlabel("Valence (Happiness)", color="white")
    plt.ylabel("Energy", color="white")
    plt.xticks(color="white")
    plt.yticks(color="white")
    st.pyplot(fig)

# --- Main App ---
st.title("MusoMood")
st.markdown("**Discover Your Music. Understand Your Mood.**")

authenticate_spotify()
sp = st.session_state["sp"]

page = st.sidebar.radio("Navigate to:", ["Liked Songs", "Recently Played", "Insights & Stats"])

if page == "Liked Songs":
    st.subheader("Your Liked Songs")
    with st.spinner("Fetching your liked songs..."):
        liked_songs = fetch_liked_songs(sp)
    st.write(liked_songs[['name', 'artist']])
    analyze_mood(liked_songs)
    scatter_energy_valence(liked_songs)

elif page == "Recently Played":
    st.subheader("Your Recently Played Songs")
    with st.spinner("Fetching recently played songs..."):
        recent_songs = fetch_recently_played(sp)
    st.write(recent_songs[['name', 'artist', 'played_at']])
    analyze_mood(recent_songs)
    scatter_energy_valence(recent_songs)

elif page == "Insights & Stats":
    st.subheader("Insights & Analytics")
    st.write("We analyze your listening patterns, moods, and habits.")
    st.markdown("""
    - **Your most energetic songs reflect your vibrant personality.**  
    - **Calm songs suggest moments of peace and relaxation.**  
    - **Listening habits describe you as a dynamic and exploratory listener.**  
    """)
