import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd

# --- Spotify API Credentials ---
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]
SCOPE = "user-library-read user-read-recently-played playlist-modify-private"

# --- Streamlit Page Config ---
st.set_page_config(page_title="MusoMoodify 🎼", page_icon="🎼", layout="wide")

# --- Spotify Authentication ---
def authenticate_spotify():
    """
    Authenticate with Spotify and store the Spotify client in session state.
    """
    try:
        auth_manager = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
        )
        st.session_state["sp"] = spotipy.Spotify(auth_manager=auth_manager)
        st.session_state["authenticated"] = True
        st.success("Spotify Authentication Successful!")
    except Exception as e:
        st.error(f"Spotify Authentication failed: {e}")
        st.stop()

# --- Fetch Liked Songs ---
def fetch_liked_songs(sp):
    """
    Fetch user's liked songs and display them.
    """
    try:
        st.write("Fetching liked songs...")
        results = sp.current_user_saved_tracks(limit=10)
        st.success("Successfully fetched liked songs!")
        songs = []
        for item in results["items"]:
            track = item["track"]
            songs.append({
                "name": track["name"],
                "artist": ", ".join(artist["name"] for artist in track["artists"]),
                "album": track["album"]["name"]
            })
        return pd.DataFrame(songs)
    except Exception as e:
        st.error(f"Error fetching liked songs: {e}")
        return pd.DataFrame()

# --- Main App ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

st.title("MusoMoodify 🎼")
st.subheader("Discover your music and explore your moods!")

# Spotify Login
if not st.session_state["authenticated"]:
    if st.button("Log in with Spotify"):
        authenticate_spotify()

else:
    # Debug: Check current user
    st.write("✅ You are authenticated with Spotify!")
    try:
        sp = st.session_state["sp"]
        user = sp.current_user()
        st.write(f"Welcome, **{user['display_name']}** 👋")
    except Exception as e:
        st.error(f"Failed to fetch user details: {e}")
        st.stop()

    # Fetch Liked Songs
    liked_songs_df = fetch_liked_songs(sp)
    if not liked_songs_df.empty:
        st.dataframe(liked_songs_df)
    else:
        st.warning("No liked songs found.")
