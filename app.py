import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Spotify API credentials from Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

SCOPE = 'user-library-read user-top-read user-read-recently-played'

# Initialize Spotify OAuth
sp_oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE)

# App Layout and Configuration
st.set_page_config(page_title="Wvvy", page_icon="〰", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
    <style>
    .main {
        background-color: #f4f4f4;
        font-family: 'Courier New', Courier, monospace;
    }
    .stApp {
        background-image: linear-gradient(to right, #ff4081, #ff6347);
    }
    .header-title {
        font-size: 3em;
        color: white;
        font-weight: bold;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='header-title'>〰 Wvvy</div>", unsafe_allow_html=True)

# Authentication Functions
def is_authenticated():
    return st.session_state.get('token_info') is not None

def refresh_token():
    if st.session_state['token_info']:
        if sp_oauth.is_token_expired(st.session_state['token_info']):
            token_info = sp_oauth.refresh_access_token(st.session_state['token_info']['refresh_token'])
            st.session_state['token_info'] = token_info

def authenticate_user():
    try:
        if "code" in st.experimental_get_query_params():
            code = st.experimental_get_query_params()["code"][0]
            token_info = sp_oauth.get_access_token(code)
            st.session_state['token_info'] = token_info
            st.experimental_set_query_params(code=None)
            st.success("You're in. Refresh to access your music data.")
            if st.button("Refresh Now"):
                st.experimental_set_query_params()
        else:
            auth_url = sp_oauth.get_authorize_url()
            st.markdown(f'<a href="{auth_url}" target="_self" style="color: white; background-color: #ff4081; padding: 10px; border-radius: 8px;">Login with Spotify</a>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Authentication error: {e}")

# Helper Functions
def get_all_liked_songs(sp):
    liked_songs = []
    try:
        results = sp.current_user_saved_tracks(limit=50, offset=0)
        total_songs = results['total']

        while len(liked_songs) < total_songs:
            liked_songs.extend(results['items'])
            offset = len(liked_songs)
            results = sp.current_user_saved_tracks(limit=50, offset=offset)

    except Exception as e:
        st.error(f"Error fetching liked songs: {e}")
    
    return liked_songs

# Fetch Audio Features in Batches (Spotify API has a limit on batch size)
def fetch_audio_features_in_batches(sp, song_ids):
    features = []
    try:
        batch_size = 100  # Spotify's limit for batch requests
        for i in range(0, len(song_ids), batch_size):
            batch = song_ids[i:i + batch_size]
            audio_features = sp.audio_features(tracks=batch)
            features.extend(audio_features)
    except Exception as e:
        st.error(f"Error fetching audio features: {e}")
    
    return features

# Filter Liked Songs by Mood
def filter_liked_songs_by_mood(track_features, feeling, intensity):
    filtered_songs = []
    fallback_songs = []

    for track in track_features:
        valence = track.get('valence', 0)
        energy = track.get('energy', 0)
        danceability = track.get('danceability', 0)
        score = 0

        if feeling == "Happy":
            score += (valence - 0.6) * 10 + (energy - intensity / 5) * 5
        elif feeling == "Sad":
            score += (0.3 - valence) * 10 + (energy - 0.4) * 5
        elif feeling == "Chill":
            score += (0.4 - energy) * 7 + (danceability - 0.4) * 5
        elif feeling == "Hype":
            score += (energy - 0.7) * 12
        elif feeling == "Romantic":
            score += (valence - 0.5) * 5 + (danceability - 0.4) * 5
        elif feeling == "Adventurous":
            score += danceability * 5 + energy * 3

        if score > intensity * 1.2:
            filtered_songs.append(track)
        elif score > intensity * 0.8:
            fallback_songs.append(track)

    return filtered_songs if filtered_songs else fallback_songs

# Function for Mood-Based Music Discovery
def discover_music_by_feelings(sp):
    st.header("Curate Your Vibe")
    feeling = st.selectbox("What's your vibe today?", ["Happy", "Sad", "Chill", "Hype", "Romantic", "Adventurous"])
    intensity = st.slider(f"How {feeling} are you feeling?", 1, 5)

    try:
        liked_songs = get_all_liked_songs(sp)
        if len(liked_songs) > 0:
            random.shuffle(liked_songs)
            song_ids = [track['track']['id'] for track in liked_songs]
            features = fetch_audio_features_in_batches(sp, song_ids)
            filtered_songs = filter_liked_songs_by_mood(features, feeling, intensity)
        else:
            filtered_songs = []

        if filtered_songs:
            st.subheader(f"Here's your {feeling.lower()} playlist:")
            for i, feature in enumerate(filtered_songs[:10]):
                song = sp.track(feature['id'])
                song_name = song['name']
                artist_name = song['artists'][0]['name']
                album_cover = song['album']['images'][0]['url']
                st.image(album_cover, width=150, caption=f"{song_name} by {artist_name}")
        else:
            st.write(f"No tracks match your {feeling.lower()} vibe right now. Try tweaking the intensity or picking a different mood.")
    
    except Exception as e:
        st.error(f"Error curating your playlist: {e}")

# Top Songs, Artists, and Genres with Insights
def get_top_items_with_insights(sp):
    st.header("Your Top Songs, Artists, and Genres")
    time_range = st.radio("Select time range", ['This Week', 'This Month', 'This Year'], index=1)

    time_range_map = {'This Week': 'short_term', 'This Month': 'medium_term', 'This Year': 'long_term'}
    spotify_time_range = time_range_map[time_range]

    top_tracks = sp.current_user_top_tracks(time_range=spotify_time_range, limit=10)
    top_artists = sp.current_user_top_artists(time_range=spotify_time_range, limit=5)
    top_genres = [genre for artist in top_artists['items'] for genre in artist['genres'] if 'genres' in artist]

    st.subheader("Your Top Songs")
    for i, track in enumerate(top_tracks['items']):
        st.write(f"{i+1}. {track['name']} by {track['artists'][0]['name']}")
        st.image(track['album']['images'][0]['url'], width=60)

    st.subheader("Your Top Artists")
    for i, artist in enumerate(top_artists['items']):
        st.write(f"{i+1}. {artist['name']}")
        st.image(artist['images'][0]['url'], width=60)

    st.subheader("Your Top Genres")
    genre_df = pd.DataFrame(top_genres, columns=['Genre'])
    st.table(genre_df)

    # Insights at the Bottom
    st.write("## Insights")
    st.write("**Total Tracks Played This Week:** 120")  # Replace with actual values
    st.write("**Total Minutes Listened:** 320 minutes")  # Replace with actual values

# Listening Time Insights (Daily Listening for the Past Week)
def get_listening_time_insights(sp):
    recent_tracks = sp.current_user_recently_played(limit=50)
    timestamps = [track['played_at'] for track in recent_tracks['items']]
    
    time_data = pd.Series(pd.to_datetime(timestamps))
    daily_listening = time_data.dt.date.value_counts().sort_index()

    # Simulating daily minutes listened for demo purposes
    daily_minutes = {day: random.randint(20, 120) for day in daily_listening.index}  # Random minutes for demo
    
    return daily_listening, daily_minutes

# Music Personality Page (Create Profile)
def personality_page(sp):
    st.header("Your Music Personality")

    # Personality Traits and Colors
    genre_names = ["pop", "rock", "indie", "hip hop"]  # Demo genres
    dominant_genre = random.choice(genre_names)

    personality_map = {
        "pop": ("Groove Enthusiast", "#ffd700"),
        "rock": ("Melody Explorer", "#ff4081"),
        "indie": ("Rhythm Wanderer", "#00ff7f"),
        "hip hop": ("Vibe Creator", "#ff6347")
    }
    personality_name, color = personality_map.get(dominant_genre, ("Groove Enthusiast", "#ffd700"))

    # Display Personality Name and Color
    st.markdown(f"<div style='background-color:{color}; padding:20px;'><h2>{personality_name}</h2></div>", unsafe_allow_html=True)
    st.write(f"As a **{personality_name}**, you're someone who loves to vibe with **{dominant_genre}** music. You explore a lot of genres and enjoy blending different styles.")

    # Total Tracks Played and Total Minutes Listened
    total_tracks = 100  # Replace with actual data
    total_minutes = 250  # Replace with actual data

    # Display Total Stats Below the Graph
    daily_listening, daily_minutes = get_listening_time_insights(sp)

    st.write(f"**Total Tracks Played This Week:** {total_tracks}")
    st.write(f"**Total Minutes Listened This Week:** {total_minutes} minutes")

    # Display Listening Stats (Graph)
    st.subheader("Your Listening Stats Over the Last Week")
    daily_tracks = daily_listening.values
    days = list(daily_listening.index)
    minutes_listened = list(daily_minutes.values())

    fig, ax = plt.subplots(figsize=(10, 6))

    # Bar chart for minutes listened
    bars = ax.bar(days, minutes_listened, color=plt.cm.viridis(np.linspace(0.2, 0.8, len(days))), alpha=0.8)
    ax.set_xlabel("Day", fontsize=12)
    ax.set_ylabel("Minutes Listened", fontsize=12, color="#1e90ff")
    ax.set_title("Your Daily Listening Activity", fontsize=16)

    # Adding values on top of bars
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 2, f"{int(yval)}", ha='center', va='bottom', fontsize=10)

    # Line chart for tracks played
    ax2 = ax.twinx()
    ax2.plot(days, daily_tracks, color="#ff4081", marker='o', linewidth=2.5, label="Tracks Played")
    ax2.set_ylabel("Tracks Played", fontsize=12, color="#ff4081")

    # Add legends
    ax.legend(["Minutes Listened"], loc="upper left")
    ax2.legend(loc="upper right")

    # Grid and formatting
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    fig.tight_layout()

    st.pyplot(fig)

# Main App Layout
if is_authenticated():
    try:
        refresh_token()
        sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

        # Reorganizing the Page Flow
        page = st.sidebar.radio("Navigation", [
            "Wavvy", 
            "Your Top Hits", 
            "Music Personality"
        ])

        if page == "Wavvy":
            discover_music_by_feelings(sp)
        elif page == "Your Top Hits":
            st.header("Your Top Hits and Insights")
            get_top_items_with_insights(sp)
        elif page == "Music Personality":
            personality_page(sp)

    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to Wvvy")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
