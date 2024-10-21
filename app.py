import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Spotify API credentials from Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Define the required scope for Spotify access
scope = "user-library-read user-top-read playlist-read-private user-read-recently-played"

# Initialize Spotify OAuth object
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=scope,
    cache_path=".cache"
)

# Set Streamlit page configuration
st.set_page_config(
    page_title="Wvvy",
    page_icon="〰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
    <style>
    * {
        color: white !important;
    }
    body {
        background: linear-gradient(to right, black, #1DB954) !important;
    }
    .stApp {
        background: linear-gradient(to right, black, #1DB954) !important;
    }
    .header-title {
        font-size: 5em;
        font-weight: bold;
        text-align: center;
        padding-top: 50px;
        margin-bottom: 20px;
        letter-spacing: 5px;
        color: black !important; /* Changed title color to black */
    }
    .login-button {
        color: white;
        background-color: #1DB954;
        padding: 15px 30px;
        font-size: 1.5em;
        border-radius: 12px;
        text-align: center;
        display: inline-block;
        font-weight: bold;
        margin-top: 30px;
    }
    .personality-card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .personality-color-box {
        width: 50px;
        height: 50px;
        display: inline-block;
        margin-right: 10px;
        border-radius: 50%;
    }
    .insight-box {
        background-color: #333;
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    select, .stSlider label, .stRadio label, .stButton button {
        color: black !important; /* Set filter labels to black */
    }
    </style>
""", unsafe_allow_html=True)

# Wvvy logo and title
st.markdown("<div class='header-title'>〰 Wvvy</div>", unsafe_allow_html=True)

# Function to refresh the token if expired
def refresh_token():
    token_info = st.session_state.get('token_info', None)
    if token_info and sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        st.session_state['token_info'] = token_info

# Function to check if the user is authenticated
def is_authenticated():
    if 'token_info' in st.session_state and st.session_state['token_info']:
        refresh_token()  # Ensure token is refreshed before using it
        return True
    return False

# Authentication flow
def authenticate_user():
    query_params = st.experimental_get_query_params()

    if "code" in query_params:
        code = query_params["code"][0]
        try:
            token_info = sp_oauth.get_cached_token()  # Get the cached token if available
            if not token_info:
                token_info = sp_oauth.get_access_token(code)  # Request a new token using the code
            st.session_state['token_info'] = token_info
            st.experimental_set_query_params()  # Clear query parameters after the code is processed
            st.success("You're authenticated! Click the button below to enter.")
            if st.button("Enter Wvvy"):
                st.experimental_rerun()
        except Exception as e:
            st.error(f"Authentication error: {e}")
    else:
        auth_url = sp_oauth.get_authorize_url()  # Generate authorization URL
        st.markdown(
            f'<a href="{auth_url}" class="login-button">Login with Spotify</a>',
            unsafe_allow_html=True
        )

# Helper Function for Handling Spotify API Rate Limit (429 Error)
def handle_spotify_rate_limit(sp_func, *args, max_retries=10, **kwargs):
    retries = 0
    wait_time = 1
    while retries < max_retries:
        try:
            return sp_func(*args, **kwargs)
        except spotipy.SpotifyException as e:
            if e.http_status == 429:
                retry_after = int(e.headers.get("Retry-After", wait_time)) if e.headers and "Retry-After" in e.headers else wait_time
                st.warning(f"Rate limit reached. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                retries += 1
                wait_time *= 2
            else:
                st.error(f"Error: {e}")
                break
    return None

# Fetch liked songs and audio features
def get_liked_songs(sp):
    results = handle_spotify_rate_limit(sp.current_user_saved_tracks, limit=50)
    if not results:
        return []  # Return empty list if retries exceeded
    liked_songs = []
    for item in results['items']:
        track = item['track']
        audio_features = handle_spotify_rate_limit(sp.audio_features, [track['id']])[0]
        liked_songs.append({
            "name": track['name'],
            "artist": track['artists'][0]['name'],
            "cover": track['album']['images'][0]['url'] if track['album']['images'] else None,
            "energy": audio_features["energy"],
            "valence": audio_features["valence"],
            "tempo": audio_features["tempo"],
            "popularity": track['popularity']
        })
    return liked_songs

# Display top insights
def display_top_insights(sp, time_range='short_term'):
    top_tracks = get_top_items(sp, item_type='tracks', time_range=time_range)
    top_artists = get_top_items(sp, item_type='artists', time_range=time_range)
    
    st.write(f"### Top Insights for {time_range.replace('_', ' ').title()}")

    # Display top songs with cover images
    if top_tracks:
        st.write("### Top Songs")
        for track in top_tracks:
            col1, col2 = st.columns([1, 4])
            with col1:
                st.image(track['cover'], width=80)
            with col2:
                st.write(f"**{track['name']}** by {track['artist']}")

    # Display genres explored in a pie chart (Removed artist genres)
    genres = [artist['name'] for artist in top_artists]
    display_genres_pie_chart(genres)

# Pie Chart for Genres (Reduced Size)
def display_genres_pie_chart(genre_list):
    genre_df = pd.DataFrame(genre_list, columns=["Genre"])
    genre_counts = genre_df["Genre"].value_counts()

    fig, ax = plt.subplots(figsize=(3, 3), facecolor='#000')  # Reduced pie chart size
    wedges, texts, autotexts = ax.pie(
        genre_counts, 
        labels=None,  # No labels for artists
        autopct=lambda p: '{:.0f}%'.format(p),
        colors=plt.cm.viridis(np.linspace(0, 1, len(genre_counts))),
        textprops=dict(color="white"),
        wedgeprops=dict(edgecolor='black'),
    )

    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')

    for text in autotexts:
        text.set_fontsize(8)  # Smaller percentage text
        text.set_color("white")

    st.write("### Artists You Explore (Pie Chart)")
    st.pyplot(fig)

# Analyze Time of Day Listening Pattern (Dot and Line Graph)
def analyze_time_of_day(sp):
    results = handle_spotify_rate_limit(sp.current_user_recently_played, limit=50)
    if not results:
        return None
    
    hours = [pd.to_datetime(item['played_at']).
