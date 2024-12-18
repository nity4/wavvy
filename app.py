import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import time

# --- Spotify API Credentials (Using Streamlit Secrets) ---
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]
SCOPE = "user-library-read playlist-modify-private user-read-recently-played"

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="MusoMoodify 🎼", page_icon="🎼", layout="wide")

# --- Spotify Authentication ---
def authenticate_spotify():
    """Authenticate and initialize Spotify client."""
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
        st.error(f"Authentication Error: {e}")

# --- Fetch Liked Songs with Retry Logic ---
def fetch_liked_songs(sp):
    """Fetch liked songs and their audio features."""
    try:
        with st.spinner("Fetching your liked songs... 🎶"):
            results = sp.current_user_saved_tracks(limit=50)
            songs = []

            for item in results["items"]:
                track = item["track"]
                features = sp.audio_features(track["id"])
                if features and features[0]:  # Ensure features are not None
                    songs.append({
                        "Name": track["name"],
                        "Artist": ", ".join([artist["name"] for artist in track["artists"]]),
                        "Valence": features[0]["valence"],
                        "Energy": features[0]["energy"],
                        "ID": track["id"]
                    })
                time.sleep(0.1)  # Prevent hitting API rate limits

            return pd.DataFrame(songs)
    except Exception as e:
        st.error(f"Error fetching songs: {e}")
        return pd.DataFrame()

# --- Main Streamlit App Logic ---
def main():
    st.markdown(
        "<h1 style='text-align: center; color: white;'>🎼 MusoMoodify 🎼</h1>",
        unsafe_allow_html=True
    )

    # Initialize authentication state
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # Authenticate Spotify
    if not st.session_state["authenticated"]:
        st.warning("Please log in with Spotify to continue.")
        if st.button("Log in with Spotify", help="Authenticate with your Spotify account"):
            authenticate_spotify()
    else:
        # Display the liked songs
        sp = st.session_state["sp"]
        liked_songs_df = fetch_liked_songs(sp)

        if not liked_songs_df.empty:
            st.success("Here are your liked songs with mood and intensity data:")
            st.dataframe(liked_songs_df)
        else:
            st.warning("No liked songs found. Add some songs to your library!")

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

# Run the main app
if __name__ == "__main__":
    main()
