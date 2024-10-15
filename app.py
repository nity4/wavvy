import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import pandas as pd
import time

# Spotify API credentials from Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Define the required scope for Spotify access
scope = "user-library-read user-top-read"

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

# Custom CSS styling for app layout and UI
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
        padding-top: 20px;
    }
    .loading-text {
        font-size: 1.5em;
        color: white;
        text-align: center;
        padding: 20px;
    }
    .login-button {
        color: white;
        background-color: #ff4081;
        padding: 10px 20px;
        border-radius: 8px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='header-title'>〰 Wvvy</div>", unsafe_allow_html=True)

# Authentication Functions
def is_authenticated():
    return 'token_info' in st.session_state and st.session_state['token_info'] is not None

def refresh_token():
    if 'token_info' in st.session_state and sp_oauth.is_token_expired(st.session_state['token_info']):
        token_info = sp_oauth.refresh_access_token(st.session_state['token_info']['refresh_token'])
        st.session_state['token_info'] = token_info

def authenticate_user():
    query_params = st.query_params  # Updated from st.experimental_get_query_params()
    
    if "code" in query_params:
        code = query_params["code"]
        try:
            token_info = sp_oauth.get_access_token(code)
            st.session_state['token_info'] = token_info
            st.experimental_set_query_params()  # Clear the query params
            st.success("You're authenticated! You can now access your music data.")
        except Exception as e:
            st.error(f"Authentication error: {e}")
    else:
        auth_url = sp_oauth.get_authorize_url()
        # Open in a new tab to avoid iframe issues
        st.markdown(
            f'<a href="{auth_url}" target="_blank" class="login-button">Login with Spotify</a>',
            unsafe_allow_html=True
        )

# Loading Animation
def show_loading_animation(text="Loading..."):
    st.markdown(f"<div class='loading-text'>{text}</div>", unsafe_allow_html=True)
    with st.spinner("Processing..."):
        time.sleep(2)  # Simulate a loading process

# Fetch all liked songs
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

# Fetch audio features in batches
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

# Filter liked songs by mood
def filter_liked_songs_by_mood(track_features, feeling, intensity):
    filtered_songs = []
    fallback_songs = []

    for track in track_features:
        if track is None:
            continue  # Skip if audio features are not available

        valence = track.get('valence', 0)
        energy = track.get('energy', 0)
        danceability = track.get('danceability', 0)
        tempo = track.get('tempo', 0)

        score = 0  # Base score for filtering
        
        # Apply mood-based filtering
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

        # Track filtering based on intensity and score
        if score > intensity * 1.2:
            filtered_songs.append(track)
        elif score > intensity * 0.8:
            fallback_songs.append(track)

    # Return fallback songs if no strong match
    return filtered_songs if filtered_songs else fallback_songs

# Mood-based music discovery
def discover_music_by_feelings(sp):
    st.header("Curate Your Vibe")
    feeling = st.selectbox("What's your vibe today?", ["Happy", "Sad", "Chill", "Hype", "Romantic", "Adventurous"])
    intensity = st.slider(f"How {feeling.lower()} are you feeling?", 1, 5)

    try:
        liked_songs = get_all_liked_songs(sp)
        if len(liked_songs) > 0:
            show_loading_animation(text="Creating your vibe-based playlist...")
            random.shuffle(liked_songs)
            song_ids = [track['track']['id'] for track in liked_songs if track['track']['id'] is not None]
            features = fetch_audio_features_in_batches(sp, song_ids)
            filtered_songs = filter_liked_songs_by_mood(features, feeling, intensity)
        else:
            filtered_songs = []

        if filtered_songs:
            st.subheader(f"Here's your {feeling.lower()} playlist:")
            cols = st.columns(2)
            for i, feature in enumerate(filtered_songs[:10]):
                with cols[i % 2]:
                    song = sp.track(feature['id'])
                    song_name = song['name']
                    artist_name = song['artists'][0]['name']
                    album_cover = song['album']['images'][0]['url']
                    st.image(album_cover, width=150, caption=f"{song_name} by {artist_name}")
        else:
            st.write(f"No tracks match your {feeling.lower()} vibe right now. Try adjusting the intensity or picking a different mood.")
    
    except Exception as e:
        st.error(f"Error curating your playlist: {e}")

# Fetch and display user's top tracks, artists, and genres
def get_top_items_with_insights(sp):
    st.header("Your Top Songs, Artists, and Genres")
    time_range = st.radio("Select time range", ['This Week', 'This Month', 'This Year'], index=1)

    time_range_map = {'This Week': 'short_term', 'This Month': 'medium_term', 'This Year': 'long_term'}
    spotify_time_range = time_range_map[time_range]

    show_loading_animation(text="Fetching your top tracks and insights...")
    top_tracks = sp.current_user_top_tracks(time_range=spotify_time_range, limit=10)
    top_artists = sp.current_user_top_artists(time_range=spotify_time_range, limit=5)
    top_genres = [genre for artist in top_artists['items'] for genre in artist.get('genres', [])]

    st.subheader("Your Top Songs")
    for i, track in enumerate(top_tracks['items']):
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(track['album']['images'][0]['url'], width=60)
        with col2:
            st.write(f"**{i+1}. {track['name']}** by {track['artists'][0]['name']}")

    st.subheader("Your Top Artists")
    for i, artist in enumerate(top_artists['items']):
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(artist['images'][0]['url'], width=60)
        with col2:
            st.write(f"**{i+1}. {artist['name']}**")

    st.subheader("Your Top 5 Genres")
    if top_genres:
        top_5_genres = pd.Series(top_genres).value_counts().head(5).index.tolist()
        st.write(", ".join(top_5_genres))
    else:
        st.write("No genre information available.")

# Optional: Implement Music Personality section
def music_personality(sp):
    st.header("Music Personality Insights")
    st.write("Coming soon! Explore more about your music personality based on your listening habits.")

# Main app logic
if is_authenticated():
    try:
        refresh_token()
        sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

        # Navigation for different pages
        page = st.sidebar.radio("Navigation", [
            "Wavvy", 
            "Your Top Hits", 
            "Music Personality"
        ])

        if page == "Wavvy":
            discover_music_by_feelings(sp)
        elif page == "Your Top Hits":
            get_top_items_with_insights(sp)
        elif page == "Music Personality":
            music_personality(sp)

    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to Wvvy")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
