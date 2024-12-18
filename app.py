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

# --- Custom CSS for Styling ---
st.markdown("""
    <style>
        body {
            background: linear-gradient(to right, black, #1DB954);
            color: white;
            font-family: Arial, sans-serif;
        }
        .stApp {
            background: linear-gradient(to right, black, #1DB954);
        }
        h1 {
            font-size: 4em;
            text-align: center;
            margin-top: 50px;
            color: white;
        }
        p {
            text-align: center;
            font-size: 1.5em;
            margin: 20px 0;
        }
        .login-button {
            display: flex;
            justify-content: center;
            margin-top: 50px;
        }
        .login-button button {
            background-color: white;
            color: black;
            font-size: 1.2em;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .login-button button:hover {
            background-color: #f1f1f1;
        }
    </style>
""", unsafe_allow_html=True)

# --- Spotify Authentication ---
def authenticate_spotify():
    """
    Authenticate with Spotify and store the Spotify client in session state.
    """
    auth_manager = SpotifyOAuth(client_id=CLIENT_ID,
                                client_secret=CLIENT_SECRET,
                                redirect_uri=REDIRECT_URI,
                                scope=SCOPE)
    st.session_state["sp"] = spotipy.Spotify(auth_manager=auth_manager)
    st.session_state["authenticated"] = True

# --- Main App ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    # Landing Page
    st.markdown("<h1>MusoMoodify</h1>", unsafe_allow_html=True)
    st.markdown("<p>Discover your music and understand your mood. Explore your listening trends and connect with your favorite tracks on a deeper level.</p>", unsafe_allow_html=True)

    st.markdown('<div class="login-button"><button onclick="window.location.reload();">Log in with Spotify</button></div>', unsafe_allow_html=True)

    if st.button("Log in with Spotify", key="login"):
        authenticate_spotify()
        st.experimental_rerun()
else:
    # Redirect to the first page (currently blank)
    st.title("Welcome to MusoMoodify")
    st.write("This is the first page. Content will be added here later.")
