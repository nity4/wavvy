import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import pandas as pd
import random
import matplotlib.pyplot as plt
from requests.exceptions import ReadTimeout

# Spotify API credentials from Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Define scope for Spotify access
SCOPE = "user-library-read user-top-read playlist-read-private user-read-recently-played"

# Initialize Spotify OAuth object
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE
)

# Streamlit page config
st.set_page_config(page_title="Wvvy", page_icon="〰", layout="wide")

# Custom CSS for styling
st.markdown("""
    <style>
    body {background: linear-gradient(to right, black, #1DB954); color: white;}
    .header-title {text-align: center; font-size: 3em; font-weight: bold; color: white;}
    .button {background-color: #1DB954; color: white; padding: 10px; border-radius: 5px; font-weight: bold;}
    .insight-box {background-color: #333; padding: 15px; margin-bottom: 20px; border-radius: 10px; color: white;}
    .genre-text {font-size: 1.2em; color: #1DB954; font-weight: bold; margin-bottom: 10px;}
    .genre-text:hover {color: #66FF99;}
    </style>
""", unsafe_allow_html=True)

# Helper: Refresh token if expired
def refresh_token():
    if 'token_info' in st.session_state:
        token_info = st.session_state['token_info']
        if sp_oauth.is_token_expired(token_info):
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            st.session_state['token_info'] = token_info

# Helper: Spotify API call with error handling
def spotify_api_call(func, *args, **kwargs):
    for attempt in range(3):
        try:
            return func(*args, **kwargs)
        except spotipy.SpotifyException as e:
            if e.http_status == 429:  # Rate limit
                retry_after = int(e.headers.get("Retry-After", 1))
                time.sleep(retry_after)
            else:
                st.error(f"Spotify API Error: {e}")
                return None
        except ReadTimeout:
            time.sleep(1)
    return None

# Authentication
def authenticate_user():
    query_params = st.experimental_get_query_params()
    if "code" in query_params:
        try:
            token_info = sp_oauth.get_access_token(query_params["code"][0])
            st.session_state['token_info'] = token_info
            st.experimental_set_query_params()
            st.success("Authentication successful!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Error during authentication: {e}")
    else:
        auth_url = sp_oauth.get_authorize_url()
        st.markdown(f'<a href="{auth_url}" class="button">Login with Spotify</a>', unsafe_allow_html=True)

# Fetch user's liked songs
def get_liked_songs(sp):
    tracks = []
    offset = 0
    while True:
        results = spotify_api_call(sp.current_user_saved_tracks, limit=50, offset=offset)
        if not results or not results['items']:
            break
        for item in results['items']:
            tracks.append({
                "name": item['track']['name'],
                "artist": item['track']['artists'][0]['name'],
                "cover": item['track']['album']['images'][0]['url'] if item['track']['album']['images'] else None
            })
        offset += 50
    return tracks

# Display songs with covers
def display_songs(tracks, title):
    st.write(f"### {title}")
    for track in tracks:
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(track.get("cover", ""), width=80)
        with col2:
            st.write(f"**{track['name']}** by {track['artist']}")

# Fetch and display recommendations
def recommend_songs(sp, mood, intensity):
    mood_map = {"Happy": 0.8, "Calm": 0.3, "Energetic": 0.9, "Sad": 0.2}
    valence = mood_map[mood] * intensity / 5
    energy = mood_map[mood] * intensity / 5
    top_tracks = spotify_api_call(sp.current_user_top_tracks, limit=5)
    seed_tracks = [track['id'] for track in top_tracks['items']]

    if seed_tracks:
        recs = spotify_api_call(sp.recommendations, seed_tracks=seed_tracks, limit=10, target_valence=valence, target_energy=energy)
        if recs and 'tracks' in recs:
            tracks = [{"name": t['name'], "artist": t['artists'][0]['name'], "cover": t['album']['images'][0]['url']} for t in recs['tracks']]
            display_songs(tracks, "Recommended Songs")

# Display insights (top artists, genres, hidden gems)
def display_top_insights(sp):
    top_tracks = spotify_api_call(sp.current_user_top_tracks, limit=20)
    top_artists = spotify_api_call(sp.current_user_top_artists, limit=20)

    st.write("### Top Songs")
    if top_tracks:
        display_songs(top_tracks['items'], "Your Top Songs")
    st.write("### Top Artists")
    if top_artists:
        artists = [{"name": artist['name'], "cover": artist['images'][0]['url']} for artist in top_artists['items']]
        display_songs(artists, "Your Top Artists")

    # Extract and display top genres
    genres = [artist['genres'][0] for artist in top_artists['items'] if artist['genres']]
    if genres:
        st.markdown(f"<div class='genre-text'>Top Genres: {', '.join(set(genres))}</div>", unsafe_allow_html=True)

# Weekly listening pattern
def display_weekly_patterns(sp):
    results = spotify_api_call(sp.current_user_recently_played, limit=50)
    if results:
        hours = [pd.to_datetime(item['played_at']).hour for item in results['items']]
        df = pd.DataFrame(hours, columns=["Hour"])
        st.write("### Weekly Listening Pattern")
        st.line_chart(df["Hour"].value_counts().sort_index())

# Personality analysis
def analyze_personality(sp):
    top_artists = spotify_api_call(sp.current_user_top_artists, limit=50)
    if top_artists:
        total_artists = len(top_artists['items'])
        st.write("### Your Personality")
        if total_artists > 30:
            st.write("You are an Explorer: You love discovering new artists.")
        else:
            st.write("You are a Loyal Listener: You stick to your favorite artists.")

# Main app logic
if "token_info" in st.session_state:
    refresh_token()
    sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

    tab1, tab2, tab3 = st.tabs(["Liked Songs", "Discover New Music", "Insights"])
    
    with tab1:
        songs = get_liked_songs(sp)
        if songs:
            display_songs(random.sample(songs, min(len(songs), 20)), "Your Liked Songs")
        else:
            st.write("No liked songs found.")

    with tab2:
        mood = st.selectbox("Mood", ["Happy", "Calm", "Energetic", "Sad"])
        intensity = st.slider("Intensity", 1, 5, 3)
        recommend_songs(sp, mood, intensity)

    with tab3:
        display_top_insights(sp)
        display_weekly_patterns(sp)
        analyze_personality(sp)

else:
    st.write("<div class='header-title'>Welcome to Wvvy</div>", unsafe_allow_html=True)
    authenticate_user()
