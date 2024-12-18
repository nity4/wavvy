import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Spotify API credentials
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]
SCOPE = "user-library-read"  # Simplified for testing

# Spotify Authentication Function
def authenticate_spotify():
    """Authenticate and initialize Spotify client."""
    try:
        auth_manager = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            show_dialog=True,  # Forces the Spotify login dialog
            open_browser=True  # Opens a browser window for authentication
        )
        st.session_state["sp"] = spotipy.Spotify(auth_manager=auth_manager)
        st.session_state["authenticated"] = True
        st.success("Successfully connected to Spotify! 🎉")
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        st.stop()
