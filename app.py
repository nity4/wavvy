import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
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

# Custom CSS for modern and interactive design
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
    .insight-popup {
        background-color: #2c2c2c;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .insight-header {
        color: #ffd700;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .insight-detail {
        color: #f5f5f5;
        font-size: 1rem;
        margin-top: 10px;
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

# Fetch all liked songs from the user's library
def get_all_liked_songs(sp):
    liked_songs = []
    results = sp.current_user_saved_tracks(limit=50, offset=0)
    total_songs = results['total']
    
    while len(liked_songs) < total_songs:
        liked_songs.extend(results['items'])
        offset = len(liked_songs)
        results = sp.current_user_saved_tracks(limit=50, offset=offset)
    
    return liked_songs

# Fetch audio features in batches to avoid the 414 error
def fetch_audio_features_in_batches(sp, song_ids):
    features = []
    batch_size = 100  # Spotify's limit for batch requests

    for i in range(0, len(song_ids), batch_size):
        batch = song_ids[i:i + batch_size]
        audio_features = sp.audio_features(tracks=batch)
        features.extend(audio_features)

    return features

# Filter songs by mood and intensity
def filter_songs_by_mood(track_features, feeling, intensity):
    filtered_songs = []
    
    for track in track_features:
        valence = track.get('valence', 0)
        energy = track.get('energy', 0)
        tempo = track.get('tempo', 0)
        danceability = track.get('danceability', 0)

        score = 0
        if feeling == "Happy":
            score += (valence - 0.7) * 10
            score += (energy - (intensity / 10)) * 5
        elif feeling == "Sad":
            score += (0.3 - valence) * 10
        elif feeling == "Chill":
            score += (0.5 - energy) * 7
        elif feeling == "Hype":
            score += (energy - 0.8) * 12
        elif feeling == "Romantic":
            score += (valence - 0.6) * 5
        elif feeling == "Adventurous":
            score += danceability * 5

        if score > intensity * 1.8:
            filtered_songs.append(track)
    
    return filtered_songs

# Display personalized insights
def display_insights(top_tracks, top_artists, top_genres, time_range):
    st.header(f"Fun Insights from your {time_range} Listening Habits")

    # Total number of songs listened to
    total_songs = len(top_tracks['items']) if top_tracks else 0
    most_played_artist = top_artists['items'][0]['name'] if top_artists['items'] else "Unknown Artist"
    most_played_song = top_tracks['items'][0]['name'] if top_tracks['items'] else "Unknown Song"

    with st.sidebar:
        st.markdown('<div class="insight-popup">', unsafe_allow_html=True)
        st.markdown('<div class="insight-header">🎤 Your Most Played Artist</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-detail">**{most_played_artist}**</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="insight-header">🎵 Your Most Played Song</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-detail">**{most_played_song}**</div>', unsafe_allow_html=True)
        
        # Insight: Genre diversity
        st.markdown('<div class="insight-header">🎶 Genre Diversity</div>', unsafe_allow_html=True)
        genre_count = len(set(top_genres))
        st.markdown(f'<div class="insight-detail">Your listening span covered **{genre_count}** unique genres!</div>', unsafe_allow_html=True)

        # Insight: Number of new artists discovered
        st.markdown('<div class="insight-header">🌟 New Artists Discovered</div>', unsafe_allow_html=True)
        new_artists = len(set(artist['name'] for artist in top_artists['items']))
        st.markdown(f'<div class="insight-detail">You discovered **{new_artists}** new artists this {time_range.lower()}!</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

# Get and display top items with filtering and insights
def get_top_items_with_insights(sp):
    st.header("Your Top Songs, Artists, and Genres with Insights")

    # Time range selection for filtering insights
    time_range = st.radio("Select time range", ['This Week', 'This Month', 'This Year'], index=1, key="time_range_radio")
    time_range_map = {'This Week': 'short_term', 'This Month': 'medium_term', 'This Year': 'long_term'}
    spotify_time_range = time_range_map[time_range]

    # Fetch top tracks, artists, and genres
    top_tracks = sp.current_user_top_tracks(time_range=spotify_time_range, limit=10)
    top_artists = sp.current_user_top_artists(time_range=spotify_time_range, limit=5)
    top_genres = [genre for artist in top_artists['items'] for genre in artist['genres']]

    # Display top songs
    if top_tracks['items']:
        st.subheader("Your Top Songs")
        for i, track in enumerate(top_tracks['items']):
            song_name = track['name']
            artist_name = track['artists'][0]['name']
            album_cover = track['album']['images'][0]['url']
            st.image(album_cover, width=150, caption=f"{i+1}. {song_name} by {artist_name}")
    else:
        st.write(f"No top songs found for {time_range}.")

    # Display top artists
    if top_artists['items']:
        st.subheader("Your Top Artists")
        for i, artist in enumerate(top_artists['items']):
            artist_name = artist['name']
            artist_cover = artist['images'][0]['url']
            st.image(artist_cover, width=150, caption=f"{i+1}. {artist_name}")
    else:
        st.write(f"No top artists found for {time_range}.")

    # Display top genres
    if top_genres:
        st.subheader("Your Top Genres")
        unique_genres = list(set(top_genres))[:5]
        if unique_genres:
            st.write("You're currently into these genres:")
            for genre in unique_genres:
                st.write(f"🎶 - {genre.capitalize()}")
        else:
            st.write(f"No genres found for {time_range}.")
    else:
        st.write(f"No top genres for {time_range}.")

    # Show insights based on the user's listening habits
    display_insights(top_tracks, top_artists, top_genres, time_range)

# Mood-Based Music Discovery
def discover_music_by_feelings(sp):
    st.header("Curated Music for Your Mood")
    st.write("Select your mood, and we'll build the perfect playlist.")

    feeling = st.selectbox("What's your vibe today?", ["Happy", "Sad", "Chill", "Hype", "Romantic", "Adventurous"])
    intensity = st.slider(f"How {feeling} are you feeling?", 1, 10)

    try:
        # Fetch user's liked songs and audio features
        liked_songs = get_all_liked_songs(sp)
        random.shuffle(liked_songs)
        song_ids = [track['track']['id'] for track in liked_songs]

        # Fetch audio features in batches
        features = fetch_audio_features_in_batches(sp, song_ids)

        # Apply filtering based on mood and intensity
        filtered_songs = filter_songs_by_mood(features, feeling, intensity)

        if filtered_songs:
            st.subheader(f"Here's your {feeling.lower()} playlist:")
            for i, feature in enumerate(filtered_songs[:10]):
                song = liked_songs[i]['track']
                song_name = song['name']
                artist_name = song['artists'][0]['name']
                album_cover = song['album']['images'][0]['url']
                st.image(album_cover, width=150, caption=f"{song_name} by {artist_name}")
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
            "Your Music Insights"
        ], key="main_radio")

        if section == "Mood-Based Music Discovery":
            discover_music_by_feelings(sp)
        elif section == "Your Music Insights":
            get_top_items_with_insights(sp)

    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to **Wavvy**")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
