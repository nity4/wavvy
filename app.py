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
    .insights-box {display: flex; justify-content: space-between; flex-wrap: wrap; background: #333; padding: 20px; border-radius: 15px; margin-top: 20px;}
    .insight-badge {flex: 1 1 calc(33.333% - 20px); background: #444; color: white; margin: 10px; padding: 20px; border-radius: 15px; text-align: center; font-size: 1.2em; font-weight: bold; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.3);}
    .cover-small {border-radius: 10px; margin: 10px; width: 80px; height: 80px; object-fit: cover;}
    </style>
""", unsafe_allow_html=True)

# Helper functions
def refresh_access_token():
    try:
        if "token_info" in st.session_state:
            token_info = sp_oauth.refresh_access_token(st.session_state["token_info"]["refresh_token"])
            st.session_state["token_info"] = token_info
            return token_info["access_token"]
        else:
            st.error("No refresh token available. Please log in again.")
    except Exception as e:
        st.error(f"Failed to refresh token: {e}")
        return None

def initialize_spotify():
    if "token_info" in st.session_state:
        access_token = st.session_state["token_info"]["access_token"]
        return spotipy.Spotify(auth=access_token)
    return None

def fetch_spotify_data(sp_func, *args, **kwargs):
    for _ in range(2):  # Try twice: refresh token if expired
        try:
            return sp_func(*args, **kwargs)
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 401:  # Token expired
                refresh_access_token()
                st.session_state["sp"] = initialize_spotify()
            else:
                st.error(f"Spotify API error: {e}")
                return None
    return None

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

def fetch_top_data(sp):
    top_tracks = fetch_spotify_data(sp.current_user_top_tracks, limit=5, time_range="short_term")
    top_artists = fetch_spotify_data(sp.current_user_top_artists, limit=5, time_range="short_term")
    genres = [genre for artist in top_artists["items"] for genre in artist.get("genres", [])]
    return top_tracks, top_artists, genres

def display_persona():
    persona_name = "Rhythm Explorer"
    explanation = "You're a Rhythm Explorer—your playlists are like a map of the beats that move your soul."
    st.markdown(f"""
        <div class="persona-card">
            <div class="persona-title">{persona_name}</div>
            <div class="persona-desc">{explanation}</div>
        </div>
    """, unsafe_allow_html=True)

def display_insights(behavior_data):
    if behavior_data.empty:
        st.warning("No recent play data available.")
    else:
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

def display_top_data(top_tracks, top_artists, genres):
    if top_tracks and "items" in top_tracks:
        st.subheader("Your Top Songs")
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

    if top_artists and "items" in top_artists:
        st.subheader("Your Top Artists")
        for artist in top_artists["items"]:
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <img src="{artist['images'][0]['url']}" alt="Artist" class="cover-small">
                    <div>
                        <p><strong>{artist['name']}</strong></p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    if genres:
        st.subheader("Your Top Genres")
        st.markdown(", ".join(genres[:5]))

# Main application
def main():
    if "token_info" not in st.session_state:
        st.header("Log in to Spotify")
        auth_url = sp_oauth.get_authorize_url()
        st.markdown(f"[Click here to log in to Spotify]({auth_url})")
        response_url = st.text_input("Paste the redirected URL here after logging in:")
        if response_url:
            try:
                code = sp_oauth.parse_response_code(response_url)
                token_info = sp_oauth.get_access_token(code)
                st.session_state["token_info"] = token_info
                st.session_state["sp"] = initialize_spotify()
                st.success("Login successful! Reload the page to explore insights.")
            except Exception as e:
                st.error(f"Failed to log in: {e}")
    else:
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
            week_type = "current" if datetime.today().weekday() > 2 else "last"
            st.header(f"Insights & Behavior ({'Current Week' if week_type == 'current' else 'Last Week'})")
            behavior_data = fetch_behavioral_data(sp, week_type)
            top_tracks, top_artists, genres = fetch_top_data(sp)

            display_persona()
            display_insights(behavior_data)
            display_top_data(top_tracks, top_artists, genres)

# Run the app
if __name__ == "__main__":
    main()
