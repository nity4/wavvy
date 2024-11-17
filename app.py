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
    .persona-box {background: #1DB954; color: black; padding: 20px; border-radius: 15px; text-align: center; font-size: 2.5em; font-weight: bold; margin: 20px 0;}
    .persona-desc {background: #333; color: white; padding: 20px; border-radius: 15px; font-size: 1.3em; text-align: center; margin: 20px 0;}
    .cover-small {border-radius: 10px; margin: 10px; width: 80px; height: 80px; object-fit: cover;}
    .data-box {background: #444; color: white; padding: 15px; border-radius: 10px; margin-top: 20px; text-align: center; font-size: 1.2em;}
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

def fetch_top_data(sp):
    """Fetch user's top tracks and artists."""
    top_tracks = fetch_spotify_data(sp.current_user_top_tracks, limit=5, time_range="short_term")
    top_artists = fetch_spotify_data(sp.current_user_top_artists, limit=5, time_range="short_term")
    return top_tracks, top_artists

def fetch_behavioral_data(sp):
    """Fetch and analyze user's recently played tracks."""
    recent_plays = fetch_spotify_data(sp.current_user_recently_played, limit=50)
    if recent_plays:
        timestamps = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ") for item in recent_plays["items"]]
        track_names = [item["track"]["name"] for item in recent_plays["items"]]
        df = pd.DataFrame({"played_at": timestamps, "track_name": track_names})
        df["hour"] = df["played_at"].dt.hour
        df["date"] = df["played_at"].dt.date
        return df
    return pd.DataFrame()

def display_top_songs(top_tracks):
    """Display user's top songs with smaller covers."""
    st.header("Your Top Songs")
    if top_tracks and "items" in top_tracks:
        for track in top_tracks["items"]:
            album_image = track['album']['images'][0]['url']
            song_name = track['name']
            artists = ', '.join(artist['name'] for artist in track['artists'])
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <img src="{album_image}" alt="Cover" class="cover-small">
                    <div>
                        <p><strong>{song_name}</strong></p>
                        <p>by {artists}</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.warning("No top songs available.")

def display_persona():
    """Generate and display user's persona."""
    persona_name = random.choice(["Beat Maverick", "Harmony Prodigy", "Rhythm Nomad", "Melody Seeker"])
    st.markdown(f"<div class='persona-box'>{persona_name}</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='persona-desc'>You're a {persona_name}—always exploring new vibes, grooving to rhythms, and embracing melodies like no one else!</div>",
        unsafe_allow_html=True
    )

def display_insights(behavior_data):
    """Display revamped insights in a Gen Z style."""
    st.header("Insights")
    if behavior_data.empty:
        st.warning("No recent play data available.")
    else:
        most_played_day = behavior_data["date"].mode()[0]
        total_tracks = len(behavior_data)
        unique_songs = len(behavior_data["track_name"].unique())

        insights = [
            f"You listened the most on {most_played_day}.",
            f"You vibed with {total_tracks} tracks this month.",
            f"You explored {unique_songs} unique songs. Curator vibes?"
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
    """Plot a heatmap showing listening activity by date and time."""
    if not behavior_data.empty:
        st.subheader("Listening Heatmap (Date vs. Hour)")
        heatmap_data = behavior_data.groupby(["hour", "date"]).size().unstack(fill_value=0)
        plt.figure(figsize=(12, 6))
        sns.heatmap(heatmap_data, cmap="magma", linewidths=0.5)
        plt.title("Listening Activity Heatmap", color="white")
        plt.xlabel("Date", color="white")
        plt.ylabel("Hour of the Day", color="white")
        plt.xticks(color="white", rotation=45)
        plt.yticks(color="white")
        plt.gca().patch.set_facecolor("black")
        plt.gcf().set_facecolor("black")
        st.pyplot(plt)

def plot_fun_chart(behavior_data):
    """Plot a fun chart showing track diversity by date."""
    if not behavior_data.empty:
        st.subheader("Track Diversity Over the Month")
        diversity_data = behavior_data.groupby("date")["track_name"].nunique()
        plt.figure(figsize=(10, 6))
        diversity_data.plot(kind="line", marker="o", color="#1DB954", linewidth=2)
        plt.title("Daily Track Diversity", color="white")
        plt.xlabel("Date", color="white")
        plt.ylabel("Unique Tracks", color="white")
        plt.xticks(color="white", rotation=45)
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
            display_top_songs(liked_songs)

        elif feature == "Discover New Songs":
            st.header("Discover New Songs")
            recommendations = fetch_recommendations(sp, mood, intensity)
            display_top_songs(recommendations)

    # Page 2: Insights & Behavior
    elif page == "Insights & Behavior":
        st.title("Insights & Behavior (Last Month)")

        # Fetch Data
        top_tracks, top_artists = fetch_top_data(sp)
        behavior_data = fetch_behavioral_data(sp)

        # Persona
        display_persona()

        # Display Sections
        display_top_songs(top_tracks)
        display_insights(behavior_data)

        # Graphical Analysis
        st.header("Graphical Analysis")
        plot_listening_heatmap(behavior_data)
        plot_fun_chart(behavior_data)
