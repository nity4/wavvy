import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from datetime import datetime
import random

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
    page_title="WVY - Your Spotify Insights",
    page_icon="🎧",
    layout="wide"
)

# CSS for Styling
st.markdown("""
    <style>
    body {background: linear-gradient(to right, black, #1DB954) !important; color: white;}
    .stApp {background: linear-gradient(to right, black, #1DB954) !important;}
    h1, h2, h3, p {color: white !important;}
    .title-box {background: linear-gradient(to right, #1DB954, black); padding: 20px; border-radius: 15px; text-align: center; color: white; font-size: 2em; font-weight: bold;}
    .cover-circle {border-radius: 50%; margin: 10px; width: 80px; height: 80px; object-fit: cover;}
    .cover-square {border-radius: 10px; margin: 10px; width: 120px; height: 120px; object-fit: cover;}
    .data-box {background: #333; color: white; padding: 15px; border-radius: 10px; margin-top: 20px; text-align: center;}
    </style>
""", unsafe_allow_html=True)

# Helper Functions
def fetch_spotify_data(sp_func, *args, **kwargs):
    """Fetch Spotify data with error handling."""
    try:
        return sp_func(*args, **kwargs)
    except spotipy.exceptions.SpotifyException as e:
        st.error(f"Spotify API error: {e}")
        return None

def fetch_liked_songs(sp):
    """Fetch user's liked songs."""
    return fetch_spotify_data(sp.current_user_saved_tracks, limit=50)

def fetch_recommendations(sp, mood, intensity):
    """Fetch recommendations based on mood and intensity."""
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
    """Fetch user's top tracks and artists."""
    top_tracks = fetch_spotify_data(sp.current_user_top_tracks, limit=5, time_range="short_term")
    top_artists = fetch_spotify_data(sp.current_user_top_artists, limit=5, time_range="short_term")
    return top_tracks, top_artists

def fetch_behavioral_data(sp):
    """Fetch and analyze user's recently played tracks."""
    recent_plays = fetch_spotify_data(sp.current_user_recently_played, limit=50)
    if recent_plays:
        timestamps = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ") for item in recent_plays["items"]]
        df = pd.DataFrame(timestamps, columns=["played_at"])
        df["hour"] = df["played_at"].dt.hour
        df["weekday"] = df["played_at"].dt.weekday
        return df
    return pd.DataFrame()

def display_top_songs(top_tracks):
    """Display the user's top songs."""
    st.header("Your Top Songs")
    if top_tracks and "items" in top_tracks:
        for track in top_tracks["items"]:
            album_image = track['album']['images'][0]['url']
            song_name = track['name']
            artists = ', '.join(artist['name'] for artist in track['artists'])
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <img src="{album_image}" alt="Cover" class="cover-square">
                    <div style="margin-left: 10px;">
                        <p><strong>{song_name}</strong></p>
                        <p>by {artists}</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.warning("No top songs data available.")

def display_top_artists(top_artists):
    """Display the user's top artists."""
    st.header("Your Top Artists")
    if top_artists and "items" in top_artists:
        for artist in top_artists["items"]:
            artist_image = artist['images'][0]['url']
            artist_name = artist['name']
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <img src="{artist_image}" alt="Artist" class="cover-circle">
                    <div style="margin-left: 10px;">
                        <p><strong>{artist_name}</strong></p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.warning("No top artists data available.")

def display_insights(behavior_data):
    """Display insights based on user's listening behavior."""
    st.header("Listening Insights")
    if behavior_data.empty:
        st.warning("No recent play data available.")
    else:
        peak_hour = behavior_data["hour"].mode()[0]
        total_tracks = len(behavior_data)
        insights = [
            f"Your favorite time to listen is {peak_hour}:00.",
            f"You played {total_tracks} tracks this month."
        ]
        for insight in insights:
            st.markdown(
                f"""
                <div class="data-box">
                    {insight}
                </div>
                """,
                unsafe_allow_html=True
            )

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
        st.markdown(
            f'<a href="{auth_url}" target="_self" style="color: white; text-decoration: none; background-color: #1DB954; padding: 10px 20px; border-radius: 5px;">Login with Spotify</a>',
            unsafe_allow_html=True
        )

if "token_info" in st.session_state:
    sp = spotipy.Spotify(auth=st.session_state["token_info"]["access_token"])

    # Page Navigation
    page = st.radio("Navigate to:", ["Liked Songs & Discover New", "Insights & Behavior"])

    # Page 1: Liked Songs & Discover New
    if page == "Liked Songs & Discover New":
        st.title("Liked Songs & Discover New")
        mood = st.selectbox("Choose a Mood:", ["Happy", "Calm", "Energetic", "Sad"])
        intensity = st.slider("Select Intensity (1-5):", 1, 5, 3)
        feature = st.radio("Explore:", ["Liked Songs", "Discover New Songs"])

        if feature == "Liked Songs":
            st.header("Your Liked Songs")
            liked_songs = fetch_liked_songs(sp)
            if liked_songs and "items" in liked_songs:
                for item in liked_songs["items"][:10]:
                    track = item["track"]
                    st.markdown(
                        f"""
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <img src="{track['album']['images'][0]['url']}" alt="Cover" class="cover-square">
                            <div style="margin-left: 10px;">
                                <p><strong>{track['name']}</strong></p>
                                <p>by {', '.join(artist['name'] for artist in track['artists'])}</p>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.warning("No liked songs available.")

        elif feature == "Discover New Songs":
            st.header("Discover New Songs")
            recommendations = fetch_recommendations(sp, mood, intensity)
            if recommendations and "tracks" in recommendations:
                for track in recommendations["tracks"]:
                    st.markdown(
                        f"""
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <img src="{track['album']['images'][0]['url']}" alt="Cover" class="cover-square">
                            <div style="margin-left: 10px;">
                                <p><strong>{track['name']}</strong></p>
                                <p>by {', '.join(artist['name'] for artist in track['artists'])}</p>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.warning("No recommendations available.")

    # Page 2: Insights & Behavior
    elif page == "Insights & Behavior":
        st.title("Insights & Behavior (Last Month)")

        # Fetch Data
        top_tracks, top_artists = fetch_top_tracks_artists(sp)
        recent_plays = fetch_spotify_data(sp.current_user_recently_played, limit=50)
        behavior_data = pd.DataFrame(
            [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ") for item in recent_plays["items"]],
            columns=["played_at"]
        ) if recent_plays else pd.DataFrame()
        behavior_data["hour"] = behavior_data["played_at"].dt.hour

        # Display Persona
        persona_name = random.choice(["Melody Master", "Rhythm Explorer", "Beat Connoisseur", "Vibe Enthusiast"])
        st.markdown(
            f"""
            <div class="title-box">
                Your Monthly Persona: <strong>{persona_name}</strong>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write("Your listening habits this month earned you this unique persona. You explore music with style and purpose.")

        # Display Sections
        display_top_songs(top_tracks)
        display_top_artists(top_artists)
        display_insights(behavior_data)
