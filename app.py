import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd

# --- Spotify API Credentials ---
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]
SCOPE = "user-library-read playlist-modify-private user-read-recently-played"

# --- Streamlit Page Config ---
st.set_page_config(page_title="MusoMoodify 🎼", page_icon="🎼", layout="wide")

# --- Custom CSS for Background and Text Styling ---
st.markdown("""
    <style>
        body, .stApp {
            background: linear-gradient(to right, black, #1DB954);
            color: white;
        }
        .header-container {
            margin-top: 20px;
            padding-left: 20px;
        }
        h1 {
            font-size: 4em;
            margin-bottom: 10px;
            color: white;
        }
        p {
            font-size: 1.3em;
            margin-bottom: 30px;
            color: white;
        }
        .spotify-button {
            background-color: white;
            color: black;
            font-size: 1.1em;
            padding: 10px 20px;
            border-radius: 5px;
            border: none;
            cursor: pointer;
            transition: 0.3s;
        }
        .spotify-button:hover {
            background-color: #f1f1f1;
        }
    </style>
""", unsafe_allow_html=True)

# --- Spotify Authentication ---
def authenticate_spotify():
    if "sp" not in st.session_state:
        auth_manager = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE
        )
        st.session_state["sp"] = spotipy.Spotify(auth_manager=auth_manager)
        st.session_state["authenticated"] = True

# --- Fetch Liked Songs with Error Handling ---
def fetch_liked_songs(sp):
    try:
        with st.spinner("Fetching your liked songs..."):
            results = sp.current_user_saved_tracks(limit=50)
            songs = []
            for item in results["items"]:
                track = item["track"]
                features = sp.audio_features(track["id"])[0]
                songs.append({
                    "name": track["name"],
                    "artist": ", ".join(artist["name"] for artist in track["artists"]),
                    "id": track["id"],
                    "image": track["album"]["images"][0]["url"],
                    "valence": features["valence"],
                    "energy": features["energy"]
                })
            return pd.DataFrame(songs)
    except Exception as e:
        st.error(f"Error fetching songs: {e}")
        return pd.DataFrame()

# --- Main App Logic ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

authenticate_spotify()

# Landing Page
if not st.session_state["authenticated"]:
    st.markdown("""
        <div class="header-container">
            <h1>MusoMoodify</h1>
            <p>Discover your music and understand your mood. Explore your listening trends and connect with your favorite tracks on a deeper level.</p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("Log in with Spotify", help="Authenticate with Spotify"):
        authenticate_spotify()
else:
    # Page 1: Liked Songs with Mood and Intensity Filters
    st.title("Page 1: Liked Songs with Mood and Intensity Filters 🎼")

    sp = st.session_state["sp"]
    liked_songs = fetch_liked_songs(sp)

    if not liked_songs.empty:
        st.write("Here are your liked songs:")
        st.dataframe(liked_songs[["name", "artist", "valence", "energy"]])
    else:
        st.warning("No songs found. Please try again later.")
