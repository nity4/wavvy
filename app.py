import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import pandas as pd
import matplotlib.pyplot as plt
import time

# Spotify API credentials from Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

SCOPE = 'user-library-read user-top-read user-read-recently-played'

# Initialize Spotify OAuth
sp_oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE)

# App Layout and Configuration
st.set_page_config(page_title="VibeCheck", page_icon="🎧", layout="wide", initial_sidebar_state="expanded")
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
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='header-title'>VibeCheck</div>", unsafe_allow_html=True)

# Authentication Functions
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
            st.success("You're in. Refresh to access your music data.")
            if st.button("Refresh Now"):
                st.experimental_set_query_params()
        else:
            auth_url = sp_oauth.get_authorize_url()
            st.markdown(f'<a href="{auth_url}" target="_self" style="color: white; background-color: #ff4081; padding: 10px; border-radius: 8px;">Login with Spotify</a>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Authentication error: {e}")

# Helper Functions
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

# Listening Time Insights (Daily Listening for the Past Week)
def get_listening_time_insights(sp):
    st.subheader("How much have you been listening this week?")
    recent_tracks = sp.current_user_recently_played(limit=50)
    timestamps = [track['played_at'] for track in recent_tracks['items']]
    
    # Convert timestamps to pandas datetime series for time-based analysis
    time_data = pd.Series(pd.to_datetime(timestamps))
    daily_listening = time_data.dt.date.value_counts().sort_index()

    st.write("Here's how much you've listened each day this week:")
    for day, count in daily_listening.items():
        st.write(f"{day}: {count} tracks")

# Genre Evolution Over Time
def get_genre_evolution(sp):
    st.subheader("Your Genre Evolution Over Time")
    top_artists_long_term = sp.current_user_top_artists(time_range='long_term', limit=50)['items']
    top_artists_short_term = sp.current_user_top_artists(time_range='short_term', limit=50)['items']
    
    long_term_genres = [genre for artist in top_artists_long_term for genre in artist['genres']]
    short_term_genres = [genre for artist in top_artists_short_term for genre in artist['genres']]

    # Display Top Genres
    unique_long_term_genres = set(long_term_genres)
    unique_short_term_genres = set(short_term_genres)
    new_genres = unique_short_term_genres - unique_long_term_genres
    
    st.write(f"Your top genres over time: {', '.join(unique_long_term_genres)}")
    if new_genres:
        st.write(f"Recently explored genres: {', '.join(new_genres)}")

# Mainstream vs Niche Insight
def get_niche_vs_mainstream_insight(sp, top_tracks):
    st.subheader("Mainstream vs Niche Insights")
    popularity_scores = [track['popularity'] for track in top_tracks['items']]
    
    avg_popularity = sum(popularity_scores) / len(popularity_scores)
    if avg_popularity > 70:
        st.write("You're into pretty mainstream tracks.")
    else:
        st.write("You're into niche, lesser-known tracks.")

# Insights Switching Mechanism
def insights_rotator(sp):
    top_tracks = sp.current_user_top_tracks(time_range='long_term', limit=10)

    insights = [
        ("Listening Time Insights", get_listening_time_insights),
        ("Genre Evolution Over Time", get_genre_evolution),
        ("Mainstream vs Niche", lambda sp: get_niche_vs_mainstream_insight(sp, top_tracks))
    ]

    insight_index = st.session_state.get("insight_index", 0)
    
    # Display the current insight
    insight_name, insight_func = insights[insight_index]
    st.write(f"Current Insight: **{insight_name}**")
    insight_func(sp)

    # Add buttons to navigate between insights
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Previous Insight"):
            insight_index = (insight_index - 1) % len(insights)
    with col2:
        if st.button("Next Insight"):
            insight_index = (insight_index + 1) % len(insights)

    # Save the current insight index in the session state
    st.session_state["insight_index"] = insight_index

# Music Personality Page (Create Profile)
def personality_page(sp):
    st.header("Your Music Personality")

    top_tracks = sp.current_user_top_tracks(time_range='long_term', limit=50)
    top_artists = sp.current_user_top_artists(time_range='long_term', limit=5)

    st.subheader("🎧 Music Profile")
    
    # Add Personal Insights
    st.write("Here's a profile based on your listening habits:")
    
    # Display their top artist, favorite song, and genres
    if top_artists['items']:
        favorite_artist = top_artists['items'][0]['name']
        st.write(f"Your favorite artist: **{favorite_artist}**")

    if top_tracks['items']:
        favorite_song = top_tracks['items'][0]['name']
        st.write(f"Your favorite song: **{favorite_song}**")

    # Music Personality Traits
    st.subheader("What your music taste says about you")
    st.write("Based on your listening habits, here's a little bit about your personality:")
    # Add some fun, data-driven personality insights
    if top_artists['items']:
        st.write(f"You're someone who loves exploring new music by {top_artists['items'][0]['name']}, which shows you're creative and open to new experiences.")
    
    # Add interesting data points like how often they listen to music, favorite genre, etc.
    st.write("You have a broad taste in music, from niche genres to mainstream hits.")
    
    st.subheader("Unique Stats")
    st.write("Here are some fun stats about your listening habits:")
    # Show more unique data points: average listening time, top genre, most frequent listening time of day, etc.

    get_listening_time_insights(sp)  # Reuse existing insights

# Main App Layout
if is_authenticated():
    try:
        refresh_token()
        sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

        # Reorganizing the Page Flow
        page = st.sidebar.radio("Navigation", [
            "Vibe Check", 
            "Your Top Hits", 
            "Music Personality"
        ])

        if page == "Vibe Check":
            discover_music_by_feelings(sp)
        elif page == "Your Top Hits":
            st.header("Your Top Hits and Insights")
            get_top_items_with_insights(sp)
            st.markdown("---")
            insights_rotator(sp)  # Add rotating insights
        elif page == "Music Personality":
            personality_page(sp)

    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to VibeCheck")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
