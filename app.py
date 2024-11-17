import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time
import random

# Spotify API credentials from Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Define the required scope for Spotify access
scope = "user-library-read user-top-read playlist-read-private user-read-recently-played"

# Initialize Spotify OAuth
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=scope
)

st.set_page_config(
    page_title="Wvvy - Personalized Music Insights",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Black-Green Theme
st.markdown("""
    <style>
    body {background: linear-gradient(to right, black, #1DB954) !important; color: white;}
    .stApp {background: linear-gradient(to right, black, #1DB954) !important;}
    h1, h2, h3, p {color: white !important;}
    .cover {border-radius: 15px; margin: 5px;}
    .fun-insight-box {background: #333; padding: 15px; border-radius: 10px; margin-top: 20px;}
    .grid {display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 10px;}
    .grid-item {text-align: center;}
    .grid img {width: 100%; border-radius: 10px;}
    </style>
""", unsafe_allow_html=True)

# Function to authenticate user
def authenticate_user():
    if "token_info" not in st.session_state:
        query_params = st.experimental_get_query_params()
        if "code" in query_params:
            try:
                token_info = sp_oauth.get_access_token(query_params["code"][0])
                st.session_state["token_info"] = token_info
                st.experimental_set_query_params()
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Authentication failed: {e}")
        else:
            auth_url = sp_oauth.get_authorize_url()
            st.markdown(f'<a href="{auth_url}" target="_self" style="color: white; text-decoration: none; background-color: #1DB954; padding: 10px 20px; border-radius: 5px;">Login with Spotify</a>', unsafe_allow_html=True)
    return "token_info" in st.session_state

# Fetch data with retry logic
def fetch_spotify_data(sp_func, *args, retries=3, **kwargs):
    for attempt in range(retries):
        try:
            result = sp_func(*args, **kwargs)
            if result:
                return result
        except Exception as e:
            if "rate limit" in str(e).lower():
                time.sleep(2 ** attempt)
            else:
                st.warning(f"Attempt {attempt + 1} failed. Retrying...")
    return None

# Fetch Top Data
def fetch_top_data(sp):
    top_tracks = fetch_spotify_data(sp.current_user_top_tracks, limit=5, time_range="short_term")
    top_artists = fetch_spotify_data(sp.current_user_top_artists, limit=5, time_range="short_term")
    if not top_tracks or not top_artists:
        st.warning("Could not fetch top tracks or artists. Please try again later.")
        return None, None, []
    genres = [genre for artist in top_artists.get("items", []) for genre in artist.get("genres", [])]
    return top_tracks, top_artists, genres

# Generate Fun Insights
def generate_funny_insights(top_artists, genres):
    if not top_artists or not genres:
        return "We couldn't fetch enough data to roast you properly this time."
    artist_names = [artist["name"] for artist in top_artists.get("items", [])]
    if artist_names and genres:
        return f"""Your top artist is **{artist_names[0]}**—basically your soulmate.
                   With genres like **{genres[0]}** and **{genres[1]}**, you're definitely cooler than everyone else."""
    return "Not enough data to generate insights. Keep listening to more music!"

# Fetch Behavioral Data
def fetch_behavioral_data(sp):
    recent_plays = fetch_spotify_data(sp.current_user_recently_played, limit=50)
    if not recent_plays or "items" not in recent_plays:
        st.warning("Could not fetch listening history. Please try again later.")
        return pd.Series(dtype=int)
    hours = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ").hour for item in recent_plays["items"]]
    return pd.Series(hours).value_counts()

# Fun Personality Label
def get_personality_label(peak_hour):
    if 0 <= peak_hour <= 6:
        return "Night Owl", "Grooving in the quiet hours."
    elif 7 <= peak_hour <= 12:
        return "Morning Motivator", "Starting your day with vibes."
    elif 13 <= peak_hour <= 18:
        return "Afternoon Explorer", "Jamming through productive hours."
    else:
        return "Evening Relaxer", "Chilling and vibing post-sunset."

# Main App Logic
if authenticate_user():
    sp = spotipy.Spotify(auth=st.session_state["token_info"]["access_token"])

    # Sidebar Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a Page:", ["Liked Songs and Discover", "Top Songs and Genres", "Behavior and Insights"])

    if page == "Liked Songs and Discover":
        st.title("Liked Songs and Discover New Recommendations")
        # Handle liked songs and recommendations here...
    elif page == "Top Songs and Genres":
        st.title("Top Songs, Artists, and Genres")
        top_tracks, top_artists, genres = fetch_top_data(sp)
        if top_tracks:
            st.header("Top Tracks")
            for track in top_tracks["items"]:
                st.write(f"**{track['name']}** by {track['artists'][0]['name']}")
        if top_artists:
            st.header("Top Artists")
            for artist in top_artists["items"]:
                st.write(f"**{artist['name']}**")
        if genres:
            st.header("Top Genres")
            st.write(", ".join(set(genres[:5])))
        st.header("Fun Insights")
        st.markdown(f"""
            <div class="fun-insight-box">
                {generate_funny_insights(top_artists, genres)}
            </div>
        """, unsafe_allow_html=True)
    elif page == "Behavior and Insights":
        st.title("Your Listening Behavior and Fun Insights")
        listening_hours = fetch_behavioral_data(sp)
        if not listening_hours.empty:
            # Plot Listening Patterns
            st.header("Listening Patterns Throughout the Day")
            fig, ax = plt.subplots()
            listening_hours.sort_index().plot(kind="bar", ax=ax, color="#1DB954")
            ax.set_title("Listening Behavior")
            ax.set_xlabel("Hour of Day")
            ax.set_ylabel("Tracks Played")
            st.pyplot(fig)
            # Personality Insight
            peak_hour = listening_hours.idxmax()
            personality, description = get_personality_label(peak_hour)
            st.header("Your Music Personality")
            st.success(f"**{personality}:** {description}")
        else:
            st.warning("No behavioral data available.")
else:
    st.write("Please log in to access your Spotify data.")
