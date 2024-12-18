import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import time

# --- Spotify API Credentials ---
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]
SCOPE = "user-library-read playlist-modify-private user-read-recently-played"

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="MusoMoodify 🎼", page_icon="🎼", layout="wide")

# --- Spotify Authentication ---
def authenticate_spotify():
    """Authenticate Spotify and initialize the client."""
    try:
        auth_manager = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        st.session_state["sp"] = sp
        st.session_state["authenticated"] = True
        st.success("Successfully connected to Spotify! 🎉")
    except Exception as e:
        st.error(f"Error during authentication: {e}")
        st.stop()

# --- Fetch Liked Songs with Timeout Handling ---
def fetch_liked_songs(sp, timeout=10):
    """Fetch user's liked songs with error handling and timeout."""
    start_time = time.time()
    songs = []

    try:
        with st.spinner("Fetching your liked songs... 🎶"):
            results = sp.current_user_saved_tracks(limit=50)
            for item in results["items"]:
                if time.time() - start_time > timeout:  # Timeout check
                    st.error("Fetching songs timed out. Please try again later.")
                    return pd.DataFrame()

                track = item["track"]
                features = sp.audio_features(track["id"])
                
                if features and features[0]:  # Ensure features are valid
                    songs.append({
                        "Name": track["name"],
                        "Artist": ", ".join([artist["name"] for artist in track["artists"]]),
                        "Valence": features[0]["valence"],
                        "Energy": features[0]["energy"],
                        "ID": track["id"]
                    })
                else:
                    st.warning(f"Skipping track: {track['name']} (no audio features)")

                time.sleep(0.1)  # Avoid hitting Spotify API rate limits

        return pd.DataFrame(songs)

    except Exception as e:
        st.error(f"Error fetching liked songs: {e}")
        return pd.DataFrame()

# --- Main Streamlit App Logic ---
def main():
    st.markdown(
        "<h1 style='text-align: center; color: white;'>🎼 MusoMoodify 🎼</h1>",
        unsafe_allow_html=True
    )

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.warning("Please log in with Spotify to continue.")
        if st.button("Log in with Spotify", help="Authenticate with Spotify"):
            authenticate_spotify()
    else:
        sp = st.session_state["sp"]
        st.info("Fetching your liked songs from Spotify...")
        liked_songs_df = fetch_liked_songs(sp)

        if not liked_songs_df.empty:
            st.success("Here are your liked songs with mood and intensity:")
            st.dataframe(liked_songs_df)
        else:
            st.warning("No songs found or failed to fetch songs. Try again later.")

# --- Custom CSS ---
st.markdown("""
    <style>
        body, .stApp {
            background: linear-gradient(to bottom right, black, #1DB954);
            color: white;
        }
        .stButton > button {
            background-color: #1DB954;
            color: white;
            border-radius: 5px;
        }
        .stButton > button:hover {
            background-color: #1ed760;
        }
    </style>
""", unsafe_allow_html=True)

# --- Run Main App ---
if __name__ == "__main__":
    main()
