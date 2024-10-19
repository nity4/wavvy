import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import time
import datetime

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
    query_params = st.query_params  # Replaced experimental_get_query_params with query_params
    
    if "code" in query_params:
        code = query_params["code"][0]
        try:
            token_info = sp_oauth.get_cached_token()  # Using cached token to avoid the deprecation warning
            if not token_info:
                token_info = sp_oauth.get_access_token(code)
            st.session_state['token_info'] = token_info
            st.experimental_set_query_params()  # Clear query parameters for now
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

# Retry cache for API calls to avoid redundant requests
@st.cache_data(ttl=600)  # Cache for 10 minutes
def cached_spotify_api_call(api_func, *args, **kwargs):
    return api_func(*args, **kwargs)

# Custom retry logic with better handling of the Retry-After header
def handle_spotify_rate_limit(sp_func, *args, max_retries=10, **kwargs):
    retries = 0
    while retries < max_retries:
        try:
            return sp_func(*args, **kwargs)
        except spotipy.SpotifyException as e:
            if e.http_status == 429:
                retry_after = int(e.headers.get("Retry-After", 5))  # Wait for the exact time Spotify suggests
                st.warning(f"Rate limit reached. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                retries += 1
            else:
                st.error(f"Error: {e}")
                break
    st.error("Max Retries reached. Please try again later.")
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
    random.shuffle(liked_songs)
    return liked_songs

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

# Fetch top items for insights
@st.cache_data(ttl=600)  # Cache results for 10 minutes to prevent excessive API requests
def get_top_items(sp, item_type='tracks', time_range='short_term', limit=10):
    if item_type == 'tracks':
        results = handle_spotify_rate_limit(sp.current_user_top_tracks, time_range=time_range, limit=limit)
    elif item_type == 'artists':
        results = handle_spotify_rate_limit(sp.current_user_top_artists, time_range=time_range, limit=limit)
    
    items = []
    if results:
        for item in results['items']:
            if item_type == 'tracks':
                items.append({
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

# Main app logic
if is_authenticated():
    sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

    # Tabs for different features
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
            liked_songs = get_liked_songs(sp)
            if liked_songs:
                filtered_liked_songs = [song for song in liked_songs if song['energy'] > 0.5]  # example filter
                display_songs(filtered_liked_songs, "Your Liked Songs")
            else:
                st.warning("No liked songs available.")
        else:
            st.warning("Discover New Songs feature not implemented.")

    with tab2:
        time_filter = st.selectbox("Select Time Period:", ["This Week", "This Month", "This Year"])
        time_mapping = {'This Week': 'short_term', 'This Month': 'medium_term', 'This Year': 'long_term'}
        top_tracks = get_top_items(sp, item_type='tracks', time_range=time_mapping[time_filter])
        display_songs(top_tracks, "Your Top Tracks")

else:
    st.write("Welcome to Wvvy")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
