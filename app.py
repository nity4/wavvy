import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import random
import time

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
    page_title="WVY - Your Spotify Companion",
    page_icon="🌊",
    layout="wide"
)

# CSS for Styling
st.markdown("""
    <style>
    body {background: linear-gradient(to right, black, #1DB954) !important; color: white;}
    .stApp {background: linear-gradient(to right, black, #1DB954) !important;}
    h1, h2, h3, p {color: white !important;}
    .brand {position: absolute; top: 20px; left: 20px; font-size: 3.5em; font-weight: bold; color: white;}
    .cover-circle {border-radius: 50%; margin: 10px; width: 80px; height: 80px;}
    .fun-insight-box {background: #333; color: white; padding: 15px; border-radius: 10px; margin-top: 20px; font-size: 1.2em; line-height: 1.5;}
    .personalized-box {background: #444; color: white; padding: 20px; border-radius: 15px; margin-top: 20px; font-size: 1.3em; line-height: 1.6;}
    .gift-box {background: #1DB954; color: black; padding: 20px; border-radius: 15px; margin-top: 20px; font-size: 1.5em; font-weight: bold; text-align: center;}
    .chart-title {color: white; text-align: center; font-size: 1.5em; margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

# Refresh Token Function
def refresh_access_token():
    if "token_info" in st.session_state:
        try:
            token_info = sp_oauth.refresh_access_token(st.session_state["token_info"]["refresh_token"])
            st.session_state["token_info"] = token_info
            return token_info["access_token"]
        except Exception as e:
            st.error(f"Failed to refresh access token: {e}")
            return None
    else:
        st.error("No token info found. Please log in again.")
        return None

# Fetch Spotify Data Function
def fetch_spotify_data(sp_func, *args, retries=3, **kwargs):
    delay = 1
    for attempt in range(1, retries + 1):
        try:
            return sp_func(*args, **kwargs)
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 401:
                st.warning("Access token expired. Refreshing token...")
                new_token = refresh_access_token()
                if new_token:
                    global sp
                    sp = spotipy.Spotify(auth=new_token)
                else:
                    st.error("Failed to refresh access token. Please log in again.")
                    return None
            elif "rate limit" in str(e).lower():
                st.warning(f"Rate limit hit. Retrying in {delay} seconds... (Attempt {attempt}/{retries})")
                time.sleep(delay)
                delay *= 2
            else:
                st.warning(f"Attempt {attempt} failed: {e}")
                time.sleep(delay)
        delay *= 2
    st.error("Failed to fetch data after multiple retries. Please try again later.")
    return None

# Authentication
def authenticate_user():
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
            st.markdown(f'<a href="{auth_url}" target="_self" style="color: white; text-decoration: none; background-color: #1DB954; padding: 10px 20px; border-radius: 5px;">Login with Spotify</a>', unsafe_allow_html=True)
    return "token_info" in st.session_state

# Fetch Top Data
def fetch_top_data(sp):
    if "top_data" not in st.session_state:
        top_tracks = fetch_spotify_data(sp.current_user_top_tracks, limit=5, time_range="short_term")
        top_artists = fetch_spotify_data(sp.current_user_top_artists, limit=5, time_range="short_term")
        genres = [genre for artist in top_artists["items"] for genre in artist.get("genres", [])]
        st.session_state["top_data"] = (top_tracks, top_artists, genres)
    return st.session_state["top_data"]

# Fetch Behavioral Data (Last Month Only)
def fetch_behavioral_data(sp):
    if "behavior_data" not in st.session_state:
        recent_plays = fetch_spotify_data(sp.current_user_recently_played, limit=50)
        last_month_date = datetime.now() - timedelta(days=30)
        filtered_plays = [item for item in recent_plays["items"] if datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ") >= last_month_date]
        hours = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ").hour for item in filtered_plays]
        weekdays = [datetime.strptime(item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ").weekday() for item in filtered_plays]
        st.session_state["behavior_data"] = (pd.Series(hours).value_counts(), pd.Series(weekdays).value_counts())
    return st.session_state["behavior_data"]

# Main App Logic
if authenticate_user():
    sp = spotipy.Spotify(auth=st.session_state["token_info"]["access_token"])

    st.markdown('<div class="brand">WVY</div>', unsafe_allow_html=True)

    page = st.radio("Navigate to:", ["Top Insights", "Behavior"])

    if page == "Top Insights":
        st.title("Your Top Insights")
        top_tracks, top_artists, genres = fetch_top_data(sp)

        # Top Songs Section
        st.header("Your Top Songs")
        for track in top_tracks["items"]:
            st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <img src="{track['album']['images'][0]['url']}" alt="Cover" class="cover-circle">
                    <div style="margin-left: 10px;">
                        <p style="margin: 0;"><strong>{track['name']}</strong></p>
                        <p style="margin: 0;">by {track['artists'][0]['name']}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Top Artists Section
        st.header("Your Top Artists")
        for artist in top_artists["items"]:
            st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <img src="{artist['images'][0]['url']}" alt="Artist Cover" class="cover-circle">
                    <div style="margin-left: 10px;">
                        <p style="margin: 0;"><strong>{artist['name']}</strong></p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Genres Section
        st.header("Genres You Vibe With")
        st.write(", ".join(genres[:5]))

        # Fun Insights
        st.header("Fun Insights")
        insights = [
            f"🎧 Your top genre this month is: <strong>{random.choice(genres).capitalize()}</strong>.",
            f"🎵 You've jammed to <strong>{len(top_tracks['items'])} top songs</strong> this month.",
            f"🔥 You're vibing with {len(top_artists['items'])} amazing artists!"
        ]
        for insight in insights:
            st.markdown(f"""
                <div class="fun-insight-box">
                    {insight}
                </div>
            """)

    elif page == "Behavior":
        st.title("Your Personalized Music Behavior")
        listening_hours, listening_weekdays = fetch_behavioral_data(sp)

        # Hourly Listening Trends
        st.header("Hourly Listening Trends")
        fig, ax = plt.subplots()
        listening_hours.sort_index().plot(kind="bar", ax=ax, color="#1DB954")
        ax.set_title("Hourly Listening Trends", fontsize=16, color="white")
        ax.set_xlabel("Hour of the Day", fontsize=12, color="white")
        ax.set_ylabel("Tracks Played", fontsize=12, color="white")
        ax.tick_params(colors='white')
        fig.patch.set_alpha(0)
        ax.set_facecolor("none")
        st.pyplot(fig)

        # Weekly Listening Trends
        st.header("Weekly Listening Trends")
        fig, ax = plt.subplots()
        listening_weekdays.sort_index().plot(kind="line", ax=ax, color="#1DB954", marker="o")
        ax.set_title("Weekly Listening Trends", fontsize=16, color="white")
        ax.set_xlabel("Day of the Week (0=Monday, 6=Sunday)", fontsize=12, color="white")
        ax.set_ylabel("Tracks Played", fontsize=12, color="white")
        ax.tick_params(colors='white')
        fig.patch.set_alpha(0)
        ax.set_facecolor("none")
        st.pyplot(fig)

        # Music Personality
        peak_hour = listening_hours.idxmax()
        if peak_hour >= 18:
            personality = "🎶 Night Owl"
            description = "You thrive in the nighttime melodies and vibe when the world sleeps."
        elif peak_hour < 12:
            personality = "☀️ Morning Melodist"
            description = "Your mornings are powered by rhythms, fueling your energy for the day."
        else:
            personality = "🌇 Daytime Dreamer"
            description = "You groove during the day, making every moment a music video."

        st.markdown(f"""
            <div class="gift-box">
                Your Music Personality: {personality}
            </div>
            <div class="personalized-box">
                {description}
            </div>
        """)

else:
    st.write("Please log in to access your Spotify data.")
