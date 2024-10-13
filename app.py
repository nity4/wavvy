import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import matplotlib.pyplot as plt
import time

# Spotify API credentials from Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Spotify OAuth Scope to access user's full library and other data
SCOPE = 'user-library-read user-top-read user-read-recently-played'

# Initialize Spotify OAuth
sp_oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE)

# Streamlit App Layout with Sleek Design
st.set_page_config(page_title="Wavvy", page_icon="🌊", layout="centered", initial_sidebar_state="collapsed")

# Custom CSS for Modern, Visual Appeal
st.markdown(
    """
    <style>
    body {
        background-color: #121212;
        color: #f5f5f5;
        font-family: 'Roboto', sans-serif;
    }
    .stButton>button {
        background-color: #0073e6;
        color: #ffffff;
        border-radius: 12px;
        font-size: 1rem;
        padding: 0.5rem;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #ff4081;
    }
    .stImage {
        border-radius: 15px;
        margin-bottom: 12px;
    }
    h1, h2, h3 {
        font-weight: 400;
        color: #ff4081;
    }
    h1 {
        font-size: 3.5rem;
        margin-bottom: 1rem;
    }
    h2 {
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    h3 {
        font-size: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .album-cover {
        display: inline-block;
        margin: 10px;
        text-align: center;
    }
    .artist-cover {
        width: 150px;
        height: 150px;
        border-radius: 50%;
    }
    </style>
    """, unsafe_allow_html=True
)

# Authentication Helpers
def is_authenticated():
    return st.session_state.get('token_info') is not None

def refresh_token():
    if st.session_state['token_info']:
        if sp_oauth.is_token_expired(st.session_state['token_info']):
            token_info = sp_oauth.refresh_access_token(st.session_state['token_info']['refresh_token'])
            st.session_state['token_info'] = token_info

def authenticate_user():
    try:
        if "code" in st.experimental_get_query_params():
            code = st.experimental_get_query_params()["code"][0]
            token_info = sp_oauth.get_access_token(code)
            st.session_state['token_info'] = token_info
            st.experimental_set_query_params(code=None)
            st.success("You're authenticated! Refresh to get your music data.")
            if st.button("Refresh Now"):
                st.experimental_set_query_params()
        else:
            auth_url = sp_oauth.get_authorize_url()
            st.markdown(f'<a href="{auth_url}" target="_self" style="color: #ff4081;">Login with Spotify</a>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Authentication error: {e}")

# Fetch all liked songs
def get_all_liked_songs(sp):
    liked_songs = []
    results = sp.current_user_saved_tracks(limit=50, offset=0)
    total_songs = results['total']
    
    while len(liked_songs) < total_songs:
        liked_songs.extend(results['items'])
        offset = len(liked_songs)
        results = sp.current_user_saved_tracks(limit=50, offset=offset)
    
    return liked_songs

# Enhanced Mood-Based Music Discovery
def discover_music_by_feelings(sp):
    st.header("Curated Music for Your Mood")
    st.write("Select your mood, and we'll build the perfect playlist.")

    feeling = st.selectbox("What's your vibe today?", ["Happy", "Sad", "Chill", "Hype", "Romantic", "Adventurous"])
    intensity = st.slider(f"How {feeling} are you feeling?", 1, 10)
    song_type = st.radio("Choose:", ["Shuffle Liked Songs", "Discover New Vibes"])

    try:
        st.write("Creating your playlist...")
        
        if song_type == "Shuffle Liked Songs":
            liked_songs = get_all_liked_songs(sp)  # Fetch all liked songs
            random.shuffle(liked_songs)
        else:
            seed_artists = [artist['id'] for artist in sp.current_user_top_artists(limit=5)['items']]
            results = sp.recommendations(seed_artists=seed_artists, limit=50)
            liked_songs = results['tracks']

        song_ids = [track['track']['id'] if song_type == "Shuffle Liked Songs" else track['id'] for track in liked_songs]
        features = sp.audio_features(tracks=song_ids)

        filtered_songs = []
        for i, song in enumerate(liked_songs):
            feature = features[i]
            if feature:
                valence, energy, danceability, tempo, acousticness = feature['valence'], feature['energy'], feature['danceability'], feature['tempo'], feature['acousticness']
                if feeling == "Happy" and valence > 0.7 and energy >= intensity / 10:
                    filtered_songs.append(song)
                elif feeling == "Sad" and valence < 0.3 and energy <= intensity / 10 and acousticness > 0.5:
                    filtered_songs.append(song)
                elif feeling == "Chill" and energy < 0.5 and tempo < 100:
                    filtered_songs.append(song)
                elif feeling == "Hype" and energy > 0.8 and tempo > 120:
                    filtered_songs.append(song)
                elif feeling == "Romantic" and valence > 0.6 and 60 <= tempo <= 90:
                    filtered_songs.append(song)
                elif feeling == "Adventurous" and danceability > 0.6 and tempo > 100:
                    filtered_songs.append(song)

        if filtered_songs:
            st.subheader(f"Here's your {feeling.lower()} playlist:")
            for track in filtered_songs[:10]:
                song_name = track['track']['name'] if song_type == "Shuffle Liked Songs" else track['name']
                artist_name = track['track']['artists'][0]['name'] if song_type == "Shuffle Liked Songs" else track['artists'][0]['name']
                album_cover = track['track']['album']['images'][0]['url'] if song_type == "Shuffle Liked Songs" else track['album']['images'][0]['url']
                st.image(album_cover, width=150)
                st.write(f"**{song_name}** by *{artist_name}*")
        else:
            st.write(f"No tracks match your {feeling.lower()} vibe right now. Try tweaking the intensity or picking a different mood.")

    except Exception as e:
        st.error(f"Error curating your playlist: {e}")

# Main App Flow
if is_authenticated():
    try:
        refresh_token()
        sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

        section = st.radio("Choose an Experience:", [
            "Mood-Based Music Discovery", 
            "Your Music Insights", 
            "Your Music Personality"
        ])

        if section == "Mood-Based Music Discovery":
            discover_music_by_feelings(sp)
        # Other sections omitted for brevity
    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to **Wavvy** 🌊")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
