import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import pandas as pd
import datetime
import time  # For handling delays in retries

# Spotify API credentials from Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Define the required scope for Spotify access
scope = "user-library-read user-top-read playlist-read-private"

# Initialize Spotify OAuth object
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=scope,
    cache_path=".cache"  # Optional: Specify a cache path
)

# Set Streamlit page configuration
st.set_page_config(
    page_title="Wvvy",
    page_icon="〰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for white text in the main body and normal text for select elements
st.markdown("""
    <style>
    body {
        background: linear-gradient(to right, black, #1DB954) !important;
    }
    .stApp {
        background: linear-gradient(to right, black, #1DB954) !important;
    }
    .header-title {
        font-size: 5em;
        font-weight: bold;
        color: white !important;
        text-align: center;
        padding-top: 50px;
        margin-bottom: 20px;
        letter-spacing: 5px;
    }
    .login-button {
        color: white;
        background-color: #1DB954;
        padding: 15px 30px;
        font-size: 1.5em;
        border-radius: 12px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-weight: bold;
        margin-top: 30px;
    }
    /* Set white text for markdown and body */
    .stMarkdown p, .stMarkdown h3 {
        color: white !important;
    }
    /* Set text color for select box and slider labels */
    .stSelectbox label, .stSlider label {
        color: white !important;
    }
    /* Set black color for options in selectbox */
    .stSelectbox .css-1wa3eu0-placeholder, .stSelectbox .css-2b097c-container {
        color: white !important;
    }
    /* Set text color for slider numbers */
    .stSlider .css-164nlkn .css-qrbaxs {
        color: white !important;
    }
    /* Adjust background and text color for tabs */
    .stTabs [role="tab"] {
        color: white !important;
    }
    .stTabs [role="tabpanel"] {
        background-color: rgba(0, 0, 0, 0.5) !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# Wvvy logo and title
st.markdown("<div class='header-title'>〰 Wvvy</div>", unsafe_allow_html=True)

# Authentication Functions
def is_authenticated():
    return 'token_info' in st.session_state and st.session_state['token_info'] is not None

def refresh_token():
    if 'token_info' in st.session_state and sp_oauth.is_token_expired(st.session_state['token_info']):
        token_info = sp_oauth.refresh_access_token(st.session_state['token_info']['refresh_token'])
        st.session_state['token_info'] = token_info

def authenticate_user():
    # Correct handling of query params
    query_params = st.query_params  # Updated way to get query parameters
    
    if "code" in query_params:
        code = query_params["code"][0]
        try:
            # Using get_cached_token to avoid future deprecation
            token_info = sp_oauth.get_cached_token()
            if not token_info:
                token_info = sp_oauth.get_access_token(code)
            st.session_state['token_info'] = token_info
            # Use query_params to reset query parameters
            st.query_params.clear()  # Clear query parameters to avoid repeated authentication
            st.success("You're authenticated! Click the button below to enter.")
            if st.button("Enter Wvvy"):
                st.experimental_rerun()  # Reload the app once authenticated
        except Exception as e:
            st.error(f"Authentication error: {e}")
    else:
        auth_url = sp_oauth.get_authorize_url()
        st.markdown(
            f'<a href="{auth_url}" class="login-button">Login with Spotify</a>',
            unsafe_allow_html=True
        )

# Helper Function for Handling Spotify API Rate Limit (429 Error)
def handle_spotify_rate_limit(sp_func, *args, max_retries=10, **kwargs):
    retries = 0
    wait_time = 1  # Start with 1 second wait time
    suppressed_warning = False  # Flag to suppress multiple retry warnings
    while retries < max_retries:
        try:
            return sp_func(*args, **kwargs)
        except spotipy.SpotifyException as e:
            if e.http_status == 429:
                retry_after = int(e.headers.get("Retry-After", wait_time)) if e.headers and "Retry-After" in e.headers else wait_time
                if not suppressed_warning:  # Suppress multiple warnings
                    st.warning(f"Rate limit reached. Retrying after {retry_after} seconds...")
                    suppressed_warning = True
                time.sleep(retry_after)  # Sleep for 'Retry-After' seconds
                retries += 1
                wait_time *= 2  # Double the wait time after each retry (exponential backoff)
            else:
                st.error(f"Error: {e}")
                break
    return None  # Silent return, no more 'Max Retries' messages

# Fetch audio features for a batch of tracks (with 429 handling)
def fetch_audio_features(sp, track_ids):
    audio_features = []
    batch_size = 50  # Fetch in batches of 50 to avoid rate limits
    for i in range(0, len(track_ids), batch_size):
        batch_ids = track_ids[i:i + batch_size]
        features = handle_spotify_rate_limit(sp.audio_features, batch_ids)
        if features:
            audio_features.extend(features)
    return audio_features

# Example function to get liked songs and audio features (with 429 error handling)
def get_liked_songs(sp):
    results = handle_spotify_rate_limit(sp.current_user_saved_tracks, limit=50)
    if not results:
        return []  # Return empty list if retries exceeded
    liked_songs = []
    for item in results['items']:
        track = item['track']
        track_id = track['id']
        audio_features = fetch_audio_features(sp, [track_id])[0]
        liked_songs.append({
            "name": track['name'],
            "artist": track['artists'][0]['name'],
            "cover": track['album']['images'][0]['url'] if track['album']['images'] else None,
            "energy": audio_features["energy"],
            "valence": audio_features["valence"],
            "tempo": audio_features["tempo"]
        })
    return liked_songs

# Retrieve recommendations based on user's listening habits (with 429 error handling)
def get_new_discoveries(sp):
    top_tracks_results = handle_spotify_rate_limit(sp.current_user_top_tracks, limit=5, time_range="medium_term")
    top_artists_results = handle_spotify_rate_limit(sp.current_user_top_artists, limit=5, time_range="medium_term")
    
    if not top_tracks_results or not top_artists_results:
        return []  # Return empty if max retries exceeded
    
    top_tracks = [track['id'] for track in top_tracks_results['items']]
    top_genres = [artist['genres'][0] for artist in top_artists_results['items'] if artist['genres']]

    seed_tracks = top_tracks[:3]
    seed_genres = top_genres[:2]

    if not seed_tracks and not seed_genres:
        seed_tracks = ['4uLU6hMCjMI75M1A2tKUQC']  # Default track seed

    recommendations = handle_spotify_rate_limit(sp.recommendations, seed_tracks=seed_tracks, seed_genres=seed_genres, limit=50)
    
    if not recommendations:
        return []  # Return empty if max retries exceeded
    
    new_songs = []
    for track in recommendations['tracks']:
        audio_features = fetch_audio_features(sp, [track['id']])[0]
        new_songs.append({
            "name": track['name'],
            "artist": track['artists'][0]['name'],
            "cover": track['album']['images'][0]['url'] if track['album']['images'] else None,
            "energy": audio_features["energy"],
            "valence": audio_features["valence"],
            "tempo": audio_features["tempo"]
        })
    return new_songs

# Enhanced mood classification based on valence and tempo
def filter_songs(songs, mood, intensity):
    mood_ranges = {
        "Happy": {"valence": (0.6, 1), "tempo": (100, 200)},
        "Calm": {"valence": (0.3, 0.5), "tempo": (40, 100)},
        "Energetic": {"valence": (0.5, 1), "tempo": (120, 200)},
        "Sad": {"valence": (0, 0.3), "tempo": (40, 80)}
    }
    
    mood_filter = mood_ranges[mood]
    
    # Apply mood and intensity filtering
    filtered_songs = [
        song for song in songs
        if mood_filter["valence"][0] <= song["valence"] <= mood_filter["valence"][1]
        and mood_filter["tempo"][0] <= song["tempo"] <= mood_filter["tempo"][1]
        and song['energy'] >= (intensity / 5)
    ]
    
    return filtered_songs

# Function to display songs with their cover images
def display_songs(song_list, title):
    st.write(f"### {title}")
    if song_list:
        for song in song_list:
            col1, col2 = st.columns([1, 4])
            with col1:
                if song["cover"]:
                    st.image(song["cover"], width=80)
                else:
                    st.write("No cover")
            with col2:
                st.write(f"**{song['name']}** by {song['artist']}")
    else:
        st.write("No songs found.")

# Main app logic
if is_authenticated():
    try:
        st.markdown("""
        <div style='color: white; font-size: 18px; font-weight: bold;'>
            You are logged in! Your Spotify data is ready for analysis.
        </div>
        """, unsafe_allow_html=True)

        sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])
        
        mood = st.selectbox("Choose your mood:", ["Happy", "Calm", "Energetic", "Sad"])
        intensity = st.slider("Choose intensity:", 1, 5, 3)

        tab1, tab2 = st.tabs(["Liked Songs", "New Discoveries"])

        with tab1:
            liked_songs = get_liked_songs(sp)
            if liked_songs:
                filtered_liked_songs = filter_songs(liked_songs, mood, intensity)
                display_songs(filtered_liked_songs, "Your Liked Songs")
            else:
                st.warning("No liked songs available.")

        with tab2:
            new_songs = get_new_discoveries(sp)
            if new_songs:
                filtered_new_songs = filter_songs(new_songs, mood, intensity)
                display_songs(filtered_new_songs, "New Song Discoveries")
            else:
                st.warning("No new discoveries available.")
        
    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to Wvvy")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
