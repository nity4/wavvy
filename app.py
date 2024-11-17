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
                st.experimental_set_query_params()  # Clear query params
                st.success("Authentication successful! Refresh the page to continue.")
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
            return sp_func(*args, **kwargs)
        except Exception as e:
            if "rate limit" in str(e).lower():
                time.sleep(2 ** attempt)
            else:
                st.warning(f"Attempt {attempt + 1} failed. Retrying...")
    return None

# Fetch Liked Songs
def fetch_liked_songs(sp):
    liked_songs = fetch_spotify_data(sp.current_user_saved_tracks, limit=20)
    return liked_songs

# Fetch Recommendations
def fetch_recommendations(sp):
    seed_tracks = fetch_spotify_data(sp.current_user_saved_tracks, limit=5)
    if not seed_tracks:
        return None
    recommendations = fetch_spotify_data(
        sp.recommendations,
        seed_tracks=[item["track"]["id"] for item in seed_tracks["items"]],
        limit=10
    )
    return recommendations

# Fetch Top Data
def fetch_top_data(sp):
    top_tracks = fetch_spotify_data(sp.current_user_top_tracks, limit=5, time_range="short_term")
    top_artists = fetch_spotify_data(sp.current_user_top_artists, limit=5, time_range="short_term")
    genres = [genre for artist in top_artists["items"] for genre in artist.get("genres", [])]
    return top_tracks, top_artists, genres

# Fetch Behavioral Data
def fetch_behavioral_data(sp):
    recent_plays = fetch_spotify_data(sp.current_user_recently_played, limit=50)
    hours = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ").hour for item in recent_plays["items"]]
    return pd.Series(hours).value_counts()

# Fun Personality Label
def get_personality_label(peak_hour):
    if 0 <= peak_hour <= 6:
        return "Night Owl", "Grooving in the quiet hours."
    elif 7 <= peak_hour <= 12:
        return "Morning Motivator", "Getting inspired early in the day."
    elif 13 <= peak_hour <= 18:
        return "Afternoon Explorer", "Discovering beats while staying productive."
    else:
        return "Evening Relaxer", "Unwinding with chill vibes."

# Generate Fun Insights
def generate_funny_insights(top_artists, genres):
    artist_names = [artist["name"] for artist in top_artists["items"]]
    return f"""Your top artist is **{artist_names[0]}**—basically your soulmate.
               With genres like **{genres[0]}** and **{genres[1]}**, you're definitely out here making the cool kids jealous."""

# Main App Logic
if authenticate_user():
    sp = spotipy.Spotify(auth=st.session_state["token_info"]["access_token"])

    # Sidebar Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to:", ["Liked Songs and Discover", "Top Songs and Genres", "Behavior and Insights"])

    if page == "Liked Songs and Discover":
        st.title("Liked Songs and Discover New Recommendations")
        feature = st.radio("Select an Option:", ["Liked Songs", "Discover New Songs"])

        if feature == "Liked Songs":
            st.header("Liked Songs")
            liked_songs = fetch_liked_songs(sp)
            if liked_songs:
                for item in random.sample(liked_songs["items"], min(len(liked_songs["items"]), 10)):
                    track = item["track"]
                    st.markdown(f"""
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <img src="{track['album']['images'][0]['url']}" alt="Cover" width="80" height="80" class="cover">
                            <div style="margin-left: 10px;">
                                <p><b>{track['name']}</b><br><i>{track['artists'][0]['name']}</i></p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

        elif feature == "Discover New Songs":
            st.header("Discover New Songs")
            recommendations = fetch_recommendations(sp)
            if recommendations:
                for track in recommendations["tracks"]:
                    st.markdown(f"""
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <img src="{track['album']['images'][0]['url']}" alt="Cover" width="80" height="80" class="cover">
                            <div style="margin-left: 10px;">
                                <p><b>{track['name']}</b><br><i>{track['artists'][0]['name']}</i></p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

    elif page == "Top Songs and Genres":
        st.title("Top Songs, Artists, and Genres")
        top_tracks, top_artists, genres = fetch_top_data(sp)

        st.header("Top Tracks")
        for track in top_tracks["items"]:
            st.write(f"**{track['name']}** by {track['artists'][0]['name']}")

        st.header("Top Artists")
        for artist in top_artists["items"]:
            st.write(f"**{artist['name']}**")

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

        st.header("Listening Patterns Throughout the Day")
        fig, ax = plt.subplots()
        listening_hours.sort_index().plot(kind="bar", ax=ax, color="#1DB954")
        ax.set_title("Listening Behavior")
        ax.set_xlabel("Hour of Day")
        ax.set_ylabel("Tracks Played")
        st.pyplot(fig)

        peak_hour = listening_hours.idxmax()
        personality, description = get_personality_label(peak_hour)
        st.header("Your Music Personality")
        st.success(f"**{personality}:** {description}")

        st.header("Additional Insight")
        st.markdown(f"""
            <div class="fun-insight-box">
                You're listening more during the {personality} hours. Music lover alert!
            </div>
        """, unsafe_allow_html=True)

else:
    st.write("Please log in to access your Spotify data.")
