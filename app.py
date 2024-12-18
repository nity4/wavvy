import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# --- Spotify API Credentials ---
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]
SCOPE = "user-library-read"

st.title("Spotify OAuth Test")

if "sp" not in st.session_state:
    st.warning("Click below to authenticate with Spotify.")
    if st.button("Log in to Spotify"):
        st.session_state["sp"] = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            show_dialog=True,
            open_browser=True
        ))
        st.success("Connected to Spotify!")
else:
    st.success("Already authenticated with Spotify!")
    sp = st.session_state["sp"]
    st.write("Fetching your profile...")
    user_profile = sp.me()
    st.write(f"Hello, {user_profile['display_name']}!")
