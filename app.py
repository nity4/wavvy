import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd

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
        .stTextInput > div > div > input {
            background-color: #222222;
            color: white;
            border-radius: 5px;
            border: 1px solid #1DB954;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Spotify Authentication Function ---
def authenticate_spotify():
    """Authenticate Spotify and reload the current page after success."""
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        open_browser=False
    )
    if not st.session_state.get("token_info"):
        token_info = auth_manager.get_access_token(as_dict=False)
        if token_info:
            st.session_state["token_info"] = token_info
            st.session_state["authenticated"] = True
            st.experimental_rerun()  # Reload the app page after authentication

# --- Fetch Liked Songs ---
def fetch_liked_songs(sp):
    """Fetch user's liked songs."""
    results = sp.current_user_saved_tracks(limit=50)
    songs = [
        {
            "Name": item["track"]["name"],
            "Artist": ", ".join([artist["name"] for artist in item["track"]["artists"]])
        }
        for item in results["items"]
    ]
    return pd.DataFrame(songs)

# --- Main App ---
def main():
    st.markdown("<h1>🎼 MusoMoodify 🎼</h1>", unsafe_allow_html=True)

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.warning("Please authenticate with Spotify to continue.")
        if st.button("Log in with Spotify"):
            authenticate_spotify()
    else:
        st.success("✅ Successfully connected to Spotify!")
        sp = spotipy.Spotify(auth=st.session_state["token_info"])
        liked_songs_df = fetch_liked_songs(sp)

        if not liked_songs_df.empty:
            st.success("🎵 Here are your liked songs:")
            st.dataframe(liked_songs_df)
        else:
            st.warning("No liked songs found!")

# Run the app
if __name__ == "__main__":
    main()
