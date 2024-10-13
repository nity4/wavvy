import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import matplotlib.pyplot as plt

# Spotify API credentials stored in Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Scope to access user's top tracks and recently played
SCOPE = 'user-top-read user-read-recently-played'

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

# Check if the user is authenticated
def is_authenticated():
    return st.session_state['token_info'] is not None

# Handle Spotify Authentication
def authenticate_user():
    # Check if code is present in query params
    if "code" in st.experimental_get_query_params():
        code = st.experimental_get_query_params()["code"][0]
        token_info = sp_oauth.get_access_token(code)
        st.session_state['token_info'] = token_info
        st.experimental_rerun()  # Ensure the app is refreshed after receiving the token
    else:
        auth_url = sp_oauth.get_authorize_url()
        st.markdown(f'<a href="{auth_url}" target="_self">Click here to authorize with Spotify</a>', unsafe_allow_html=True)

# Main Flow of the App
if is_authenticated():
    sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

    # Main navigation
    section = st.radio("Explore your music journey", [
        "Personality-Based Recommendations", 
        "Predictive Soundtrack", 
        "Music Archetypes", 
        "Social Connectivity", 
        "Music Journaling", 
        "Wellness Insights"
    ])

    if section == "Personality-Based Recommendations":
        personality_based_recommendations(sp)
    elif section == "Predictive Soundtrack":
        predictive_recommendations()
    elif section == "Music Archetypes":
        music_archetypes()
    elif section == "Social Connectivity":
        social_connectivity(sp)
    elif section == "Music Journaling":
        music_journaling()
    elif section == "Wellness Insights":
        musical_wellness()

else:
    st.write("Welcome to **Wavvy** 〰")
    st.write("Wavvy offers you a personal reflection on your emotional and personality-driven journey through music.")
    authenticate_user()

