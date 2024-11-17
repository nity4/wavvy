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
    .brand-box {text-align: center; margin: 20px 0;}
    .brand-logo {font-size: 3.5em; font-weight: bold; color: white;}
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
        # Check if we have the refresh token saved
        if "token_info" in st.session_state and "refresh_token" in st.session_state["token_info"]:
            token_info = sp_oauth.refresh_access_token(st.session_state["token_info"]["refresh_token"])
            st.session_state["token_info"] = token_info
            return token_info["access_token"]
        else:
            st.error("No refresh token available. Please log in again.")
            return None
    except Exception as e:
        st.error(f"Failed to refresh token: {e}")
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

# Main Application Logic
def main():
    if "token_info" not in st.session_state:
        st.header("Log in to Spotify")
        auth_url = sp_oauth.get_authorize_url()
        st.markdown(f"[Click here to log in to Spotify]({auth_url})")

        # Spotify Redirect URI Handling
        response_url = st.text_input("Paste the redirected URL here after logging in:")
        if response_url:
            try:
                code = sp_oauth.parse_response_code(response_url)
                token_info = sp_oauth.get_access_token(code)
                st.session_state["token_info"] = token_info
                st.session_state["sp"] = initialize_spotify()
                st.success("Login successful! Reload the page to start exploring your insights.")
            except Exception as e:
                st.error(f"Failed to log in: {e}")
    else:
        st.success("You are logged in to Spotify!")
        sp = st.session_state["sp"]

        # App Navigation
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
            today = datetime.today().date()
            week_type = "current" if today.weekday() > 2 else "last"  # Check if today is after Wednesday
            st.header(f"Insights & Behavior ({'Current Week' if week_type == 'current' else 'Last Week'})")
            # Insights logic here...

# Run the app
if __name__ == "__main__":
    main()
