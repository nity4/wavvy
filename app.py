import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random

# Spotify API credentials from Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Define the required scope for Spotify access
scope = "user-library-read user-top-read playlist-read-private user-read-recently-played"

# Initialize Spotify OAuth object
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=scope,
    cache_path=".cache"
)

# Set Streamlit page configuration
st.set_page_config(
    page_title="Wvvy",
    page_icon="〰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
    <style>
    * {
        color: white !important;
    }
    body {
        background: linear-gradient(to right, black, #1DB954) !important;
    }
    .stApp {
        background: linear-gradient(to right, black, #1DB954) !important;
    }
    .header-title {
        font-size: 5em;
        font-weight: bold;
        text-align: center;
        padding-top: 50px;
        margin-bottom: 20px;
        letter-spacing: 5px;
        color: white !important;
    }
    .login-button {
        color: white;
        background-color: #1DB954;
        padding: 15px 30px;
        font-size: 1.5em;
        border-radius: 12px;
        text-align: center;
        display: inline-block;
        font-weight: bold;
        margin-top: 30px;
    }
    .insight-box {
        background-color: #333;
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    select, .stSlider label, .stRadio label, .stButton button {
        color: black !important;  /* Black filters */
    }
    </style>
""", unsafe_allow_html=True)

# Wvvy logo and title
st.markdown("<div class='header-title'>〰 Wvvy</div>", unsafe_allow_html=True)

# Function to refresh the token if expired
def refresh_token():
    token_info = st.session_state.get('token_info', None)
    if token_info and sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        st.session_state['token_info'] = token_info

# Function to check if the user is authenticated
def is_authenticated():
    if 'token_info' in st.session_state and st.session_state['token_info']:
        refresh_token()  # Ensure token is refreshed before using it
        return True
    return False

# Authentication flow
def authenticate_user():
    query_params = st.experimental_get_query_params()

    if "code" in query_params:
        code = query_params["code"][0]
        try:
            token_info = sp_oauth.get_cached_token()
            if not token_info:
                token_info = sp_oauth.get_access_token(code)
            st.session_state['token_info'] = token_info
            st.experimental_set_query_params()
            st.success("You're authenticated! Click the button below to enter.")
            if st.button("Enter Wvvy"):
                st.experimental_rerun()
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
    wait_time = 1
    while retries < max_retries:
        try:
            return sp_func(*args, **kwargs)
        except spotipy.SpotifyException as e:
            if e.http_status == 429:
                retry_after = int(e.headers.get("Retry-After", wait_time)) if e.headers and "Retry-After" in e.headers else wait_time
                st.warning(f"Rate limit reached. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                retries += 1
                wait_time *= 2
            else:
                st.error(f"Error: {e}")
                break
    return None

# Fetch liked songs and audio features
def get_liked_songs(sp):
    results = handle_spotify_rate_limit(sp.current_user_saved_tracks, limit=50)
    if not results:
        return []  # Return empty list if retries exceeded
    liked_songs = []
    for item in results['items']:
        track = item['track']
        audio_features = handle_spotify_rate_limit(sp.audio_features, [track['id']])[0]
        liked_songs.append({
            "name": track['name'],
            "artist": track['artists'][0]['name'],
            "cover": track['album']['images'][0]['url'] if track['album']['images'] else None,
            "energy": audio_features["energy"],
            "valence": audio_features["valence"],
            "tempo": audio_features["tempo"],
            "popularity": track['popularity']
        })
    random.shuffle(liked_songs)  # Shuffle the liked songs before displaying
    return liked_songs

# Function to display songs with their cover images (cover left, name right)
def display_songs_with_cover(song_list, title):
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

# Function to fetch top items for insights
def get_top_items(sp, item_type='tracks', time_range='short_term', limit=10):
    if item_type == 'tracks':
        results = handle_spotify_rate_limit(sp.current_user_top_tracks, time_range=time_range, limit=limit)
    elif item_type == 'artists':
        results = handle_spotify_rate_limit(sp.current_user_top_artists, time_range=time_range, limit=limit)
    items = []
    for item in results['items']:
        if item_type == 'tracks':
            items.append({
                'id': item['id'],  # Track ID for recommendations
                'name': item['name'],
                'artist': item['artists'][0]['name'],
                'popularity': item.get('popularity', 0),
                'cover': item['album']['images'][0]['url'] if item['album']['images'] else None,
                'tempo': item.get('tempo', 120)
            })
        elif item_type == 'artists':
            items.append({
                'name': item['name'],
                'genres': item.get('genres', ['Unknown Genre']),
                'cover': item['images'][0]['url'] if item['images'] else None
            })
    return items

# Function to get albums and suggest undiscovered songs based on user’s history
def undiscovered_songs_in_top_albums(sp):
    st.write("### 🎧 Undiscovered Songs in Top Albums")
    
    top_albums = handle_spotify_rate_limit(sp.current_user_top_tracks, limit=10)
    if not top_albums:
        st.write("No top albums found.")
        return

    for album in top_albums['items']:
        album_name = album['album']['name']
        album_tracks = handle_spotify_rate_limit(sp.album_tracks, album['album']['id'])
        
        undiscovered_songs = []
        for track in album_tracks['items']:
            track_played = handle_spotify_rate_limit(sp.current_user_recently_played, limit=50)  # Fetch user's recently played songs
            played_track_ids = [item['track']['id'] for item in track_played['items']]  # Get list of played track IDs

            if track['id'] not in played_track_ids:  # If the track hasn't been played
                undiscovered_songs.append(track['name'])
        
        if undiscovered_songs:
            st.write(f"**{album_name}**")
            st.write(", ".join(undiscovered_songs))

# Display top songs and artists insights (cover left, name right)
def display_top_insights_with_emojis(sp, time_range='short_term'):
    top_tracks = get_top_items(sp, item_type='tracks', time_range=time_range)
    top_artists = get_top_items(sp, item_type='artists', time_range=time_range)

    display_songs_with_cover(top_tracks, "🎵 Top Songs")
    display_songs_with_cover(top_artists, "🎤 Top Artists")

    st.write("### Fascinating Insights 💡")
    if top_tracks:
        avg_popularity = round(sum(track['popularity'] for track in top_tracks) / len(top_tracks), 1) if top_tracks else 0
        avg_tempo = round(sum(track.get('tempo', 120) for track in top_tracks) / len(top_tracks), 1)
        hidden_gems = [track for track in top_tracks if track['popularity'] < 50]

        st.markdown(f"<div class='insight-box'>🌟 <strong>Average Popularity of Top Songs:</strong> {avg_popularity}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='insight-box'>🎶 <strong>Average Tempo of Top Songs:</strong> {avg_tempo} BPM</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='insight-box'>💎 <strong>Hidden Gems (Less Popular Tracks):</strong> {len(hidden_gems)} discovered</div>", unsafe_allow_html=True)

# Fetch weekly listening data and create a weekly-based personality profile
def display_music_personality(sp):
    st.write("### Your Weekly Music Personality Profile")

    weekly_tracks, weekly_minutes = fetch_recently_played(sp, time_range='short_term')

    # Fetch listening patterns based on past week's listening habits
    display_weekly_listening_patterns(sp)

    st.markdown(f"""
    <div class="personality-card">
        <h2>Weekly Listening Stats</h2>
        <p><strong>Total Tracks This Week:</strong> {weekly_tracks}</p>
        <p><strong>Total Minutes Listened This Week:</strong> {weekly_minutes} minutes</p>
    </div>
    """, unsafe_allow_html=True)

# Analyze weekly listening patterns and show peak timing
def display_weekly_listening_patterns(sp):
    results = handle_spotify_rate_limit(sp.current_user_recently_played, limit=50)
    if not results:
        return None
    
    hours = [pd.to_datetime(item['played_at']).hour for item in results['items']]
    hour_df = pd.DataFrame(hours, columns=["Hour"])
    
    # Plot the graph for the past week
    fig, ax = plt.subplots(figsize=(5, 2))
    hour_df["Hour"].value_counts().sort_index().plot(kind='line', marker='o', ax=ax, color='#FF5733', linewidth=1.5)
    
    ax.set_title("Weekly Listening Patterns", color="white")
    ax.set_xlabel("Hour of Day", color="white")
    ax.set_ylabel("Number of Tracks", color="white")
    ax.spines['bottom'].set_color('white')
    ax.spines['top'].set_color('white')
    ax.spines['right'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    st.pyplot(fig)

    peak_hour = hour_df["Hour"].mode()[0]
    st.markdown(f"<div class='insight-box'>Your peak listening hour this week is {peak_hour}:00.</div>", unsafe_allow_html=True)

# Fetch recent listening data for a specific time range (week-based)
def fetch_recently_played(sp, time_range='short_term'):
    results = handle_spotify_rate_limit(sp.current_user_recently_played, limit=50)
    if not results:
        return 0, 0
    total_songs = len(results['items'])
    total_minutes = sum([item['track']['duration_ms'] for item in results['items']]) / (1000 * 60)  # Convert ms to minutes
    return total_songs, total_minutes

# Main app logic
if is_authenticated():
    sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

    tab1, tab2, tab3, tab4 = st.tabs([
        "Liked Songs & New Discoveries", 
        "Top Songs, Artists & Genres", 
        "Top Albums", 
        "Your Music Personality"
    ])

    with tab1:
        option = st.radio("Choose Option:", ["Liked Songs", "Discover New Songs"])
        mood = st.selectbox("Choose your mood:", ["Happy", "Calm", "Energetic", "Sad"])
        intensity = st.slider("Choose intensity:", 1, 5, 3)

        if option == "Liked Songs":
            liked_songs = get_liked_songs(sp)
            filtered_liked_songs = [song for song in liked_songs if song['energy'] > 0.5]
            display_songs_with_cover(filtered_liked_songs, "Your Liked Songs")
        elif option == "Discover New Songs":
            discover_new_songs(sp, mood, intensity)

    with tab2:
        time_filter = st.selectbox("Select Time Period:", ["This Week", "This Month", "This Year"])
        time_mapping = {'This Week': 'short_term', 'This Month': 'medium_term', 'This Year': 'long_term'}
        display_top_insights_with_emojis(sp, time_range=time_mapping[time_filter])

    with tab3:
        undiscovered_songs_in_top_albums(sp)  # Display undiscovered songs from top albums

    with tab4:
        display_music_personality(sp)
    
else:
    st.write("Welcome to Wvvy")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
