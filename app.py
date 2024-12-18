import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# --- Spotify API Credentials ---
CLIENT_ID = st.secrets["spotify"]["client_id"]  # Replace in secrets.toml
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]  # Replace in secrets.toml
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]  # Replace in secrets.toml
SCOPE = "user-library-read user-top-read playlist-read-private user-read-recently-played"

# --- Streamlit Page Config ---
st.set_page_config(page_title="MusoMood - Authentication", page_icon="🎼", layout="centered")

# --- Spotify OAuth Login ---
def authenticate_spotify():
    """
    Handles Spotify Authentication and stores the Spotify client in session state.
    """
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        show_dialog=True
    )
    try:
        st.session_state["sp"] = spotipy.Spotify(auth_manager=auth_manager)
        st.session_state["logged_in"] = True
        user_info = st.session_state["sp"].current_user()
        st.session_state["user_name"] = user_info["display_name"]
        st.success(f"Welcome, {user_info['display_name']}!")
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        st.stop()

# --- Main App ---
st.title("MusoMood 🎼")
st.subheader("Discover Your Music. Understand Your Mood.")
st.write("To continue, please log in with Spotify to access your data.")

# Authentication Section
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.info("You need to log in to access your Spotify data.")
    if st.button("Log in with Spotify"):
        authenticate_spotify()
else:
    # Show logged-in user message
    st.success(f"Logged in as {st.session_state['user_name']}")
    st.write("You are now authenticated. You can proceed to explore your data.")

    # Logout Button
    if st.button("Log Out"):
        st.session_state.clear()
        st.info("You have been logged out. Please refresh the page.")
