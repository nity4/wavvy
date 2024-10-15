import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Spotify API credentials from Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Define the required scope for Spotify access
scope = "user-library-read user-top-read"

# Initialize Spotify OAuth object
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=scope,
    cache_path=".cache"  # Optional: Specify a cache path
)

# Set Streamlit page configuration
st.set_page_config(
    page_title="Wvvy",
    page_icon="〰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling to apply black and green gradient to the entire app and make all text white
st.markdown("""
    <style>
    /* Set background to black and green gradient */
    body {
        background: linear-gradient(to right, black, #1DB954) !important;
    }

    /* Apply the gradient background to the main container and sidebar */
    .stApp {
        background: linear-gradient(to right, black, #1DB954) !important;
    }

    /* Make all text white */
    h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown, .success, .error, .warning {
        color: white !important;  /* Force all text to be white */
    }

    /* Customize the Wvvy header text */
    .header-title {
        font-size: 5em; /* Larger font size */
        font-weight: bold;
        color: white !important;
        text-align: center;
        padding-top: 50px;
        margin-bottom: 20px;
        letter-spacing: 5px; /* Adds spacing between letters for style */
    }

    /* Style for the login button */
    .login-button {
        color: white;
        background-color: #1DB954;  /* Spotify Green */
        padding: 15px 30px;  /* Larger padding for a bigger button */
        font-size: 1.5em;  /* Larger font size for the button */
        border-radius: 12px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-weight: bold;
        margin-top: 30px;
    }

    .main {
        font-family: 'Courier New', Courier, monospace;
    }
    </style>
""", unsafe_allow_html=True)

# Larger Wvvy logo and text
st.markdown("<div class='header-title'>〰 Wvvy</div>", unsafe_allow_html=True)

# Authentication Functions
def is_authenticated():
    return 'token_info' in st.session_state and st.session_state['token_info'] is not None

def refresh_token():
    if 'token_info' in st.session_state and sp_oauth.is_token_expired(st.session_state['token_info']):
        token_info = sp_oauth.refresh_access_token(st.session_state['token_info']['refresh_token'])
        st.session_state['token_info'] = token_info

def authenticate_user():
    query_params = st.experimental_get_query_params()  # Fetch query params
    
    if "code" in query_params:
        code = query_params["code"][0]  # Get the auth code from the query parameters
        try:
            token_info = sp_oauth.get_access_token(code)
            st.session_state['token_info'] = token_info
            st.experimental_set_query_params()  # Clear the query params to avoid loop
            st.success("You're authenticated! Click the button below to enter.")
            if st.button("Enter Wvvy"):
                st.experimental_rerun()  # Reload the app to load the user's data
        except Exception as e:
            st.error(f"Authentication error: {e}")
    else:
        auth_url = sp_oauth.get_authorize_url()
        # Directly display the Spotify login URL button within the same tab
        st.markdown(
            f'<a href="{auth_url}" class="login-button">Login with Spotify</a>',
            unsafe_allow_html=True
        )

# Main app logic
if is_authenticated():
    try:
        refresh_token()
        st.success("You are logged in! Your Spotify data is ready for analysis.")
        st.write("Future content like insights, graphs, and data visualizations will be displayed here.")

    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to Wvvy")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
