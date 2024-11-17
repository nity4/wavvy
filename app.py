import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import random
import time

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
    page_title="Wvvy - Your Music Insights",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Design
st.markdown("""
    <style>
    body {background: linear-gradient(to right, black, #1DB954) !important; color: white;}
    .stApp {background: linear-gradient(to right, black, #1DB954) !important;}
    h1, h2, h3, p {color: white !important;}
    .cover {border-radius: 10px; margin: 5px;}
    .fun-insight-box {background: #333; padding: 15px; border-radius: 10px; margin-top: 20px; color: #1DB954;}
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

# Fetch Spotify Data
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

# Top Songs, Artists, and Genres
def get_top_items(sp, time_range="short_term"):
    top_tracks = fetch_spotify_data(sp.current_user_top_tracks, limit=10, time_range=time_range)
    top_artists = fetch_spotify_data(sp.current_user_top_artists, limit=10, time_range=time_range)
    genres = [genre for artist in top_artists["items"] for genre in artist.get("genres", [])]
    return top_tracks, top_artists, genres

# Behavioral Insights
def get_recently_played(sp):
    recent_plays = fetch_spotify_data(sp.current_user_recently_played, limit=50)
    hours = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ").hour for item in recent_plays["items"]]
    return pd.Series(hours).value_counts()

# Fun Personality Label
def get_personality_label(peak_hour):
    if 0 <= peak_hour <= 6:
        return "Night Owl", "Grooving at unholy hours like it's your personal rave."
    elif 7 <= peak_hour <= 12:
        return "Morning Motivator", "Starting your day like a main character in a feel-good movie."
    elif 13 <= peak_hour <= 18:
        return "Afternoon Explorer", "Finding hidden gems while sipping coffee and avoiding emails."
    else:
        return "Evening Relaxer", "Ending your day with vibes smoother than melted chocolate."

# Fun Insights
def generate_fun_insights(top_artists, top_tracks, genres):
    artist_count = len(top_artists["items"])
    genre_count = len(set(genres))
    track_count = len(top_tracks["items"])
    top_genre = genres[0] if genres else "Unknown"

    insights = [
        f"You explored {genre_count} unique genres. Spotify might owe you a curator's job.",
        f"Your top artist count is {artist_count}. You're either eclectic or indecisive.",
        f"Your favorite genre is {top_genre}. No surprises there, though, right?",
        f"You've been through {track_count} tracks this month. Professional procrastinator or secret DJ?",
        "Listening patterns indicate you're likely the person who sets the mood for group road trips."
    ]

    return random.choice(insights)

# Main App Logic
if authenticate_user():
    sp = spotipy.Spotify(auth=st.session_state["token_info"]["access_token"])

    st.title("Wvvy - Your Music Insights")

    # Top Songs, Artists, and Genres
    st.header("Top Music Insights")
    time_range = st.selectbox("Select Time Range:", ["Last Month", "Last 6 Months", "All Time"])
    time_map = {"Last Month": "short_term", "Last 6 Months": "medium_term", "All Time": "long_term"}
    top_tracks, top_artists, genres = get_top_items(sp, time_map[time_range])

    st.subheader("Top Tracks")
    for track in top_tracks["items"][:5]:
        album_cover = track["album"]["images"][0]["url"] if track["album"]["images"] else None
        st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <img src="{album_cover}" alt="Cover" width="80" height="80" class="cover">
                <div style="margin-left: 10px;">
                    <p><b>{track['name']}</b><br><i>{track['artists'][0]['name']}</i></p>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.subheader("Top Artists")
    for artist in top_artists["items"][:5]:
        artist_image = artist["images"][0]["url"] if artist["images"] else None
        st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <img src="{artist_image}" alt="Artist" width="80" height="80" class="cover">
                <div style="margin-left: 10px;">
                    <p><b>{artist['name']}</b></p>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.subheader("Top Genres")
    st.write(", ".join(set(genres[:5])))

    # Fun Insight
    st.write("### Fun Insight")
    fun_insight = generate_fun_insights(top_artists, top_tracks, genres)
    st.markdown(f"""
        <div class="fun-insight-box">
            <p>{fun_insight}</p>
        </div>
    """, unsafe_allow_html=True)

    # Listening Behavior
    st.header("Your Listening Behavior")
    listening_hours = get_recently_played(sp)
    peak_hour = listening_hours.idxmax()
    personality, description = get_personality_label(peak_hour)

    st.subheader("Listening Patterns Throughout the Day")
    fig, ax = plt.subplots()
    listening_hours.sort_index().plot(kind="bar", ax=ax, color="#1DB954")
    ax.set_title("Listening Behavior")
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Tracks Played")
    st.pyplot(fig)

    st.subheader("Your Music Personality")
    st.success(f"**{personality}:** {description}")

else:
    st.write("Please log in to access your Spotify data.")
