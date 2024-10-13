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

# Fetch top songs, artists, and genres with time range filter and fun insights
def get_top_items(sp):
    st.header("Your Top Songs, Artists, and Genres")
    
    # Allow users to select time range for insights
    time_range = st.radio("Select time range", ['This Week', 'This Month', 'This Year'], index=1)
    
    time_range_map = {
        'This Week': 'short_term',
        'This Month': 'medium_term',
        'This Year': 'long_term'
    }
    
    spotify_time_range = time_range_map[time_range]
    st.write(f"Showing data for: **{time_range}**")

    # Fetch top tracks
    top_tracks = sp.current_user_top_tracks(time_range=spotify_time_range, limit=10)
    if top_tracks['items']:
        st.subheader("Your Top Songs")
        for i, track in enumerate(top_tracks['items']):
            song_name = track['name']
            artist_name = track['artists'][0]['name']
            album_cover = track['album']['images'][0]['url']
            st.image(album_cover, width=150, caption=f"{i+1}. {song_name} by {artist_name}")
    else:
        st.write(f"No top songs for {time_range}.")

    # Fetch top artists
    top_artists = sp.current_user_top_artists(time_range=spotify_time_range, limit=5)
    if top_artists['items']:
        st.subheader("Your Top Artists")
        for i, artist in enumerate(top_artists['items']):
            artist_name = artist['name']
            artist_cover = artist['images'][0]['url']
            st.image(artist_cover, width=150, caption=f"{i+1}. {artist_name}")
    else:
        st.write(f"No top artists for {time_range}.")

    # Fetch top genres from top artists
    if top_artists['items']:
        st.subheader("Your Top Genres")
        all_genres = [genre for artist in top_artists['items'] for genre in artist['genres']]
        unique_genres = list(set(all_genres))[:5]  # Limit to 5 unique genres

        if unique_genres:
            st.write("You're currently into these genres:")
            for genre in unique_genres:
                st.write(f"🎶 - {genre.capitalize()}")
        else:
            st.write(f"No genres found for {time_range}.")
    else:
        st.write(f"No top genres for {time_range}.")

# Fun insights pop-up after data is loaded
def show_fun_insights(sp, top_artists, top_tracks, time_range):
    st.write(f"Fun insights for **{time_range}**:")

    most_played_artist = top_artists['items'][0]['name'] if top_artists['items'] else 'Unknown Artist'
    most_played_song = top_tracks['items'][0]['name'] if top_tracks['items'] else 'Unknown Song'

    st.toast(f"Your most played artist of {time_range} is **{most_played_artist}** with the song **{most_played_song}**.")
    
    # Fun fact: Number of new artists discovered
    new_artists = len(set(track['artists'][0]['name'] for track in top_tracks['items']))
    st.toast(f"You've discovered **{new_artists}** new artists this {time_range.lower()}.")

    # Fun fact: Genre diversity
    all_genres = [genre for artist in top_artists['items'] for genre in artist['genres']]
    genre_count = len(set(all_genres))
    st.toast(f"Your listening span covered **{genre_count}** unique genres!")

    # Fun fact: Song replay habit
    repeat_songs = random.choice(top_tracks['items'])['name'] if top_tracks['items'] else None
    if repeat_songs:
        st.toast(f"You seem to love replaying **{repeat_songs}** quite a bit!")

# Comprehensive insights and stats with improved flow
def comprehensive_insights(sp):
    st.header("Your Music Journey: Insights")

    try:
        # Fetch user's top items based on time range selection
        time_range = st.radio("Select time range", ['This Week', 'This Month', 'This Year'], index=1)
        spotify_time_range = {
            'This Week': 'short_term',
            'This Month': 'medium_term',
            'This Year': 'long_term'
        }[time_range]

        # Fetch top tracks
        top_tracks = sp.current_user_top_tracks(time_range=spotify_time_range, limit=10)
        # Fetch top artists
        top_artists = sp.current_user_top_artists(time_range=spotify_time_range, limit=5)

        # Display top items (songs, artists, genres)
        get_top_items(sp)

        # Show fun insights (pass the time_range variable to the function)
        show_fun_insights(sp, top_artists, top_tracks, time_range)

    except Exception as e:
        st.error(f"Error fetching insights: {e}")

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
        elif section == "Your Music Insights":
            comprehensive_insights(sp)
        elif section == "Your Music Personality":
            music_personality_analysis(sp)

    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to **Wavvy**")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
