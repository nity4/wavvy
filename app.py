import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import time

# --- Spotify API Credentials ---
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]
SCOPE = "user-library-read"

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="MusoMoodify 🎼", page_icon="🎼", layout="wide")

# --- Custom CSS for Improved Visuals ---
st.markdown(
    """
    <style>
        body, .stApp {
            background: linear-gradient(to bottom right, black, #1DB954);
            color: white;
        }
        h1, h2, h3, h4, h5, h6 {
            color: white;
            text-align: center;
        }
        .stButton > button {
            background-color: #1DB954;
            color: black;
            font-size: 1em;
            font-weight: bold;
            border-radius: 10px;
            padding: 10px 20px;
            border: none;
        }
        .stButton > button:hover {
            background-color: #1ed760;
            color: black;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Spotify Authentication ---
def authenticate_spotify():
    """Authenticate Spotify and store token in session."""
    if "token_info" not in st.session_state or st.session_state["token_info"] is None:
        auth_manager = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            open_browser=False
        )
        if not auth_manager.get_cached_token():
            auth_url = auth_manager.get_authorize_url()
            st.info("Please log in to Spotify:")
            st.markdown(f"[Login here]({auth_url})", unsafe_allow_html=True)
        else:
            token_info = auth_manager.get_access_token()
            st.session_state["token_info"] = token_info
            st.experimental_rerun()
    else:
        # Refresh token if expired
        token_info = st.session_state["token_info"]
        if time.time() > token_info["expires_at"]:
            auth_manager = SpotifyOAuth(
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                redirect_uri=REDIRECT_URI,
                scope=SCOPE,
                open_browser=False
            )
            token_info = auth_manager.refresh_access_token(token_info["refresh_token"])
            st.session_state["token_info"] = token_info

# --- Fetch Liked Songs ---
def fetch_liked_songs():
    """Fetch user's liked songs."""
    sp = spotipy.Spotify(auth=st.session_state["token_info"]["access_token"])
    results = sp.current_user_saved_tracks(limit=50)
    songs = [
        {
            "Name": item["track"]["name"],
            "Artist": ", ".join([artist["name"] for artist in item["track"]["artists"]]),
        }
        for item in results["items"]
    ]
    return pd.DataFrame(songs)

# --- Main App ---
def main():
    st.markdown("<h1>🎼 MusoMoodify 🎼</h1>", unsafe_allow_html=True)

    # Step 1: Authenticate
    if "token_info" not in st.session_state or st.session_state["token_info"] is None:
        st.warning("Please authenticate with Spotify to continue.")
        authenticate_spotify()
    else:
        st.success("✅ Successfully connected to Spotify!")
        
        # Step 2: Fetch and display liked songs
        try:
            liked_songs_df = fetch_liked_songs()
            if not liked_songs_df.empty:
                st.success("🎵 Here are your liked songs:")
                st.dataframe(liked_songs_df)
            else:
                st.warning("No liked songs found!")
        except Exception as e:
            st.error(f"Error fetching liked songs: {e}")
            st.session_state["token_info"] = None

if __name__ == "__main__":
    main()
