import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Spotify API credentials from Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Define the required scope for Spotify access
scope = "user-library-read user-top-read playlist-read-private"

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

# Custom CSS styling
st.markdown("""
    <style>
    body {
        background: linear-gradient(to right, black, #1DB954) !important;
    }
    .stApp {
        background: linear-gradient(to right, black, #1DB954) !important;
    }
    h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown, .success, .error, .warning {
        color: white !important;
    }
    .header-title {
        font-size: 5em;
        font-weight: bold;
        color: white !important;
        text-align: center;
        padding-top: 50px;
        margin-bottom: 20px;
        letter-spacing: 5px;
    }
    .login-button {
        color: white;
        background-color: #1DB954;
        padding: 15px 30px;
        font-size: 1.5em;
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
    .stSelectbox, .stSlider {
        color: black !important;  /* Black text for the mood options */
    }
    </style>
""", unsafe_allow_html=True)

# Wvvy logo and title
st.markdown("<div class='header-title'>〰 Wvvy</div>", unsafe_allow_html=True)

# Authentication Functions
def is_authenticated():
    return 'token_info' in st.session_state and st.session_state['token_info'] is not None

def refresh_token():
    if 'token_info' in st.session_state and sp_oauth.is_token_expired(st.session_state['token_info']):
        token_info = sp_oauth.refresh_access_token(st.session_state['token_info']['refresh_token'])
        st.session_state['token_info'] = token_info

def authenticate_user():
    query_params = st.experimental_get_query_params()
    
    if "code" in query_params:
        code = query_params["code"][0]
        try:
            token_info = sp_oauth.get_access_token(code)
            st.session_state['token_info'] = token_info
            st.experimental_set_query_params()
            st.success("You're authenticated! Click the button below to enter.")
            if st.button("Enter Wvvy"):
                st.experimental_rerun()
        except Exception as e:
            st.error(f"Authentication error: {e}")
    else:
        auth_url = sp_oauth.get_authorize_url()
        st.markdown(
            f'<a href="{auth_url}" class="login-button">Login with Spotify</a>',
            unsafe_allow_html=True
        )

# Function to retrieve liked songs
def get_liked_songs(sp):
    results = sp.current_user_saved_tracks(limit=50)
    liked_songs = []
    for item in results['items']:
        track = item['track']
        liked_songs.append({
            "name": track['name'],
            "artist": track['artists'][0]['name'],
            "cover": track['album']['images'][0]['url'] if track['album']['images'] else None,
            "energy": random.uniform(0, 1),  # Simulate energy feature (0-1)
            "valence": random.uniform(0, 1)  # Simulate valence feature (0-1)
        })
    return liked_songs

# Function to retrieve new song recommendations
def get_new_discoveries(sp):
    recommendations = sp.recommendations(seed_genres=["pop", "rock", "hip-hop"], limit=50)
    new_songs = []
    for track in recommendations['tracks']:
        new_songs.append({
            "name": track['name'],
            "artist": track['artists'][0]['name'],
            "cover": track['album']['images'][0]['url'] if track['album']['images'] else None,
            "energy": random.uniform(0, 1),  # Simulate energy feature (0-1)
            "valence": random.uniform(0, 1)  # Simulate valence feature (0-1)
        })
    return new_songs

# Function to filter songs based on mood and intensity
def filter_songs(songs, mood, intensity):
    mood_ranges = {
        "Happy": (0.7, 1),
        "Calm": (0.3, 0.6),
        "Energetic": (0.6, 1),
        "Sad": (0, 0.3)
    }
    
    mood_range = mood_ranges[mood]
    filtered_songs = [song for song in songs if mood_range[0] <= song['valence'] <= mood_range[1] and song['energy'] >= (intensity / 10)]
    
    return filtered_songs

# Function to display songs with their cover images
def display_songs(song_list, title):
    st.write(f"### {title}")
    if song_list:
        for song in song_list:
            col1, col2 = st.columns([1, 4])
            with col1:
                if song["cover"]:
                    st.image(song["cover"], width=80)
                else:
                    st.write("No cover")
            with col2:
                st.write(f"**{song['name']}** by {song['artist']}")
    else:
        st.write("No songs found.")

# Main app logic
if is_authenticated():
    try:
        refresh_token()
        st.success("You are logged in! Your Spotify data is ready for analysis.")
        
        sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])
        
        # Mood and Intensity filters
        mood = st.selectbox("Choose your mood:", ["Happy", "Calm", "Energetic", "Sad"])
        intensity = st.slider("Choose intensity:", 1, 10, 5)
        
        # Tabs for liked songs and new discoveries
        tab1, tab2 = st.tabs(["Liked Songs", "New Discoveries"])

        with tab1:
            liked_songs = get_liked_songs(sp)
            filtered_liked_songs = filter_songs(liked_songs, mood, intensity)
            display_songs(filtered_liked_songs, "Your Liked Songs")

        with tab2:
            new_songs = get_new_discoveries(sp)
            filtered_new_songs = filter_songs(new_songs, mood, intensity)
            display_songs(filtered_new_songs, "New Song Discoveries")
        
    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to Wvvy")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
