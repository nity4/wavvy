import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
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
    page_icon="🌊",
    layout="wide"
)

# CSS for Styling
st.markdown("""
    <style>
    body {background: linear-gradient(to right, black, #1DB954) !important; color: white;}
    .stApp {background: linear-gradient(to right, black, #1DB954) !important;}
    h1, h2, h3, p {color: white !important;}
    .brand-box {text-align: center; margin: 20px 0;}
    .brand-logo {font-size: 3.5em; font-weight: bold; color: white;}
    .persona-box {background: #1DB954; color: black; padding: 20px; border-radius: 15px; text-align: center; font-size: 2.5em; font-weight: bold; margin: 20px 0;}
    .persona-desc {background: #333; color: white; padding: 20px; border-radius: 15px; font-size: 1.3em; text-align: center; margin: 20px 0;}
    .cover-small {border-radius: 10px; margin: 10px; width: 80px; height: 80px; object-fit: cover;}
    .cover-circle {border-radius: 50%; margin: 10px; width: 80px; height: 80px; object-fit: cover;}
    .data-box {background: #444; color: white; padding: 15px; border-radius: 10px; margin-top: 20px; text-align: center; font-size: 1.2em;}
    .insights-box {background: #1DB954; color: black; padding: 20px; border-radius: 15px; margin-top: 20px; font-size: 1.5em;}
    </style>
""", unsafe_allow_html=True)

# Token Refresh Helper
def refresh_access_token():
    try:
        token_info = sp_oauth.refresh_access_token(st.session_state["token_info"]["refresh_token"])
        st.session_state["token_info"] = token_info
        return token_info["access_token"]
    except Exception as e:
        st.error(f"Token refresh failed: {e}")
        return None

# Initialize Spotify Client
def initialize_spotify():
    if "token_info" in st.session_state:
        access_token = st.session_state["token_info"]["access_token"]
        return spotipy.Spotify(auth=access_token)
    return None

# Fetch Spotify Data
def fetch_spotify_data(sp_func, *args, **kwargs):
    for attempt in range(2):  # Try twice: refresh token if expired
        try:
            return sp_func(*args, **kwargs)
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 401:  # Token expired
                st.warning("Access token expired. Refreshing...")
                new_token = refresh_access_token()
                if new_token:
                    st.session_state["sp"] = initialize_spotify()
                else:
                    st.error("Failed to refresh token. Please log in again.")
                    return None
            else:
                st.error(f"Spotify API error: {e}")
                return None
    st.error("Failed to fetch data. Please try again later.")
    return None

# Fetch Behavioral Data (Last Week)
def fetch_behavioral_data(sp):
    recent_plays = fetch_spotify_data(sp.current_user_recently_played, limit=50)
    if recent_plays:
        timestamps = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ") for item in recent_plays["items"]]
        track_names = [item["track"]["name"] for item in recent_plays["items"]]
        artist_names = [item["track"]["artists"][0]["name"] for item in recent_plays["items"]]
        durations = [item["track"]["duration_ms"] / 60000 for item in recent_plays["items"]]  # Duration in minutes
        df = pd.DataFrame({"played_at": timestamps, "track_name": track_names, "artist_name": artist_names, "duration": durations})
        df["date"] = df["played_at"].dt.date
        df["hour"] = df["played_at"].dt.hour
        df["weekday"] = df["played_at"].dt.weekday
        return df
    return pd.DataFrame()

# Fetch Top Data
def fetch_top_data(sp):
    top_tracks = fetch_spotify_data(sp.current_user_top_tracks, limit=5, time_range="short_term")
    top_artists = fetch_spotify_data(sp.current_user_top_artists, limit=5, time_range="short_term")
    genres = [genre for artist in top_artists["items"] for genre in artist.get("genres", [])]
    return top_tracks, top_artists, genres

# Display Persona
def display_persona():
    persona_name = random.choice(["Melody Seeker", "Rhythm Explorer", "Harmony Architect", "Vibe Pioneer"])
    explanation = {
        "Melody Seeker": "You're a Melody Seeker—always exploring new vibes, grooving to rhythms, and embracing melodies like no one else!",
        "Rhythm Explorer": "You're a Rhythm Explorer—your playlists are like a map of the beats that move your soul.",
        "Harmony Architect": "You're a Harmony Architect—building your world around symphonies and serene tunes.",
        "Vibe Pioneer": "You're a Vibe Pioneer—leading the charge in discovering the most unique tracks!"
    }
    st.markdown(f"<div class='persona-box'>{persona_name}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='persona-desc'>{explanation[persona_name]}</div>", unsafe_allow_html=True)

# Display Insights in a Single Box
def display_insights(behavior_data):
    if behavior_data.empty:
        st.warning("No recent play data available.")
    else:
        # Daily Listening Streak
        days_played = behavior_data["date"].unique()
        sorted_days = sorted(days_played)
        streak, max_streak = 1, 1
        for i in range(1, len(sorted_days)):
            if (sorted_days[i] - sorted_days[i - 1]).days == 1:
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak = 1

        # Current Streak
        current_streak = 1
        for i in range(len(sorted_days) - 1, 0, -1):
            if (sorted_days[i] - sorted_days[i - 1]).days == 1:
                current_streak += 1
            else:
                break

        # Day or Night Listener
        avg_hour = behavior_data["hour"].mean()
        listener_type = "Night Owl" if avg_hour > 18 else "Day Explorer"

        # Unique Artist Discovery
        unique_artists = behavior_data["artist_name"].nunique()

        insights = f"""
        - **Longest Listening Streak**: {max_streak} days.
        - **Current Streak**: {current_streak} days.
        - **Listening Style**: You're a {listener_type}.
        - **Unique Artists Discovered**: {unique_artists} this month.
        """
        st.markdown(f"<div class='insights-box'>{insights}</div>", unsafe_allow_html=True)

# Plot Listening Heatmap
def plot_listening_heatmap(behavior_data):
    if not behavior_data.empty:
        heatmap_data = behavior_data.groupby(["hour", "weekday"]).size().unstack(fill_value=0)
        plt.figure(figsize=(12, 6))
        sns.heatmap(heatmap_data, cmap="magma", linewidths=0.5, annot=True, fmt="d")
        plt.title("Listening Heatmap (Hour vs. Day)", color="white")
        plt.xlabel("Day", color="white")
        plt.ylabel("Hour", color="white")
        plt.xticks(ticks=range(7), labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], color="white", rotation=45)
        plt.yticks(color="white")
        plt.gca().patch.set_facecolor("black")
        plt.gcf().set_facecolor("black")
        st.pyplot(plt)

# Plot Average Track Length
def plot_average_track_length(behavior_data):
    if not behavior_data.empty:
        avg_duration = behavior_data.groupby("weekday")["duration"].mean()
        plt.figure(figsize=(10, 6))
        avg_duration.plot(kind="bar", color="#1DB954")
        plt.title("Average Track Length (Minutes)", color="white")
        plt.xlabel("Day of the Week", color="white")
        plt.ylabel("Average Length (Minutes)", color="white")
        plt.xticks(ticks=range(7), labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], color="white", rotation=45)
        plt.yticks(color="white")
        plt.gca().patch.set_facecolor("black")
        plt.gcf().set_facecolor("black")
        st.pyplot(plt)

# Main Application
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
    if "sp" not in st.session_state:
        st.session_state["sp"] = initialize_spotify()

    sp = st.session_state["sp"]

    st.title("WVY 🌊 - Your Spotify Insights")
    page = st.radio("Navigate to:", ["Liked Songs & Discover New", "Insights & Behavior"])

    if page == "Liked Songs & Discover New":
        st.title("Liked Songs & Discover New")
        mood = st.selectbox("Choose a Mood:", ["Happy", "Calm", "Energetic", "Sad"])
        intensity = st.slider("Select Intensity (1-5):", 1, 5, 3)
        feature = st.radio("Explore:", ["Liked Songs", "Discover New Songs"])

        if feature == "Liked Songs":
            liked_songs = fetch_spotify_data(sp.current_user_saved_tracks, limit=50)
            if liked_songs and "items" in liked_songs:
                for item in liked_songs["items"][:10]:
                    track = item["track"]
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

        elif feature == "Discover New Songs":
            recommendations = fetch_recommendations(sp, mood, intensity)
            if recommendations and "tracks" in recommendations:
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
        st.header("Insights & Behavior (Last Week)")
        behavior_data = fetch_behavioral_data(sp)
        top_tracks, top_artists, genres = fetch_top_data(sp)

        # Persona Section
        display_persona()

        # Insights Section
        st.subheader("Your Insights")
        display_insights(behavior_data)

        # Top Songs
        st.subheader("Your Top Songs")
        if top_tracks and "items" in top_tracks:
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

        # Top Artists
        st.subheader("Your Top Artists")
        if top_artists and "items" in top_artists:
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

        # Top Genres
        st.subheader("Your Top Genres")
        if genres:
            st.markdown(", ".join(genres[:5]))

        # Graphs Section
        st.subheader("Graphical Analysis")
        plot_listening_heatmap(behavior_data)
        plot_average_track_length(behavior_data)
