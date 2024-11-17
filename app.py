import streamlit as st
from spotipy import Spotify
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
    h1, h2, h3, p {color: white !important;}
    .persona-card {background: #1a1a1a; color: white; padding: 20px; border-radius: 15px; margin: 20px; text-align: center;}
    .persona-title {font-size: 2.5em; font-weight: bold; margin-bottom: 10px;}
    .persona-desc {font-size: 1.2em; color: #cfcfcf;}
    .insights-box {display: flex; flex-wrap: wrap; background: #333; padding: 20px; border-radius: 15px; margin-top: 20px;}
    .insight-badge {flex: 1; margin: 10px; padding: 20px; background: #444; border-radius: 15px; text-align: center;}
    .cover-small {border-radius: 10px; margin: 10px; width: 80px; height: 80px;}
    .cover-circle {border-radius: 50%; margin: 10px; width: 80px; height: 80px;}
    </style>
""", unsafe_allow_html=True)

# Spotify OAuth Setup
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=scope
)

# User Login Section
if "token_info" not in st.session_state:
    auth_url = sp_oauth.get_authorize_url()
    st.markdown(f"[Log in to Spotify]({auth_url})")
    st.stop()
else:
    if "sp" not in st.session_state:
        token_info = sp_oauth.get_access_token()
        st.session_state["token_info"] = token_info
        st.session_state["sp"] = Spotify(auth=token_info["access_token"])

sp = st.session_state["sp"]

# Functions to fetch Spotify data
def fetch_spotify_data(sp_func, *args, **kwargs):
    try:
        return sp_func(*args, **kwargs)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def fetch_behavioral_data(week_type):
    today = datetime.today().date()
    start_date = today - timedelta(days=today.weekday() + (7 if week_type == "last" else 0))
    recent_plays = fetch_spotify_data(sp.current_user_recently_played, limit=50)
    
    if recent_plays:
        data = [
            {
                "played_at": item["played_at"],
                "track_name": item["track"]["name"],
                "artist_name": item["track"]["artists"][0]["name"]
            }
            for item in recent_plays["items"]
        ]
        df = pd.DataFrame(data)
        df["played_at"] = pd.to_datetime(df["played_at"])
        df["date"] = df["played_at"].dt.date
        return df[df["date"] >= start_date]
    return pd.DataFrame()

def fetch_top_data():
    top_tracks = fetch_spotify_data(sp.current_user_top_tracks, time_range="short_term", limit=5)
    top_artists = fetch_spotify_data(sp.current_user_top_artists, time_range="short_term", limit=5)
    genres = [genre for artist in top_artists["items"] for genre in artist["genres"]]
    return top_tracks, top_artists, genres

# Display Functions
def display_persona():
    st.markdown("""
    <div class="persona-card">
        <div class="persona-title">Rhythm Explorer</div>
        <div class="persona-desc">You're a Rhythm Explorer—your playlists are a map of the beats that move your soul.</div>
    </div>
    """, unsafe_allow_html=True)

def display_insights(data):
    if data.empty:
        st.warning("No recent play data available.")
        return
    
    unique_days = len(data["date"].unique())
    avg_hour = data["played_at"].dt.hour.mean()
    listener_type = "Day Explorer" if avg_hour < 18 else "Night Owl"
    unique_artists = data["artist_name"].nunique()

    st.markdown(f"""
    <div class="insights-box">
        <div class="insight-badge">🔥 Current Streak: <strong>{unique_days} days</strong></div>
        <div class="insight-badge">☀️🌙 Listener Type: <strong>{listener_type}</strong></div>
        <div class="insight-badge">🎨 Unique Artists: <strong>{unique_artists}</strong></div>
    </div>
    """, unsafe_allow_html=True)

def display_top_data(top_tracks, top_artists, genres):
    if top_tracks:
        st.subheader("Top Songs")
        for track in top_tracks["items"]:
            st.markdown(f"""
            <div style="display: flex; align-items: center;">
                <img src="{track['album']['images'][0]['url']}" class="cover-small">
                <div>{track['name']} by {', '.join(artist['name'] for artist in track['artists'])}</div>
            </div>
            """, unsafe_allow_html=True)
    
    if top_artists:
        st.subheader("Top Artists")
        for artist in top_artists["items"]:
            st.markdown(f"""
            <div style="display: flex; align-items: center;">
                <img src="{artist['images'][0]['url']}" class="cover-circle">
                <div>{artist['name']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    if genres:
        st.subheader("Top Genres")
        st.write(", ".join(genres[:5]))

def plot_heatmap(data):
    if data.empty:
        return
    heatmap_data = data.groupby([data["played_at"].dt.hour, data["played_at"].dt.weekday]).size().unstack(fill_value=0)
    plt.figure(figsize=(12, 6))
    sns.heatmap(heatmap_data, cmap="magma", annot=True)
    plt.title("Listening Heatmap (Hour vs Day)")
    plt.xlabel("Day of the Week")
    plt.ylabel("Hour of the Day")
    st.pyplot(plt)

# Main Application
page = st.sidebar.selectbox("Choose Page", ["Insights", "Your Music"])

if page == "Insights":
    week_type = "current" if datetime.today().weekday() < 4 else "last"
    behavioral_data = fetch_behavioral_data(week_type)
    top_tracks, top_artists, genres = fetch_top_data()

    display_persona()
    display_insights(behavioral_data)
    display_top_data(top_tracks, top_artists, genres)
    plot_heatmap(behavioral_data)

elif page == "Your Music":
    st.subheader("Your Liked Songs")
    liked_songs = fetch_spotify_data(sp.current_user_saved_tracks, limit=10)
    if liked_songs:
        for item in liked_songs["items"]:
            track = item["track"]
            st.markdown(f"""
            <div style="display: flex; align-items: center;">
                <img src="{track['album']['images'][0]['url']}" class="cover-small">
                <div>{track['name']} by {', '.join(artist['name'] for artist in track['artists'])}</div>
            </div>
            """, unsafe_allow_html=True)
