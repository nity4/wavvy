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

# Initialize Spotify OAuth object (used for user-specific authentication)
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=scope,
    cache_path=None  # Remove cache file to ensure user-specific sessions
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
    .genre-text {
        font-size: 1.3em;
        font-weight: bold;
        color: #1DB954;
        margin-bottom: 10px;
        transition: color 0.2s;
    }
    .genre-text:hover {
        color: #66FF99;
    }
    select, .stSlider label, .stRadio label, .stButton button {
        color: black !important;
    }
    </style>
""", unsafe_allow_html=True)

# Wvvy logo and title
st.markdown("<div class='header-title'>〰 Wvvy</div>", unsafe_allow_html=True)

# Function to refresh the token if expired
def refresh_token():
    token_info = st.session_state.get('token_info', None)
    if token_info and sp_oauth.is_token_expired(token_info):
        try:
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            st.session_state['token_info'] = token_info
        except Exception as e:
            st.error(f"Error refreshing token: {e}")
            st.session_state.pop('token_info', None)  # Remove invalid token

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
            # Generate a token for the specific user
            token_info = sp_oauth.get_cached_token()
            if not token_info:
                token_info = sp_oauth.get_access_token(code)
            # Store the user's unique token in session_state
            st.session_state['token_info'] = token_info
            st.experimental_set_query_params()  # Clear the query params after authentication
            st.success("You're authenticated! Click the button below to enter.")
            if st.button("Enter Wvvy"):
                st.experimental_rerun()
        except Exception as e:
            st.error(f"Authentication error: {e}")
    else:
        # Generate the authentication URL for each user
        auth_url = sp_oauth.get_authorize_url()
        st.markdown(
            f'<a href="{auth_url}" class="login-button">Login with Spotify</a>',
            unsafe_allow_html=True
        )

# Helper Function for Handling Spotify API Rate Limit (429 Error) and Timeout
def handle_spotify_rate_limit(sp_func, *args, max_retries=10, silent=True, **kwargs):
    retries = 0
    wait_time = 1
    while retries < max_retries:
        try:
            return sp_func(*args, **kwargs)
        except (spotipy.SpotifyException, ReadTimeout) as e:
            if isinstance(e, spotipy.SpotifyException) and e.http_status == 429:
                retry_after = int(e.headers.get("Retry-After", wait_time)) if e.headers and "Retry-After" in e.headers else wait_time
                if not silent:
                    st.warning(f"Rate limit reached. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
            elif isinstance(e, ReadTimeout):
                if not silent:
                    st.warning(f"Request timed out. Retrying... ({retries + 1}/{max_retries})")
            else:
                if not silent:
                    st.error(f"Error: {e}")
                break
            retries += 1
            wait_time *= 2  # Exponential backoff
    return None

# Function to fetch all liked songs for the authenticated user
def get_all_liked_songs(sp):
    liked_songs = []
    offset = 0
    while True:
        results = handle_spotify_rate_limit(sp.current_user_saved_tracks, limit=50, offset=offset)
        if not results or not results['items']:
            break
        for item in results['items']:
            track = item['track']
            audio_features = handle_spotify_rate_limit(sp.audio_features, [track['id']])[0]
            liked_songs.append({
                "id": track.get('id', None),
                "name": track.get('name', "Unknown Track"),
                "artist": track['artists'][0]['name'] if 'artists' in track and track['artists'] else "Unknown Artist",
                "cover": track['album']['images'][0]['url'] if 'album' in track and track['album']['images'] else None,
                "energy": audio_features.get("energy", 0.5),
                "valence": audio_features.get("valence", 0.5),
                "tempo": audio_features.get("tempo", 120),
                "popularity": track.get('popularity', 0)
            })
        offset += 50  # Move to the next set of tracks
    return liked_songs

# Function to fetch top items (tracks or artists) for the authenticated user
def get_all_top_items(sp, item_type='tracks', time_range='short_term'):
    top_items = []
    offset = 0
    while True:
        if item_type == 'tracks':
            results = handle_spotify_rate_limit(sp.current_user_top_tracks, time_range=time_range, limit=50, offset=offset)
        elif item_type == 'artists':
            results = handle_spotify_rate_limit(sp.current_user_top_artists, time_range=time_range, limit=50, offset=offset)
        
        if not results or not results['items']:
            break
        for item in results['items']:
            if item_type == 'tracks':
                top_items.append({
                    'id': item.get('id', None),
                    'name': item.get('name', "Unknown Track"),
                    'artist': item['artists'][0]['name'] if 'artists' in item and item['artists'] else "Unknown Artist",
                    'popularity': item.get('popularity', 0),
                    'cover': item['album']['images'][0]['url'] if 'album' in item and item['album']['images'] else None,
                    'tempo': item.get('tempo', 120)
                })
            elif item_type == 'artists':
                top_items.append({
                    'name': item.get('name', "Unknown Artist"),
                    'genres': item.get('genres', ['Unknown Genre']),
                    'cover': item['images'][0]['url'] if 'images' in item and item['images'] else None
                })
        offset += 50  # Move to the next set of items
    return top_items

# Function to display songs with their cover images
def display_songs_with_cover(song_list, title):
    st.write(f"### {title}")
    if song_list:
        for song in song_list:
            col1, col2 = st.columns([1, 4])
            with col1:
                if song.get("cover"):
                    st.image(song["cover"], width=80)
                else:
                    st.write("No cover")
            with col2:
                song_name = song.get("name", "Unknown Song")
                artist_name = song.get("artist", "Unknown Artist")
                st.write(f"**{song_name}** by {artist_name}")
    else:
        st.write("No songs found.")

# Function to discover new songs based on mood and intensity
def discover_new_songs(sp, mood, intensity):
    top_tracks = get_all_top_items(sp, item_type='tracks', time_range='short_term')
    
    # Define mood and intensity mapping
    mood_valence_map = {"Happy": 0.8, "Calm": 0.3, "Energetic": 0.7, "Sad": 0.2}
    mood_energy_map = {"Happy": 0.7, "Calm": 0.4, "Energetic": 0.9, "Sad": 0.3}
    
    valence_target = mood_valence_map.get(mood, 0.5) * intensity / 5
    energy_target = mood_energy_map.get(mood, 0.5) * intensity / 5

    seed_tracks = [track['id'] for track in top_tracks if track.get('id')]

    if seed_tracks:
        # Shuffle and use only up to 5 seed tracks
        random.shuffle(seed_tracks)
        seed_tracks = seed_tracks[:5]

        try:
            recommendations = handle_spotify_rate_limit(
                sp.recommendations,
                seed_tracks=seed_tracks,
                limit=10,
                target_energy=energy_target,
                target_valence=valence_target
            )
            
            # Check if recommendations were successful
            if recommendations and 'tracks' in recommendations:
                new_songs = []
                for rec in recommendations['tracks']:
                    new_songs.append({
                        "name": rec.get('name', "Unknown Track"),
                        "artist": rec['artists'][0]['name'] if 'artists' in rec and rec['artists'] else "Unknown Artist",
                        "cover": rec['album']['images'][0]['url'] if 'album' in rec and rec['album']['images'] else None
                    })

                display_songs_with_cover(new_songs, "New Songs Based on Your Mood")
            else:
                st.write("No recommendations found based on your mood.")
        except Exception as e:
            st.error(f"Error fetching recommendations: {e}")
    else:
        st.write("Not enough data to recommend new songs.")

# Display top songs, artists, and genres with some styling
def display_top_insights_with_genres(sp, time_range='short_term'):
    top_tracks = get_all_top_items(sp, item_type='tracks', time_range=time_range)
    top_artists = get_all_top_items(sp, item_type='artists', time_range=time_range)

    display_songs_with_cover(top_tracks, "Top Songs")
    display_songs_with_cover(top_artists, "Top Artists")

    # Display top genres as styled text
    top_genres = [artist['genres'][0] for artist in top_artists if 'genres' in artist and artist['genres']]
    if top_genres:
        st.write("### Top Genres")
        genre_counts = pd.Series(top_genres).value_counts().index.tolist()

        # Display genres in an interesting format
        genre_text = ", ".join(genre_counts)
        st.markdown(f"<div class='genre-text'>{genre_text}</div>", unsafe_allow_html=True)

    # Fascinating insights based on the user's top songs
    if top_tracks:
        avg_popularity = round(sum(track['popularity'] for track in top_tracks) / len(top_tracks), 1) if top_tracks else 0
        avg_tempo = round(sum(track.get('tempo', 120) for track in top_tracks) / len(top_tracks), 1)
        hidden_gems = [track for track in top_tracks if track['popularity'] < 50]

        # Display insights in well-formatted boxes
        st.write("### Fascinating Insights")
        st.markdown(f"<div class='insight-box'><strong>Average Popularity of Top Songs:</strong> {avg_popularity}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='insight-box'><strong>Average Tempo of Top Songs:</strong> {avg_tempo} BPM</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='insight-box'><strong>Hidden Gems (Less Popular Tracks):</strong> {len(hidden_gems)} discovered</div>", unsafe_allow_html=True)

# Fetch and display weekly personality profile
def display_music_personality(sp):
    st.write("### Your Music Personality Profile")

    weekly_tracks, weekly_minutes = fetch_recently_played(sp, time_range='short_term')
    personality, color, description = analyze_listening_behavior(sp)

    st.markdown(f"""
    <div class="personality-card">
        <h2>Personality Summary</h2>
        <p><strong>Personality Name:</strong> {personality}</p>
        <div class="personality-color-box" style="background-color: {color}; width: 40px; height: 40px; border-radius: 50%; display: inline-block; margin-right: 10px;"></div>
        <strong>Personality Color:</strong> {color.capitalize()}</p>
        <p>{description}</p>
    </div>
    """ , unsafe_allow_html=True)

    # Fetch peak listening hours
    peak_hour = display_weekly_listening_patterns(sp)

    st.markdown(f"""
    <div class="personality-card">
        <h2>Weekly Listening Stats</h2>
        <p><strong>Total Tracks This Week:</strong> {weekly_tracks}</p>
        <p><strong>Total Minutes Listened This Week:</strong> {int(weekly_minutes)} minutes</p>
        <p><strong>Peak Listening Hour:</strong> {peak_hour}:00</p>
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
    hour_df["Hour"].value_counts().sort_index().plot(kind='line', marker='o', ax=ax, color='#FF5733', linewidth=2)
    
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

    # Return the peak listening hour
    peak_hour = hour_df["Hour"].mode()[0]
    return peak_hour

# Analyze listening behavior for the personality profile
def analyze_listening_behavior(sp):
    top_artists = get_all_top_items(sp, item_type='artists', time_range='long_term')
    total_artists = len(top_artists)
    
    top_tracks = get_all_top_items(sp, item_type='tracks', time_range='long_term')
    total_songs = len(top_tracks)

    avg_songs_per_artist = total_songs / total_artists if total_artists else 0

    if avg_songs_per_artist > 30:
        return "Deep Diver", "blue", "You're all about depth—diving deep into a few artists and their entire discographies."
    elif total_artists > 40:
        return "Explorer", "green", "You're a breadth explorer, constantly seeking new artists and sounds."
    else:
        return "Balanced Listener", "yellow", "You strike the perfect balance between exploring new music and sticking to your favorites."

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

    tab1, tab2, tab3 = st.tabs([
        "Liked Songs & New Discoveries", 
        "Top Songs, Artists & Genres", 
        "Your Music Personality"
    ])

    with tab1:
        option = st.radio("Choose Option:", ["Liked Songs", "Discover New Songs"])
        mood = st.selectbox("Choose your mood:", ["Happy", "Calm", "Energetic", "Sad"])
        intensity = st.slider("Choose intensity:", 1, 5, 3)

        if option == "Liked Songs":
            liked_songs = get_all_liked_songs(sp)
            filtered_liked_songs = random.sample(liked_songs, min(len(liked_songs), 20))  # Limit and shuffle for display
            display_songs_with_cover(filtered_liked_songs, "Your Liked Songs")
        elif option == "Discover New Songs":
            discover_new_songs(sp, mood, intensity)

    with tab2:
        time_filter = st.selectbox("Select Time Period:", ["This Week", "This Month", "This Year"])
        time_mapping = {'This Week': 'short_term', 'This Month': 'medium_term', 'This Year': 'long_term'}
        display_top_insights_with_genres(sp, time_range=time_mapping[time_filter])

    with tab3:
        display_music_personality(sp)
    
else:
    st.write("Welcome to Wvvy")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
