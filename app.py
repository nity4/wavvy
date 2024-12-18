import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# --- Spotify API Credentials ---
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]
SCOPE = "user-library-read user-top-read playlist-read-private user-read-recently-played"

# --- Streamlit Page Config ---
st.set_page_config(page_title="MusoMoodify 🎼", page_icon="🎼", layout="wide")

# --- Custom CSS ---
st.markdown("""
    <style>
        body {
            background: linear-gradient(to right, black, #1DB954);
            font-family: Arial, sans-serif;
        }
        .stApp {
            background: linear-gradient(to right, black, #1DB954);
        }
        .container {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            justify-content: center;
            height: 100vh;
            padding-left: 50px;
        }
        h1 {
            font-size: 4em;
            margin-bottom: 20px;
            color: white;
        }
        p {
            font-size: 1.5em;
            color: white;
            margin-bottom: 30px;
        }
        .spotify-button {
            background-color: white;
            color: black;
            font-size: 1.2em;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        .spotify-button:hover {
            background-color: #e6e6e6;
        }
    </style>
""", unsafe_allow_html=True)

# --- Spotify Authentication ---
def authenticate_spotify():
    """
    Handles Spotify OAuth flow and stores the Spotify client.
    """
    try:
        auth_manager = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE
        )
        st.session_state["sp"] = spotipy.Spotify(auth_manager=auth_manager)
        st.session_state["authenticated"] = True
        st.experimental_rerun()  # Reload the app to proceed
    except Exception as e:
        st.error(f"Spotify Authentication failed: {e}")

# --- Main App Logic ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    # Landing Page
    st.markdown("""
        <div class="container">
            <h1>MusoMoodify</h1>
            <p>Discover your music and understand your mood. Explore your listening trends and connect with your favorite tracks on a deeper level.</p>
            <button class="spotify-button" onclick="window.location.reload()">Log in with Spotify</button>
        </div>
    """, unsafe_allow_html=True)

    if st.button("Log in with Spotify"):
        authenticate_spotify()

else:
    # First Page (Post-Authentication)
    st.title("Welcome to MusoMoodify 🎶")
    st.write("You are successfully authenticated with Spotify!")
    st.write("This is the first page where we’ll implement mood-based song filtering.")
