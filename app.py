import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import matplotlib.pyplot as plt

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

# Feature 1: Personality-Based Recommendations from Liked Songs
def personality_based_recommendations(sp):
    try:
        st.header("Discover Music Based on Your Personality 🎧")
        
        # Fetch liked songs
        results = sp.current_user_saved_tracks(limit=50)
        liked_songs = [track['track']['name'] for track in results['items']]
        
        st.write("Here are some recommendations from your liked songs:")
        for song in liked_songs[:10]:  # Display 10 liked songs
            st.write(f"🎵 {song}")

    except Exception as e:
        st.error(f"Error fetching liked songs: {e}")

# Feature 2: Scenario-Based Recommendations from Liked Songs
def scenario_based_recommendations(sp):
    try:
        st.header("Find Songs for Your Current Mood or Scenario 🎭")
        
        # Get user input for the scenario
        scenario = st.text_input("Describe your current scenario (e.g., breakup, calm, studying):")
        
        if scenario:
            # Fetch liked songs (you can add more sophisticated filtering based on song features)
            results = sp.current_user_saved_tracks(limit=50)
            liked_songs = [track['track']['name'] for track in results['items']]
            
            st.write(f"Here are some songs from your liked tracks that might fit your mood ({scenario}):")
            for song in liked_songs[:10]:  # You can customize this recommendation logic
                st.write(f"🎧 {song}")
    except Exception as e:
        st.error(f"Error fetching scenario-based recommendations: {e}")

# Feature 3: Music Personality Analysis
def music_personality_analysis(sp):
    try:
        st.header("Your Music Personality & Color 🎨")
        
        # Fetch liked songs
        results = sp.current_user_top_tracks(limit=50)
        top_genres = [track['album']['genres'] for track in results['items'] if 'genres' in track['album']]

        # Analyze and assign a personality type
        if top_genres:
            personality_type = "Adventurer" if "rock" in top_genres else "Calm"
            color = "Blue" if personality_type == "Calm" else "Red"
            
            st.write(f"Your personality type is: **{personality_type}**")
            st.write(f"Your associated color is: **{color}**")
        else:
            st.write("Not enough data to determine your personality.")
    except Exception as e:
        st.error(f"Error analyzing your music personality: {e}")

# Feature 4: Daily Insights Based on Recent Songs
def daily_music_insights(sp):
    try:
        st.header("Your Daily Music Insights 📅")
        
        # Fetch recently played tracks
        results = sp.current_user_recently_played(limit=10)
        recent_tracks = [track['track']['name'] for track in results['items']]
        
        st.write("Here’s what your recent listening says about you:")
        for track in recent_tracks:
            st.write(f"🎶 You listened to: {track}")
        
        st.write("Based on your recent listening habits, you're feeling energetic and upbeat today!")
    except Exception as e:
        st.error(f"Error fetching daily insights: {e}")

# Main Flow of the App
if is_authenticated():
    try:
        refresh_token()  # Refresh the token if expired
        sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

        # Main navigation
        section = st.radio("Explore your music journey", [
            "Personality-Based Recommendations", 
            "Scenario-Based Recommendations", 
            "Music Personality Analysis", 
            "Daily Insights"
        ])

        if section == "Personality-Based Recommendations":
            personality_based_recommendations(sp)
        elif section == "Scenario-Based Recommendations":
            scenario_based_recommendations(sp)
        elif section == "Music Personality Analysis":
            music_personality_analysis(sp)
        elif section == "Daily Insights":
            daily_music_insights(sp)

    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to **Wavvy** 〰")
    st.write("Wavvy offers you a personal reflection on your emotional and personality-driven journey through music.")
    authenticate_user()
