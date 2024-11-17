import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

# Spotify API credentials
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Spotify OAuth Scope
scope = "user-library-read user-top-read playlist-read-private user-read-recently-played"

# Streamlit Page Configuration
st.set_page_config(
    page_title="WVY - Spotify Insights",
    page_icon="🌊",
    layout="wide"
)

# CSS for Styling
st.markdown("""
    <style>
    body {background: linear-gradient(to right, black, #1DB954) !important; color: white;}
    .stApp {background: linear-gradient(to right, black, #1DB954) !important;}
    h1, h2, h3, p {color: white !important;}
    </style>
""", unsafe_allow_html=True)

# Spotify OAuth Helper Functions
def login_with_spotify():
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=scope,
        show_dialog=True
    )
    token_info = auth_manager.get_access_token(as_dict=True)
    st.session_state["token_info"] = token_info
    st.session_state["sp"] = spotipy.Spotify(auth=token_info["access_token"])

def refresh_access_token():
    try:
        if "token_info" in st.session_state:
            auth_manager = SpotifyOAuth(
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                redirect_uri=REDIRECT_URI,
                scope=scope
            )
            token_info = auth_manager.refresh_access_token(
                st.session_state["token_info"]["refresh_token"]
            )
            st.session_state["token_info"] = token_info
            st.session_state["sp"] = spotipy.Spotify(auth=token_info["access_token"])
    except Exception as e:
        st.error(f"Failed to refresh token: {e}")

# Initialize Spotify Client
def initialize_spotify():
    if "token_info" in st.session_state:
        access_token = st.session_state["token_info"]["access_token"]
        return spotipy.Spotify(auth=access_token)
    return None

# Fetch Spotify Data
def fetch_spotify_data(sp_func, *args, **kwargs):
    try:
        return sp_func(*args, **kwargs)
    except Exception as e:
        st.error(f"Error fetching Spotify data: {e}")
        return None

# Fetch Behavioral Data
def fetch_behavioral_data(sp, week_type):
    today = datetime.today().date()
    if week_type == "current":
        start_date = today - timedelta(days=today.weekday())
    else:
        start_date = today - timedelta(days=today.weekday() + 7)

    recent_plays = fetch_spotify_data(sp.current_user_recently_played, limit=50)
    if recent_plays:
        timestamps = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ") for item in recent_plays["items"]]
        track_names = [item["track"]["name"] for item in recent_plays["items"]]
        artist_names = [item["track"]["artists"][0]["name"] for item in recent_plays["items"]]
        df = pd.DataFrame({"played_at": timestamps, "track_name": track_names, "artist_name": artist_names})
        df["date"] = df["played_at"].dt.date
        df["hour"] = df["played_at"].dt.hour
        df["weekday"] = df["played_at"].dt.weekday
        return df[df["date"] >= start_date]
    return pd.DataFrame()

# Fetch Top Tracks and Artists
def fetch_top_data(sp):
    top_tracks = fetch_spotify_data(sp.current_user_top_tracks, limit=5, time_range="short_term")
    top_artists = fetch_spotify_data(sp.current_user_top_artists, limit=5, time_range="short_term")
    genres = [genre for artist in top_artists["items"] for genre in artist.get("genres", [])] if top_artists else []
    return top_tracks, top_artists, genres

# Display Persona
def display_persona():
    st.markdown("""
        <div style="text-align: center; margin: 20px;">
            <h2>Your Spotify Persona</h2>
            <p>You are a "Rhythm Explorer"—mapping beats that move your soul!</p>
        </div>
    """, unsafe_allow_html=True)

# Display Insights
def display_insights(behavior_data):
    if behavior_data.empty:
        st.warning("No recent play data available.")
    else:
        days_played = behavior_data["date"].nunique()
        avg_hour = behavior_data["hour"].mean()
        listener_type = "Day Explorer" if avg_hour <= 18 else "Night Owl"
        unique_artists = behavior_data["artist_name"].nunique()

        st.markdown(f"""
        <div style="display: flex; justify-content: space-around; margin-top: 20px;">
            <div style="text-align: center;">
                <h3>🔥 Listening Streak</h3>
                <p>{days_played} days</p>
            </div>
            <div style="text-align: center;">
                <h3>☀️🌙 Listening Style</h3>
                <p>{listener_type}</p>
            </div>
            <div style="text-align: center;">
                <h3>🎨 Unique Artists</h3>
                <p>{unique_artists}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Display Top Data
def display_top_data(top_tracks, top_artists, genres):
    if top_tracks:
        st.subheader("Top Tracks")
        for track in top_tracks["items"]:
            st.write(f"{track['name']} by {', '.join(artist['name'] for artist in track['artists'])}")

    if top_artists:
        st.subheader("Top Artists")
        for artist in top_artists["items"]:
            st.write(artist["name"])

    if genres:
        st.subheader("Top Genres")
        st.write(", ".join(genres[:5]))

# Plot Listening Heatmap
def plot_listening_heatmap(behavior_data):
    if not behavior_data.empty:
        heatmap_data = behavior_data.groupby(["hour", "weekday"]).size().unstack(fill_value=0)
        plt.figure(figsize=(12, 6))
        sns.heatmap(heatmap_data, cmap="magma", linewidths=0.5, annot=True, fmt="d")
        plt.title("Listening Heatmap (Hour vs. Day)")
        plt.xlabel("Day")
        plt.ylabel("Hour")
        plt.xticks(ticks=range(7), labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], rotation=45)
        st.pyplot(plt)

# Main App Logic
if "token_info" not in st.session_state:
    st.title("Welcome to WVY - Spotify Insights 🌊")
    if st.button("Log in with Spotify"):
        login_with_spotify()
else:
    refresh_access_token()
    sp = st.session_state["sp"]

    page = st.radio("Navigate to:", ["Liked Songs & Discover New", "Insights & Behavior"])

    if page == "Liked Songs & Discover New":
        st.title("Liked Songs & Discover New")
        mood = st.selectbox("Choose a Mood:", ["Happy", "Calm", "Energetic", "Sad"])
        intensity = st.slider("Select Intensity (1-5):", 1, 5, 3)
        feature = st.radio("Explore:", ["Liked Songs", "Discover New Songs"])

        if feature == "Liked Songs":
            liked_songs = fetch_spotify_data(sp.current_user_saved_tracks, limit=50)
            if liked_songs:
                for item in liked_songs["items"]:
                    st.write(f"{item['track']['name']} by {', '.join(artist['name'] for artist in item['track']['artists'])}")

        elif feature == "Discover New Songs":
            recommendations = fetch_spotify_data(sp.recommendations, seed_genres=["pop", "rock"], limit=10)
            if recommendations:
                for track in recommendations["tracks"]:
                    st.write(f"{track['name']} by {', '.join(artist['name'] for artist in track['artists'])}")

    elif page == "Insights & Behavior":
        st.title("Insights & Behavior")
        week_type = "current" if datetime.today().weekday() > 2 else "last"
        behavior_data = fetch_behavioral_data(sp, week_type)
        top_tracks, top_artists, genres = fetch_top_data(sp)

        display_persona()
        display_insights(behavior_data)
        display_top_data(top_tracks, top_artists, genres)
        plot_listening_heatmap(behavior_data)
