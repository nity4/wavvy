import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import matplotlib.pyplot as plt
import time

# Spotify API credentials stored in Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Scope to access user's liked songs and recently played tracks
SCOPE = 'user-library-read user-top-read user-read-recently-played'

# Initialize Spotify OAuth
sp_oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE)

# Streamlit App Layout - Set Dark Theme
st.set_page_config(page_title="Wavvy 〰", page_icon="〰", layout="centered", initial_sidebar_state="collapsed")

# Apply Dark Mode CSS
st.markdown(
    """
    <style>
    body {
        background-color: #1c1c1e;
        color: white;
    }
    .stButton>button {
        background-color: #ff5f6d;
        color: white;
    }
    .stImage {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True
)

# Initialize session state for token persistence
if 'token_info' not in st.session_state:
    st.session_state['token_info'] = None

# Helper function to check if the user is authenticated
def is_authenticated():
    return st.session_state['token_info'] is not None

# Helper function to check if the token is expired and refresh if needed
def refresh_token():
    if st.session_state['token_info']:
        if sp_oauth.is_token_expired(st.session_state['token_info']):
            token_info = sp_oauth.refresh_access_token(st.session_state['token_info']['refresh_token'])
            st.session_state['token_info'] = token_info

# Function to authenticate user with Spotify
def authenticate_user():
    try:
        if "code" in st.experimental_get_query_params():
            code = st.experimental_get_query_params()["code"][0]
            token_info = sp_oauth.get_access_token(code)
            st.session_state['token_info'] = token_info

            # Clear the code parameter from the URL after successful authentication
            st.experimental_set_query_params(code=None)
            
            # Notify user to refresh manually (Streamlit no longer has automatic rerun)
            st.success("Authentication successful. Please refresh the page to continue.")
            if st.button("Refresh Now"):
                st.experimental_set_query_params()  # This will reload the app
        else:
            auth_url = sp_oauth.get_authorize_url()
            st.markdown(f'<a href="{auth_url}" target="_self">Click here to authorize with Spotify</a>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Authentication error: {e}")

# Feature 1: Discover Music Based on Feelings
def discover_music_by_feelings(sp):
    try:
        st.header("Discover Music Based on Your Feelings 🎶")

        # Ask user how they're feeling and intensity
        feeling = st.selectbox("How are you feeling right now?", ["Happy", "Sad", "Calm", "Energetic"])
        intensity = st.slider(f"How {feeling} are you feeling?", 1, 10)

        # Fetch liked songs
        results = sp.current_user_saved_tracks(limit=50)
        liked_songs = results['items']

        # Filter songs based on feelings (mock filtering logic for now)
        st.write(f"Here are some {feeling.lower()} songs based on your intensity level of {intensity}:")
        for track in liked_songs[:10]:  # Display 10 liked songs
            album_cover = track['track']['album']['images'][0]['url']
            song_name = track['track']['name']
            artist_name = track['track']['artists'][0]['name']
            st.image(album_cover, width=150)
            st.write(f"🎵 **{song_name}** by *{artist_name}*")

    except Exception as e:
        st.error(f"Error fetching liked songs: {e}")

# Feature 2: Unique Data Insights
def unique_data_insights(sp):
    try:
        st.header("Your Unique Data Insights 📊")
        
        # Fetch top artists
        top_artists = sp.current_user_top_artists(limit=5)
        artist_names = [artist['name'] for artist in top_artists['items']]
        top_genres = [artist['genres'] for artist in top_artists['items']]

        st.write(f"Your top artists are:")
        for artist in artist_names:
            st.write(f"🎤 {artist}")
        
        st.write(f"Top genres you listen to:")
        for genre_list in top_genres:
            st.write(f"🎧 {', '.join(genre_list)}")
        
        # Example interesting insights:
        # Mock insights based on random data, you can replace this with more accurate ones
        st.write("Interesting insight: You seem to be exploring **new genres** lately! 🎶")

    except Exception as e:
        st.error(f"Error fetching data insights: {e}")

# Feature 3: Music Personality & Color (with tension-building)
def music_personality_analysis(sp):
    try:
        st.header("Your Music Personality & Color 🎨")
        
        # Fetch top genres and tracks
        results = sp.current_user_top_tracks(limit=50)
        top_genres = [track['album']['genres'] for track in results['items'] if 'genres' in track['album']]

        # Analyze and assign a personality type with tension-building
        if top_genres:
            st.write("Analyzing your music taste...")
            progress_bar = st.progress(0)
            for percent in range(100):
                time.sleep(0.03)
                progress_bar.progress(percent + 1)

            personality_type, color = assign_personality_and_color(top_genres)
            st.write(f"**Your personality type is:** *{personality_type}*")
            st.write(f"**Your associated color is:** *{color}*")
        else:
            st.write("Not enough data to determine your personality.")
    except Exception as e:
        st.error(f"Error analyzing your music personality: {e}")

# Function to assign a personality type and color based on top genres
def assign_personality_and_color(genres):
    if "rock" in genres:
        return "Adventurer", "Red"
    elif "pop" in genres:
        return "Trendsetter", "Yellow"
    elif "jazz" in genres:
        return "Calm", "Blue"
    else:
        return "Explorer", "Green"

# Feature 4: Daily Listening Insights (more engaging insights)
def daily_music_insights(sp):
    try:
        st.header("Your Daily Music Insights 📅")
        
        # Fetch recently played tracks
        results = sp.current_user_recently_played(limit=10)
        recent_tracks = results['items']
        
        st.write("Here’s what your recent listening says about you:")
        total_tracks = len(recent_tracks)
        listening_time = total_tracks * 3  # Assume each song is 3 minutes, as an example

        st.write(f"🎶 You've listened to **{total_tracks} tracks** today, totaling about **{listening_time} minutes**.")
        
        st.write("Some of your recent listens:")
        for track in recent_tracks[:5]:
            song_name = track['track']['name']
            album_cover = track['track']['album']['images'][0]['url']
            artist_name = track['track']['artists'][0]['name']
            st.image(album_cover, width=100)
            st.write(f"🎧 **{song_name}** by *{artist_name}*")
        
        # Provide an interesting insight based on listening habits
        st.write("Insight: You've been branching out and exploring new music lately! 🎧")
    except Exception as e:
        st.error(f"Error fetching daily insights: {e}")

# Main Flow of the App
if is_authenticated():
    try:
        refresh_token()  # Refresh the token if expired
        sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

        # Main navigation
        section = st.radio("Explore your music journey", [
            "Discover Music Based on Feelings", 
            "Unique Data Insights", 
            "Music Personality & Color", 
            "Daily Listening Insights"
        ])

        if section == "Discover Music Based on Feelings":
            discover_music_by_feelings(sp)
        elif section == "Unique Data Insights":
            unique_data_insights(sp)
        elif section == "Music Personality & Color":
            music_personality_analysis(sp)
        elif section == "Daily Listening Insights":
            daily_music_insights(sp)

    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to **Wavvy** 〰")
    st.write("Wavvy offers you a personal reflection on your emotional and personality-driven journey through music.")
    authenticate_user()
