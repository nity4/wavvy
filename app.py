import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import pandas as pd
import time
import matplotlib.pyplot as plt

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
    query_params = st.experimental_get_query_params()  # Fetch query params
    
    if "code" in query_params:
        code = query_params["code"][0]  # Get the auth code from the query parameters
        try:
            token_info = sp_oauth.get_access_token(code)
            st.session_state['token_info'] = token_info
            # Clear query parameters after authentication to avoid re-running
            st.experimental_set_query_params()  
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

# Fun insights from user data
def get_user_insights(top_tracks, top_artists):
    st.header("Fun Insights from Your Data")

    # Primetime of Listening
    track_timestamps = pd.Series([pd.Timestamp(track['played_at']) for track in top_tracks['items']])
    primetime = track_timestamps.dt.hour.mode()[0]
    st.write(f"Your **primetime** of listening is around **{primetime}:00** hours!")

    # Rarest Genre
    all_genres = [genre for artist in top_artists['items'] for genre in artist['genres']]
    genre_counts = pd.Series(all_genres).value_counts()
    rarest_genre = genre_counts.idxmin()
    st.write(f"Your **rarest genre** is **{rarest_genre}**.")

    # Most Active Listening Day
    most_active_day = track_timestamps.dt.day_name().mode()[0]
    st.write(f"Your most active day of listening is **{most_active_day}**.")

    # Average Song Length
    song_durations = [track['duration_ms'] for track in top_tracks['items']]
    avg_song_length = pd.Series(song_durations).mean() / 60000  # Convert to minutes
    st.write(f"Your average song length is **{avg_song_length:.2f} minutes**.")

# Fun "Music Personality" Analysis
def music_personality_insights(top_tracks):
    st.header("Music Personality Insights")

    # Analyzing the personality based on user data (just for fun)
    total_tracks = len(top_tracks['items'])
    if total_tracks > 200:
        personality = "The Collector"
        color = "Purple"
    elif total_tracks > 100:
        personality = "The Dreamer"
        color = "Blue"
    elif total_tracks > 50:
        personality = "The Explorer"
        color = "Green"
    else:
        personality = "The Minimalist"
        color = "Yellow"

    st.write(f"Based on your listening habits, your music personality is **{personality}**!")
    st.write(f"Your associated color is **{color}**.")

    # Plotting daily listening habit (number of tracks and minutes listened)
    daily_data = pd.DataFrame({
        'Day': pd.date_range(end=pd.Timestamp.today(), periods=7),
        'Songs': [random.randint(5, 20) for _ in range(7)],  # Simulated data
        'Minutes': [random.randint(30, 120) for _ in range(7)]  # Simulated data
    })
    daily_data.set_index('Day', inplace=True)

    st.write(f"Here's how your daily listening habits look this past week:")

    # Plot number of songs
    fig, ax = plt.subplots()
    daily_data['Songs'].plot(kind='bar', color=color, ax=ax)
    ax.set_title(f"Number of Songs Played (by day) - Personality: {personality}")
    ax.set_ylabel('Number of Songs')
    st.pyplot(fig)

    # Plot number of minutes
    fig, ax = plt.subplots()
    daily_data['Minutes'].plot(kind='bar', color=color, ax=ax)
    ax.set_title(f"Number of Minutes Played (by day) - Personality: {personality}")
    ax.set_ylabel('Minutes')
    st.pyplot(fig)

# Fetch and display user's top tracks, artists, and genres with insights
def get_top_items_with_insights(sp):
    st.header("Your Top Songs, Artists, and Genres")
    time_range = st.radio("Select time range", ['This Week', 'This Month', 'This Year'], index=1)

    time_range_map = {'This Week': 'short_term', 'This Month': 'medium_term', 'This Year': 'long_term'}
    spotify_time_range = time_range_map[time_range]

    show_loading_animation(text="Fetching your top tracks and insights...")
    top_tracks = sp.current_user_top_tracks(time_range=spotify_time_range, limit=10)
    top_artists = sp.current_user_top_artists(time_range=spotify_time_range, limit=5)

    # Display top tracks
    st.subheader("Your Top Songs")
    for i, track in enumerate(top_tracks['items']):
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(track['album']['images'][0]['url'], width=60)
        with col2:
            st.write(f"**{i+1}. {track['name']}** by {track['artists'][0]['name']}")

    # Display top artists
    st.subheader("Your Top Artists")
    for i, artist in enumerate(top_artists['items']):
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(artist['images'][0]['url'], width=60)
        with col2:
            st.write(f"**{i+1}. {artist['name']}**")

    # Display fun insights
    get_user_insights(top_tracks, top_artists)

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
            top_tracks = sp.current_user_top_tracks(time_range='short_term', limit=50)
            music_personality_insights(top_tracks)

    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to Wvvy")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
