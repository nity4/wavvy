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
    .persona-card {background: #1a1a1a; color: white; padding: 20px; border-radius: 15px; margin: 20px; text-align: center; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.3);}
    .persona-title {font-size: 2.5em; font-weight: bold; margin-bottom: 10px;}
    .persona-desc {font-size: 1.2em; line-height: 1.6; color: #cfcfcf;}
    .insights-box {display: flex; justify-content: space-between; flex-wrap: wrap; background: #333; padding: 20px; border-radius: 15px; margin-top: 20px;}
    .insight-badge {flex: 1 1 calc(33.333% - 20px); background: #444; color: white; margin: 10px; padding: 20px; border-radius: 15px; text-align: center; font-size: 1.2em; font-weight: bold; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.3);}
    .insight-icon {font-size: 2em; margin-bottom: 10px; display: block;}
    .cover-small {border-radius: 10px; margin: 10px; width: 80px; height: 80px; object-fit: cover;}
    .cover-circle {border-radius: 50%; margin: 10px; width: 80px; height: 80px; object-fit: cover;}
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
        df = pd.DataFrame({"played_at": timestamps, "track_name": track_names, "artist_name": artist_names})
        df["date"] = df["played_at"].dt.date
        df["hour"] = df["played_at"].dt.hour
        df["weekday"] = df["played_at"].dt.weekday
        return df
    return pd.DataFrame()

# Display Persona
def display_persona():
    persona_name = "Rhythm Explorer"
    explanation = "You're a Rhythm Explorer—your playlists are like a map of the beats that move your soul."
    st.markdown(f"""
        <div class="persona-card">
            <div class="persona-title">{persona_name}</div>
            <div class="persona-desc">{explanation}</div>
        </div>
    """, unsafe_allow_html=True)

# Display Insights as Enhanced Badges
def display_insights(behavior_data):
    if behavior_data.empty:
        st.warning("No recent play data available.")
    else:
        # Calculate Insights
        days_played = behavior_data["date"].unique()
        current_streak = len(days_played)
        avg_hour = behavior_data["hour"].mean()
        listener_type = "Day Explorer" if avg_hour <= 18 else "Night Owl"
        unique_artists = behavior_data["artist_name"].nunique()

        st.markdown("""
        <div class="insights-box">
            <div class="insight-badge">
                <span class="insight-icon">🔥</span>
                Current Streak<br><strong>{}</strong> days
            </div>
            <div class="insight-badge">
                <span class="insight-icon">☀️🌙</span>
                Listening Style<br><strong>{}</strong>
            </div>
            <div class="insight-badge">
                <span class="insight-icon">🎨</span>
                Unique Artists Discovered<br><strong>{}</strong>
            </div>
        </div>
        """.format(current_streak, listener_type, unique_artists), unsafe_allow_html=True)

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

# Plot Mood vs. Intensity Analysis
def plot_mood_intensity_chart():
    data = pd.DataFrame({
        "Mood": ["Happy", "Calm", "Energetic", "Sad"],
        "Intensity (1-5)": [random.randint(1, 5) for _ in range(4)]
    })
    plt.figure(figsize=(10, 6))
    sns.barplot(x="Mood", y="Intensity (1-5)", data=data, palette="viridis")
    plt.title("Mood vs. Intensity Analysis", color="white")
    plt.xlabel("Mood", color="white")
    plt.ylabel("Average Intensity", color="white")
    plt.xticks(color="white", rotation=45)
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
            recommendations = fetch_spotify_data(sp.recommendations, seed_genres=["pop", "rock"], limit=10)
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

        # Persona Section
        display_persona()

        # Insights Section
        st.subheader("Your Insights")
        display_insights(behavior_data)

        # Graphs Section
        st.subheader("Graphical Analysis")
        plot_listening_heatmap(behavior_data)
        plot_mood_intensity_chart()
