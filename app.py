import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import time
import matplotlib.pyplot as plt

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
    cache_path=".cache"
)

# Set Streamlit page configuration
st.set_page_config(
    page_title="Wvvy",
    page_icon="〰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling white text, and other elements
st.markdown("""
    <style>
    body {
        background: linear-gradient(to right, black, #1DB954) !important;
    }
    .stApp {
        background: linear-gradient(to right, black, #1DB954) !important;
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
    .personality-box {
        background-color: #1DB954;
        color: white;
        padding: 20px;
        margin-bottom: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        font-size: 1.2em;
        font-family: 'Arial', sans-serif;
    }
    .insight-box {
        background-color: #333;
        color: white;
        padding: 20px;
        margin-bottom: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        font-size: 1.2em;
        font-family: 'Arial', sans-serif;
    }
    .insight-quote {
        font-style: italic;
        color: #1DB954;
        font-size: 1.5em;
    }
    .stMarkdown, .stMarkdown p, .stMarkdown h3, .stSelectbox label, .stSlider label {
        color: white !important;
    }
    .personality-color-box {
        width: 60px;
        height: 60px;
        display: inline-block;
        border-radius: 50%;
        margin-right: 20px;
        border: 2px solid white;
    }
    .song-stats-box {
        background-color: #333;
        padding: 15px;
        border-radius: 10px;
        margin-top: 20px;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Authentication Functions
def is_authenticated():
    return 'token_info' in st.session_state and st.session_state['token_info'] is not None

# Behavior insights function to analyze listening patterns
def analyze_behavioral_insights():
    hour = random.randint(0, 23)  # Simulating time of listening
    if 6 <= hour <= 11:
        return "Morning Listener", "You start your day with music. It's like your daily dose of energy!"
    elif 12 <= hour <= 17:
        return "Daytime Groover", "You keep the music going throughout your day, staying productive and energized."
    elif 18 <= hour <= 23:
        return "Night Owl", "Late-night jams are your vibe. Music hits different after dark!"
    else:
        return "Late-Night Crawler", "You're listening past midnight, discovering the best hidden tracks!"

# Function to determine listening personality type (depth vs breadth)
def analyze_listening_behavior():
    avg_songs_per_artist = random.randint(20, 50)  # Simulated behavior analysis
    total_artists = random.randint(40, 100)  # Simulated total artist count

    if avg_songs_per_artist > 30:
        return "Deep Diver", "blue", "You're all about depth—diving deep into a few artists and their entire discographies."
    elif total_artists > 40:
        return "Explorer", "green", "You're a breadth explorer, constantly seeking new artists and sounds."
    else:
        return "Balanced Listener", "yellow", "You strike the perfect balance between exploring new music and sticking to your favorites."

# Display music personality profile
def display_music_personality():
    # Analyze listening behavior and determine personality type
    personality, color, description = analyze_listening_behavior()
    listening_pattern, pattern_description = analyze_behavioral_insights()

    st.markdown(f"<div class='personality-box'><h2>Your Music Personality Profile</h2></div>", unsafe_allow_html=True)
    
    # Split into two columns
    col1, col2 = st.columns([1, 3])

    # Personality Name and Color
    with col1:
        st.markdown(f'<div class="personality-color-box" style="background-color: {color};"></div>', unsafe_allow_html=True)

    with col2:
        st.write(f"**Personality Name**: {personality}")
        st.write(description)
    
    st.markdown("---")
    
    # Listening Pattern
    st.markdown(f"<div class='insight-box'><h3>Listening Pattern</h3><p><strong>{listening_pattern}</strong></p><p>{pattern_description}</p></div>", unsafe_allow_html=True)

    # Weekly Song Listening Stats (Simulated Data)
    total_songs_this_week = random.randint(80, 200)
    total_minutes_this_week = total_songs_this_week * 3  # Assuming an average song length of 3 minutes

    # Visualization: Weekly song listening graph (Monday to Sunday)
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    songs_per_day = [random.randint(10, 40) for _ in range(7)]  # Simulated data

    # Apple Screen Time-like Visualization using Matplotlib
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.bar(days_of_week, songs_per_day, color='#1DB954')
    ax.set_title('Songs Listened Per Day (This Week)', fontsize=14)
    ax.set_ylabel('Number of Songs')
    ax.set_xlabel('Day of the Week')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('white')
    ax.spines['bottom'].set_color('white')
    ax.tick_params(colors='white')
    ax.set_facecolor('#333')
    ax.yaxis.label.set_color('white')
    ax.xaxis.label.set_color('white')
    
    # Display the stats and chart
    st.write(f"<div class='song-stats-box'><p><strong>Total Tracks This Week:</strong> {total_songs_this_week}</p>", unsafe_allow_html=True)
    st.write(f"<p><strong>Total Minutes Listened:</strong> {total_minutes_this_week} minutes</p></div>", unsafe_allow_html=True)
    st.pyplot(fig)

# Main app logic
if is_authenticated():
    sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

    tab1, tab2, tab3 = st.tabs([
        "Liked Songs & New Discoveries", 
        "Top Songs, Artists & Genres", 
        "Your Music Personality"
    ])

    with tab3:
        display_music_personality()
    
else:
    st.write("Welcome to Wvvy")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
