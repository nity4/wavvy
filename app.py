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

# Fetch user's top songs and genres based on a time range
def get_top_items(sp, time_range='medium_term'):
    st.header(f"Your Top Songs and Genres ({time_range.replace('_', ' ').title()})")
    
    # Allow users to select time range for insights
    time_range = st.radio("Select time range", ['short_term', 'medium_term', 'long_term'], index=1)
    
    # Fetch top tracks
    top_tracks = sp.current_user_top_tracks(time_range=time_range, limit=10)
    top_artists = sp.current_user_top_artists(time_range=time_range, limit=5)

    if top_tracks['items']:
        st.subheader("Your Top Songs")
        cols = st.columns(2)
        for i, track in enumerate(top_tracks['items']):
            song_name = track['name']
            artist_name = track['artists'][0]['name']
            album_cover = track['album']['images'][0]['url']
            with cols[i % 2]:
                st.image(album_cover, width=150, caption=f"{i+1}. {song_name} by {artist_name}")

    else:
        st.write("No top songs available for this time range.")

    if top_artists['items']:
        st.subheader("Your Top Genres")
        all_genres = [genre for artist in top_artists['items'] for genre in artist['genres']]
        unique_genres = list(set(all_genres))[:5]  # Limit to 5 unique genres

        if unique_genres:
            st.write("You're currently into these genres:")
            for genre in unique_genres:
                st.write(f"- {genre.capitalize()}")
        else:
            st.write("No genres found for this time range.")
    else:
        st.write("No top genres available for this time range.")

# Dynamic Insights with Expander
def comprehensive_insights(sp):
    st.header("Your Music Journey: Insights")
    
    # Fetch user's top artists and tracks
    top_artists = sp.current_user_top_artists(limit=5)
    top_tracks = sp.current_user_recently_played(limit=20)

    # Insight 1: Top Artists
    with st.expander("Your Top Artists"):
        if top_artists['items']:
            for i, artist in enumerate(top_artists['items']):
                st.write(f"{i+1}. {artist['name']}")
        else:
            st.write("No top artists available.")

    # Insight 2: Recently Played Tracks
    with st.expander("Your Recently Played Tracks"):
        if top_tracks['items']:
            for i, track in enumerate(top_tracks['items']):
                song_name = track['track']['name']
                artist_name = track['track']['artists'][0]['name']
                album_cover = track['track']['album']['images'][0]['url']
                st.image(album_cover, width=100, caption=f"{song_name} by {artist_name}")
        else:
            st.write("No recent tracks available.")

    # Insight 3: Fun Fact (Example: Number of New Artists Discovered)
    new_artists = len(set(track['track']['artists'][0]['name'] for track in top_tracks['items']))
    st.subheader(f"You've discovered {new_artists} new artists recently. Keep exploring!")

# Main App Flow
if is_authenticated():
    try:
        refresh_token()
        sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

        section = st.radio("Choose an Experience:", [
            "Your Music Insights", 
            "Mood-Based Music Discovery"
        ])

        if section == "Your Music Insights":
            get_top_items(sp)  # Provides time range filter for top tracks and artists
            comprehensive_insights(sp)  # Detailed insights

        elif section == "Mood-Based Music Discovery":
            discover_music_by_feelings(sp)

    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to **Wavvy**")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
