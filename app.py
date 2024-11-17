import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import pandas as pd
import matplotlib.pyplot as plt
from requests.exceptions import ReadTimeout

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

# Streamlit configuration
st.set_page_config(
    page_title="Wvvy",
    page_icon="〰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to authenticate user
def authenticate_user():
    if "token_info" not in st.session_state:
        query_params = st.experimental_get_query_params()
        if "code" in query_params:
            try:
                token_info = sp_oauth.get_access_token(query_params["code"][0])
                st.session_state["token_info"] = token_info
                st.experimental_set_query_params()  # Clear query params
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Authentication failed: {e}")
        else:
            auth_url = sp_oauth.get_authorize_url()
            st.markdown(f'<a href="{auth_url}" target="_self">**Login with Spotify**</a>', unsafe_allow_html=True)
    return "token_info" in st.session_state

# Function to refresh token if expired
def refresh_token():
    if "token_info" in st.session_state and sp_oauth.is_token_expired(st.session_state["token_info"]):
        st.session_state["token_info"] = sp_oauth.refresh_access_token(st.session_state["token_info"]["refresh_token"])

# Function to fetch Spotify data with error handling
def fetch_spotify_data(sp_func, *args, retries=5, **kwargs):
    for attempt in range(retries):
        try:
            return sp_func(*args, **kwargs)
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:  # Rate limit
                retry_after = int(e.headers.get("Retry-After", 1)) if e.headers and "Retry-After" in e.headers else 1
                st.warning(f"Rate limit reached. Retrying after {retry_after} seconds.")
                time.sleep(retry_after)
            else:
                st.warning(f"Attempt {attempt + 1} failed: {e}")
        except ReadTimeout:
            st.warning(f"Attempt {attempt + 1}: Timeout occurred. Retrying...")
        time.sleep(2 ** attempt)  # Exponential backoff for other errors
    st.error("Max retries reached. Skipping request.")
    return None

# Function to fetch audio features with retries
def fetch_audio_features(sp, track_id, retries=3):
    for attempt in range(retries):
        try:
            features = sp.audio_features([track_id])
            if features and isinstance(features, list) and features[0]:
                return features[0]
        except Exception as e:
            st.warning(f"Retry {attempt + 1}: Failed to fetch features for track {track_id}. Error: {e}")
        time.sleep(2 ** attempt)
    st.error(f"Max retries reached for track {track_id}. Skipping.")
    return {"energy": None, "valence": None, "tempo": None}

# Function to fetch liked songs with features
def get_liked_songs(sp):
    songs, offset = [], 0
    while True:
        results = fetch_spotify_data(sp.current_user_saved_tracks, limit=50, offset=offset)
        if not results or not results["items"]:
            break
        for item in results["items"]:
            track = item["track"]
            track_id = track.get("id")
            track_name = track.get("name", "Unknown Track")
            track_artist = track["artists"][0]["name"] if track["artists"] else "Unknown Artist"

            if not track_id:
                st.warning(f"Skipping track without valid ID: {track_name} by {track_artist}")
                continue

            features = fetch_audio_features(sp, track_id)
            if features:
                songs.append({
                    "Name": track_name,
                    "Artist": track_artist,
                    "Energy": features.get("energy"),
                    "Valence": features.get("valence"),
                    "Popularity": track.get("popularity", None)
                })
            else:
                st.warning(f"Skipping track: {track_name} by {track_artist}")
        offset += 50
    return pd.DataFrame(songs)

# Function to display insights
def display_insights(df):
    if df.empty:
        st.write("No data available.")
        return

    avg_energy = df["Energy"].mean()
    avg_valence = df["Valence"].mean()
    avg_popularity = df["Popularity"].mean()

    st.write("### Insights from Your Liked Songs")
    col1, col2, col3 = st.columns(3)
    col1.metric("Average Energy", f"{avg_energy:.2f}")
    col2.metric("Average Valence", f"{avg_valence:.2f}")
    col3.metric("Average Popularity", f"{avg_popularity:.1f}")

    st.write("#### Distribution of Energy and Valence")
    fig, ax = plt.subplots()
    df.plot.scatter(x="Energy", y="Valence", alpha=0.7, ax=ax)
    ax.set_title("Energy vs Valence")
    st.pyplot(fig)

# Main App Logic
if authenticate_user():
    refresh_token()
    sp = spotipy.Spotify(auth=st.session_state["token_info"]["access_token"])
    st.title("〰 Wvvy - Your Music Insights")

    tab1, _ = st.tabs(["Liked Songs Analysis", "Discover New Music"])
    with tab1:
        liked_songs_df = get_liked_songs(sp)
        if st.checkbox("Show Raw Data"):
            st.dataframe(liked_songs_df)
        display_insights(liked_songs_df)
else:
    st.write("Please log in to access your Spotify data.")
