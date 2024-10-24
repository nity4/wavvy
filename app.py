import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import pandas as pd
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
            token_info = sp_oauth.get_cached_token()
            if not token_info:
                token_info = sp_oauth.get_access_token(code)
            if token_info:  # Ensure token_info is not None
                st.session_state['token_info'] = token_info
                st.experimental_set_query_params()  # Clear the query params after authentication
                st.success("You're authenticated! Click the button below to enter.")
                if st.button("Enter Wvvy"):
                    st.experimental_rerun()
            else:
                st.error("Failed to retrieve token.")
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
def handle_spotify_api(sp_func, *args, **kwargs):
    try:
        return sp_func(*args, **kwargs)
    except (spotipy.SpotifyException, ReadTimeout) as e:
        st.error(f"Error: {e}")
        return None

# Function to fetch all liked songs for the authenticated user
def get_all_liked_songs(sp):
    liked_songs = []
    offset = 0
    while True:
        results = handle_spotify_api(sp.current_user_saved_tracks, limit=50, offset=offset)
        if not results or 'items' not in results:  # Ensure results exist and contain 'items'
            break
        for item in results['items']:
            track = item.get('track')
            if track is None:  # Check if track is None
                continue
            audio_features = handle_spotify_api(sp.audio_features, [track['id']])
            if audio_features and audio_features[0]:  # Check if audio_features is valid
                liked_songs.append({
                    "id": track.get('id', None),
                    "name": track.get('name', "Unknown Track"),
                    "artist": track['artists'][0]['name'] if 'artists' in track and track['artists'] else "Unknown Artist",
                    "cover": track['album']['images'][0]['url'] if 'album' in track and track['album']['images'] else None,
                    "energy": audio_features[0].get("energy", 0.5),
                    "valence": audio_features[0].get("valence", 0.5),
                    "tempo": audio_features[0].get("tempo", 120),
                    "popularity": track.get('popularity', 0)
                })
        offset += 50
    return liked_songs

# Function to fetch top items (tracks or artists) for the authenticated user
def get_all_top_items(sp, item_type='tracks', time_range='short_term'):
    top_items = []
    offset = 0
    while True:
        if item_type == 'tracks':
            results = handle_spotify_api(sp.current_user_top_tracks, time_range=time_range, limit=50, offset=offset)
        elif item_type == 'artists':
            results = handle_spotify_api(sp.current_user_top_artists, time_range=time_range, limit=50, offset=offset)
        
        if not results or 'items' not in results:  # Check if results and items exist
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
            recommendations = handle_spotify_api(
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

else:
    st.write("Welcome to Wvvy")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
