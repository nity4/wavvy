import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from datetime import datetime
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
    .data-box {background: #444; color: white; padding: 15px; border-radius: 10px; margin-top: 20px; text-align: center; font-size: 1.2em;}
    .cover-square {border-radius: 10px; margin: 10px; width: 120px; height: 120px; object-fit: cover;}
    .cover-circle {border-radius: 50%; margin: 10px; width: 80px; height: 80px; object-fit: cover;}
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

def fetch_top_data(sp):
    """Fetch user's top tracks, artists, and genres."""
    top_tracks = fetch_spotify_data(sp.current_user_top_tracks, limit=5, time_range="short_term")
    top_artists = fetch_spotify_data(sp.current_user_top_artists, limit=5, time_range="short_term")
    genres = [genre for artist in top_artists["items"] for genre in artist.get("genres", [])]
    return top_tracks, top_artists, genres

def fetch_behavioral_data(sp):
    """Fetch and analyze user's recently played tracks."""
    recent_plays = fetch_spotify_data(sp.current_user_recently_played, limit=50)
    if recent_plays:
        timestamps = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ") for item in recent_plays["items"]]
        df = pd.DataFrame({"played_at": timestamps})
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
                    <div>
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
                    <div>
                        <p><strong>{artist_name}</strong></p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.warning("No top artists data available.")

def display_top_genres(genres):
    """Display user's favorite genres."""
    st.header("Your Top Genres")
    if genres:
        st.markdown(f"**{', '.join(genres[:5])}**")
    else:
        st.warning("No genres available.")

def display_insights(behavior_data):
    """Display insights based on the user's listening behavior."""
    st.header("Insights")
    if behavior_data.empty:
        st.warning("No recent play data available.")
    else:
        peak_hour = behavior_data["hour"].mode()[0]
        total_tracks = len(behavior_data)
        unique_hours = len(behavior_data["hour"].unique())

        insights = [
            f"Peak listening hour: {peak_hour}:00.",
            f"Total tracks played: {total_tracks}.",
            f"Unique listening hours: {unique_hours}."
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

def plot_listening_heatmap(behavior_data):
    """Plot a heatmap showing listening activity by hour and day."""
    if not behavior_data.empty:
        st.subheader("Listening Activity Heatmap")
        heatmap_data = behavior_data.groupby(["hour", "weekday"]).size().unstack(fill_value=0)
        plt.figure(figsize=(10, 6))
        sns.heatmap(heatmap_data, cmap="magma", annot=True, fmt="d", linewidths=0.5)
        plt.title("Listening Activity by Hour and Day", color="white")
        plt.xlabel("Day of the Week", color="white")
        plt.ylabel("Hour of the Day", color="white")
        plt.xticks(ticks=range(7), labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], color="white")
        plt.yticks(color="white")
        plt.gca().patch.set_facecolor("black")
        plt.gcf().set_facecolor("black")
        st.pyplot(plt)

def plot_unique_hours_graph(behavior_data):
    """Plot the distribution of unique listening hours."""
    if not behavior_data.empty:
        st.subheader("Unique Listening Hours Distribution")
        unique_hours = behavior_data["hour"].value_counts().sort_index()
        plt.figure(figsize=(10, 6))
        unique_hours.plot(kind="bar", color="#1DB954")
        plt.title("Unique Listening Hours", color="white")
        plt.xlabel("Hour of the Day", color="white")
        plt.ylabel("Frequency", color="white")
        plt.xticks(color="white")
        plt.yticks(color="white")
        plt.gca().patch.set_facecolor("black")
        plt.gcf().set_facecolor("black")
        st.pyplot(plt)

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
    page = st.radio("Navigate to:", ["Insights & Behavior"])

    if page == "Insights & Behavior":
        st.title("Insights & Behavior (Last Month)")

        # Fetch Data
        top_tracks, top_artists, genres = fetch_top_data(sp)
        behavior_data = fetch_behavioral_data(sp)

        # Persona
        persona_name = random.choice(["Vibe Explorer", "Rhythm Ninja", "Beat Whisperer", "Melody Maverick"])
        st.markdown(f"<div class='title-box'>Your Persona: <strong>{persona_name}</strong></div>", unsafe_allow_html=True)
        st.markdown(f"You've been on a musical journey as a true {persona_name}. Always exploring, vibing, and feeling the beats!")

        # Display Sections
        display_top_songs(top_tracks)
        display_top_artists(top_artists)
        display_top_genres(genres)
        display_insights(behavior_data)

        # Graphical Analysis
        st.header("Graphical Analysis")
        plot_listening_heatmap(behavior_data)
        plot_unique_hours_graph(behavior_data)
