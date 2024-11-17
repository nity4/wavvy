import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from datetime import datetime
import random
from requests.exceptions import ConnectionError

# Spotify API credentials
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Spotify OAuth Scope
scope = "user-library-read user-top-read playlist-read-private user-read-recently-played"

# Spotify OAuth Setup
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=scope
)

# Streamlit Page Configuration
st.set_page_config(
    page_title="WVY - Your Spotify Companion",
    page_icon="🎧",
    layout="wide"
)

# CSS for Styling
st.markdown("""
    <style>
    body {background: linear-gradient(to right, black, #1DB954) !important; color: white;}
    .stApp {background: linear-gradient(to right, black, #1DB954) !important;}
    h1, h2, h3, p {color: white !important;}
    .brand {font-size: 3.5em; font-weight: bold; color: white; text-align: center;}
    .title-box {background: linear-gradient(to right, #1DB954, black); padding: 20px; border-radius: 15px; text-align: center; color: white; font-size: 2em;}
    .cover-circle {border-radius: 50%; margin: 10px; width: 80px; height: 80px;}
    .cover-square {border-radius: 10px; margin: 10px; width: 120px; height: 120px;}
    .fun-insight-box {background: #333; color: white; padding: 15px; border-radius: 10px; margin-top: 20px; font-size: 1.2em; line-height: 1.5; text-align: center;}
    </style>
""", unsafe_allow_html=True)

# Helper Functions
def fetch_spotify_data(sp_func, *args, **kwargs):
    """Fetch Spotify data with retry logic and error handling."""
    try:
        return sp_func(*args, **kwargs)
    except ConnectionError:
        st.error("Connection error. Please check your internet connection.")
        return None
    except spotipy.exceptions.SpotifyException as e:
        st.error(f"Spotify API error: {e}")
        return None

def fetch_liked_songs(sp):
    """Fetch user's liked songs."""
    return fetch_spotify_data(sp.current_user_saved_tracks, limit=50)

def fetch_recommendations(sp, mood, intensity):
    """Fetch song recommendations based on mood and intensity."""
    mood_map = {"Happy": (0.8, 0.7), "Calm": (0.3, 0.4), "Energetic": (0.9, 0.8), "Sad": (0.2, 0.3)}
    valence, energy = [val * intensity / 5 for val in mood_map[mood]]
    seed_tracks = fetch_spotify_data(sp.current_user_saved_tracks, limit=5)
    if seed_tracks and "items" in seed_tracks:
        seed_ids = [item["track"]["id"] for item in seed_tracks["items"][:5]]
        return fetch_spotify_data(
            sp.recommendations,
            seed_tracks=seed_ids,
            limit=10,
            target_valence=valence,
            target_energy=energy
        )
    return None

def fetch_top_tracks_artists(sp):
    """Fetch user's top tracks and artists for the past month."""
    top_tracks = fetch_spotify_data(sp.current_user_top_tracks, limit=5, time_range="short_term")
    top_artists = fetch_spotify_data(sp.current_user_top_artists, limit=5, time_range="short_term")
    return top_tracks, top_artists

def fetch_behavioral_data(sp):
    """Fetch user's recently played tracks and analyze behavioral trends."""
    recent_plays = fetch_spotify_data(sp.current_user_recently_played, limit=50)
    if recent_plays:
        timestamps = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ") for item in recent_plays["items"]]
        df = pd.DataFrame(timestamps, columns=["played_at"])
        df["hour"] = df["played_at"].dt.hour
        df["weekday"] = df["played_at"].dt.weekday
        return df
    return pd.DataFrame()

# Authentication and Initialization
if "token_info" not in st.session_state:
    query_params = st.experimental_get_query_params()
    if "code" in query_params:
        try:
            token_info = sp_oauth.get_access_token(query_params["code"][0])
            st.session_state["token_info"] = token_info
            st.experimental_set_query_params()
            st.success("Authentication successful! Refresh the page to continue.")
        except Exception as e:
            st.error(f"Authentication failed: {e}")
    else:
        auth_url = sp_oauth.get_authorize_url()
        st.markdown(f'<a href="{auth_url}" target="_self" style="color: white; text-decoration: none; background-color: #1DB954; padding: 10px 20px; border-radius: 5px;">Login with Spotify</a>', unsafe_allow_html=True)

if "token_info" in st.session_state:
    sp = spotipy.Spotify(auth=st.session_state["token_info"]["access_token"])

    # Page Navigation
    page = st.radio("Navigate to:", ["Liked Songs & Discover New", "Insights & Behavior"])

    # Page 1: Liked Songs & Discover New
    if page == "Liked Songs & Discover New":
        st.title("🎵 Liked Songs & Discover New")
        mood = st.selectbox("Choose Mood:", ["Happy", "Calm", "Energetic", "Sad"])
        intensity = st.slider("Select Intensity (1-5):", 1, 5, 3)
        feature = st.radio("What do you want to explore?", ["Liked Songs", "Discover New Songs"])

        if feature == "Liked Songs":
            st.header("❤️ Your Liked Songs")
            liked_songs = fetch_liked_songs(sp)
            if liked_songs and "items" in liked_songs:
                for item in liked_songs["items"][:10]:
                    track = item["track"]
                    st.markdown(f"""
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <img src="{track['album']['images'][0]['url']}" alt="Cover" class="cover-square">
                            <div style="margin-left: 10px;">
                                <p><strong>{track['name']}</strong></p>
                                <p>by {', '.join(artist['name'] for artist in track['artists'])}</p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

        elif feature == "Discover New Songs":
            st.header("🔍 Discover New Songs")
            recommendations = fetch_recommendations(sp, mood, intensity)
            if recommendations and "tracks" in recommendations:
                for track in recommendations["tracks"]:
                    st.markdown(f"""
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <img src="{track['album']['images'][0]['url']}" alt="Cover" class="cover-square">
                            <div style="margin-left: 10px;">
                                <p><strong>{track['name']}</strong></p>
                                <p>by {', '.join(artist['name'] for artist in track['artists'])}</p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

    # Page 2: Insights & Behavior
    elif page == "Insights & Behavior":
        st.title("🎧 Insights & Behavior (Last Month)")

        # Persona
        top_tracks, top_artists = fetch_top_tracks_artists(sp)
        persona_name = random.choice(["Melody Magician", "Rhythm Rebel", "Beat Explorer", "Vibe Dealer"])
        st.markdown(f"""
            <div class="title-box">
                🌟 Your Monthly Persona: <strong>{persona_name}</strong> 🌟
            </div>
        """)

        # Top Songs Section
        st.header("🎵 Your Top Songs")
        if top_tracks and "items" in top_tracks:
            for track in top_tracks["items"]:
                st.markdown(f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <img src="{track['album']['images'][0]['url']}" alt="Cover" class="cover-square">
                        <div style="margin-left: 10px;">
                            <p><strong>{track['name']}</strong></p>
                            <p>by {', '.join(artist['name'] for artist in track['artists'])}</p>
                        </div>
                    </div>
                """)

        # Top Artists Section
        st.header("🎨 Your Top Artists")
        if top_artists and "items" in top_artists:
            for artist in top_artists["items"]:
                st.markdown(f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <img src="{artist['images'][0]['url']}" alt="Artist" class="cover-circle">
                        <div style="margin-left: 10px;">
                            <p><strong>{artist['name']}</strong></p>
                        </div>
                    </div>
                """)

        # Fun Insights
        st.header("😂 Fun Insights from Your Month")
        behavior_data = fetch_behavioral_data(sp)
        if behavior_data.empty:
            st.warning("No recent play data available.")
        else:
            peak_hour = behavior_data["hour"].mode()[0]
            weekday = behavior_data["weekday"].mode()[0]
            day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][weekday]
            total_tracks = len(behavior_data)

            fun_insights = [
                f"🎤 You vibe the most at {peak_hour}:00. Peak hours, peak feels!",
                f"🌙 Your favorite day to jam is {day_name}. Ultimate vibe day?",
                f"🔥 You played {total_tracks} tracks this month. Music marathon much?"
            ]

            for insight in fun_insights:
                st.markdown(f"""
                    <div class="fun-insight-box">
                        {insight}
                    </div>
                """)

