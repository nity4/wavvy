import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time

CLIENT_ID = 'your_client_id'
CLIENT_SECRET = 'your_client_secret'
REDIRECT_URI = 'https://wvvy701.streamlit.app/'

scope = "user-library-read user-top-read"

sp_oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=scope)

auth_url = sp_oauth.get_authorize_url()
print(f"Navigate to this URL to authenticate: {auth_url}")

# App Layout and Configuration
st.set_page_config(page_title="Wvvy", page_icon="〰", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
    <style>
    .main {
        background-color: #f4f4f4;
        font-family: 'Courier New', Courier, monospace;
    }
    .stApp {
        background-image: linear-gradient(to right, #ff4081, #ff6347);
    }
    .header-title {
        font-size: 3em;
        color: white;
        font-weight: bold;
        text-align: center;
    }
    .loading-text {
        font-size: 1.5em;
        color: white;
        text-align: center;
        padding: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='header-title'>〰 Wvvy</div>", unsafe_allow_html=True)

# Authentication Functions
def is_authenticated():
    return st.session_state.get('token_info') is not None

def refresh_token():
    if 'token_info' in st.session_state and sp_oauth.is_token_expired(st.session_state['token_info']):
        token_info = sp_oauth.refresh_access_token(st.session_state['token_info']['refresh_token'])
        st.session_state['token_info'] = token_info

def authenticate_user():
    try:
        if "code" in st.experimental_get_query_params():
            code = st.experimental_get_query_params()["code"][0]
            token_info = sp_oauth.get_access_token(code)
            st.session_state['token_info'] = token_info
            st.experimental_set_query_params(code=None)
            st.success("You're in! Refresh the page to access your music data.")
            if st.button("Refresh Now"):
                st.experimental_set_query_params()
        else:
            auth_url = sp_oauth.get_authorize_url()
            st.markdown(f'<a href="{auth_url}" target="_self" style="color: white; background-color: #ff4081; padding: 10px; border-radius: 8px;">Login with Spotify</a>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Authentication error: {e}")

# Loading Animation
def show_loading_animation(text="Loading..."):
    st.markdown(f"<div class='loading-text'>{text}</div>", unsafe_allow_html=True)
    with st.spinner("Processing..."):
        time.sleep(2)  # Simulating a loading process

# Helper Functions
def get_all_liked_songs(sp):
    liked_songs = []
    try:
        results = sp.current_user_saved_tracks(limit=50, offset=0)
        total_songs = results['total']

        while len(liked_songs) < total_songs:
            liked_songs.extend(results['items'])
            offset = len(liked_songs)
            results = sp.current_user_saved_tracks(limit=50, offset=offset)

    except Exception as e:
        st.error(f"Error fetching liked songs: {e}")
    
    return liked_songs

# Fetch Audio Features in Batches (Spotify API has a limit on batch size)
def fetch_audio_features_in_batches(sp, song_ids):
    features = []
    try:
        batch_size = 100  # Spotify's limit for batch requests
        for i in range(0, len(song_ids), batch_size):
            batch = song_ids[i:i + batch_size]
            audio_features = sp.audio_features(tracks=batch)
            features.extend(audio_features)
    except Exception as e:
        st.error(f"Error fetching audio features: {e}")
    
    return features

# Filter Liked Songs by Mood
def filter_liked_songs_by_mood(track_features, feeling, intensity):
    filtered_songs = []
    fallback_songs = []

    for track in track_features:
        valence = track.get('valence', 0)
        energy = track.get('energy', 0)
        danceability = track.get('danceability', 0)
        tempo = track.get('tempo', 0)

        score = 0  # Base score for filtering
        
        # Apply mood-based logic
        if feeling == "Happy":
            score += (valence - 0.6) * 10 + (energy - intensity / 5) * 5
        elif feeling == "Sad":
            score += (0.3 - valence) * 10 + (energy - 0.4) * 5
        elif feeling == "Chill":
            score += (0.4 - energy) * 7 + (danceability - 0.4) * 5
        elif feeling == "Hype":
            score += (energy - 0.7) * 12 + (tempo - 120) * 0.1
        elif feeling == "Romantic":
            score += (valence - 0.5) * 5 + (danceability - 0.4) * 5
        elif feeling == "Adventurous":
            score += danceability * 5 + (tempo - 120) * 0.1

        # Choose tracks with a score above the intensity threshold
        if score > intensity * 1.2:
            filtered_songs.append(track)
        elif score > intensity * 0.8:
            fallback_songs.append(track)

    # If no strongly matching songs, return fallback songs
    return filtered_songs if filtered_songs else fallback_songs

# Function for Mood-Based Music Discovery
def discover_music_by_feelings(sp):
    st.header("Curate Your Vibe")
    feeling = st.selectbox("What's your vibe today?", ["Happy", "Sad", "Chill", "Hype", "Romantic", "Adventurous"])
    intensity = st.slider(f"How {feeling} are you feeling?", 1, 5)

    try:
        liked_songs = get_all_liked_songs(sp)
        if len(liked_songs) > 0:
            show_loading_animation(text="Creating your vibe-based playlist...")
            random.shuffle(liked_songs)
            song_ids = [track['track']['id'] for track in liked_songs]
            features = fetch_audio_features_in_batches(sp, song_ids)
            filtered_songs = filter_liked_songs_by_mood(features, feeling, intensity)
        else:
            filtered_songs = []

        if filtered_songs:
            st.subheader(f"Here's your {feeling.lower()} playlist:")
            for i, feature in enumerate(filtered_songs[:10]):
                song = sp.track(feature['id'])
                song_name = song['name']
                artist_name = song['artists'][0]['name']
                album_cover = song['album']['images'][0]['url']
                st.image(album_cover, width=150, caption=f"{song_name} by {artist_name}")
        else:
            st.write(f"No tracks match your {feeling.lower()} vibe right now. Try tweaking the intensity or picking a different mood.")
    
    except Exception as e:
        st.error(f"Error curating your playlist: {e}")

# Unique Insights Based on Data
def get_top_items_with_insights(sp):
    st.header("Your Top Songs, Artists, and Genres")
    time_range = st.radio("Select time range", ['This Week', 'This Month', 'This Year'], index=1)

    time_range_map = {'This Week': 'short_term', 'This Month': 'medium_term', 'This Year': 'long_term'}
    spotify_time_range = time_range_map[time_range]

    show_loading_animation(text="Fetching your top tracks and insights...")
    top_tracks = sp.current_user_top_tracks(time_range=spotify_time_range, limit=10)
    top_artists = sp.current_user_top_artists(time_range=spotify_time_range, limit=5)
    top_genres = [genre for artist in top_artists['items'] for genre in artist['genres'] if 'genres' in artist]

    st.subheader("Your Top Songs")
    for i, track in enumerate(top_tracks['items']):
        st.write(f"{i+1}. {track['name']} by {track['artists'][0]['name']}")
        st.image(track['album']['images'][0]['url'], width=60)

    st.subheader("Your Top Artists")
    for i, artist in enumerate(top_artists['items']):
        st.write(f"{i+1}. {artist['name']}")
        st.image(artist['images'][0]['url'], width=60)

    st.subheader("Your Top 5 Genres")
    top_5_genres = pd.Series(top_genres).value_counts().head(5).index.tolist()
    st.write(", ".join(top_5_genres))

# Main App Layout
if is_authenticated():
    try:
        refresh_token()
        sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

        # Reorganizing the Page Flow
        page = st.sidebar.radio("Navigation", [
            "Wavvy", 
            "Your Top Hits", 
            "Music Personality"
        ])

        if page == "Wavvy":
            discover_music_by_feelings(sp)
        elif page == "Your Top Hits":
            get_top_items_with_insights(sp)
        # Define the Music Personality page if needed

    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to Wvvy")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
