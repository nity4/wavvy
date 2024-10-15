import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random

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

# Custom CSS for black font on select boxes
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
    .stSelectbox label, .stSlider label {
        color: black !important;
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
    query_params = st.experimental_get_query_params()
    
    if "code" in query_params:
        code = query_params["code"][0]
        try:
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

# Retrieve liked songs and audio features (valence, energy, tempo)
def get_liked_songs(sp):
    results = sp.current_user_saved_tracks(limit=50)
    liked_songs = []
    for item in results['items']:
        track = item['track']
        audio_features = sp.audio_features(track['id'])[0]
        liked_songs.append({
            "name": track['name'],
            "artist": track['artists'][0]['name'],
            "cover": track['album']['images'][0]['url'] if track['album']['images'] else None,
            "energy": audio_features["energy"],
            "valence": audio_features["valence"],
            "tempo": audio_features["tempo"]
        })
    return liked_songs

# Retrieve recommendations based on user's listening habits
def get_new_discoveries(sp):
    results = sp.current_user_top_tracks(limit=5, time_range="medium_term")
    top_artists = sp.current_user_top_artists(limit=5, time_range="medium_term")['items']
    
    # Seed recommendations with user's top genres and tracks
    top_tracks = [track['id'] for track in results['items']]
    top_genres = [artist['genres'][0] for artist in top_artists if artist['genres']]
    
    recommendations = sp.recommendations(seed_tracks=top_tracks, seed_genres=top_genres, limit=50)
    
    new_songs = []
    for track in recommendations['tracks']:
        audio_features = sp.audio_features(track['id'])[0]
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
        refresh_token()
        st.success("You are logged in! Your Spotify data is ready for analysis.")
        
        sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])
        
        # Mood and Intensity filters
        mood = st.selectbox("Choose your mood:", ["Happy", "Calm", "Energetic", "Sad"])
        intensity = st.slider("Choose intensity:", 1, 5, 3)  # Adjusted intensity to 1-5
        
        # Tabs for liked songs and new discoveries
        tab1, tab2 = st.tabs(["Liked Songs", "New Discoveries"])

        with tab1:
            liked_songs = get_liked_songs(sp)
            filtered_liked_songs = filter_songs(liked_songs, mood, intensity)
            display_songs(filtered_liked_songs, "Your Liked Songs")

        with tab2:
            new_songs = get_new_discoveries(sp)
            filtered_new_songs = filter_songs(new_songs, mood, intensity)
            display_songs(filtered_new_songs, "New Song Discoveries")
        
    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to Wvvy")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
