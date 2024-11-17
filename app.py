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
    .persona-box {display: flex; justify-content: space-between; flex-wrap: wrap; background: #333; padding: 20px; border-radius: 15px; margin-top: 20px;}
    .persona-card {flex: 1 1 calc(33.333% - 20px); background: #444; color: white; margin: 10px; padding: 20px; border-radius: 15px; text-align: center; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.3);}
    .persona-title {font-size: 1.8em; font-weight: bold; margin-bottom: 10px;}
    .persona-value {font-size: 2.5em; font-weight: bold; margin-top: 10px;}
    .cover-small {border-radius: 10px; margin: 10px; width: 80px; height: 80px; object-fit: cover;}
    .cover-circle {border-radius: 50%; margin: 10px; width: 80px; height: 80px; object-fit: cover;}
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

# Display Persona and Insights
def display_persona_and_insights(behavior_data, streak, style, artists):
    st.markdown(f"""
        <div class="persona-box">
            <div class="persona-card">
                <div class="persona-title">🔥 Listening Streak</div>
                <div class="persona-value">{streak} days</div>
            </div>
            <div class="persona-card">
                <div class="persona-title">☀️🌙 Listening Style</div>
                <div class="persona-value">{style}</div>
            </div>
            <div class="persona-card">
                <div class="persona-title">🎨 Unique Artists</div>
                <div class="persona-value">{artists}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Display Top Data
def display_top_data(top_tracks, top_artists, genres):
    st.subheader("Your Top Songs")
    if top_tracks:
        for track in top_tracks["items"]:
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <img src="{track['album']['images'][0]['url']}" alt="Cover" class="cover-small">
                    <div>
                        <p><strong>{track['name']}</strong></p>
                        <p>by {', '.join(artist['name'] for artist in track['artists'])}</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.subheader("Your Top Artists")
    if top_artists:
        for artist in top_artists["items"]:
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <img src="{artist['images'][0]['url']}" alt="Artist" class="cover-circle">
                    <div>
                        <p><strong>{artist['name']}</strong></p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.subheader("Your Top Genres")
    if genres:
        st.write(", ".join(genres[:5]))

# Plot Listening Heatmap
def plot_listening_heatmap(behavior_data):
    if not behavior_data.empty:
        heatmap_data = behavior_data.groupby(["hour", "weekday"]).size().unstack(fill_value=0)
        plt.figure(figsize=(12, 6))
        sns.heatmap(heatmap_data, cmap="magma", linewidths=0.5, annot=True, fmt="d")
        plt.title("Listening Heatmap (Hour vs. Day)", color="white")
        plt.xlabel("Day", color="white")
        plt.ylabel("Hour", color="white")
        plt.xticks(ticks=range(7), labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], color="white")
        plt.yticks(color="white")
        plt.gca().patch.set_facecolor("black")
        plt.gcf().set_facecolor("black")
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
                    st.markdown(
                        f"""
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <img src="{item['track']['album']['images'][0]['url']}" alt="Cover" class="cover-small">
                            <div>
                                <p><strong>{item['track']['name']}</strong></p>
                                <p>by {', '.join(artist['name'] for artist in item['track']['artists'])}</p>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        elif feature == "Discover New Songs":
            recommendations = fetch_spotify_data(sp.recommendations, seed_genres=["pop", "rock"], limit=10)
            if recommendations:
                for track in recommendations["tracks"]:
                    st.markdown(
                        f"""
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <img src="{track['album']['images'][0]['url']}" alt="Cover" class="cover-small">
                            <div>
                                <p><strong>{track['name']}</strong></p>
                                <p>by {', '.join(artist['name'] for artist in track['artists'])}</p>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    elif page == "Insights & Behavior":
        st.title("Insights & Behavior")
        week_type = "current" if datetime.today().weekday() > 2 else "last"
        behavior_data = fetch_behavioral_data(sp, week_type)
        top_tracks, top_artists, genres = fetch_top_data(sp)

        display_persona_and_insights(
            behavior_data,
            streak=5,  # Example streak
            style="Day Explorer",
            artists=29  # Example unique artist count
        )
        display_top_data(top_tracks, top_artists, genres)
        plot_listening_heatmap(behavior_data)
