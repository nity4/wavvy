import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import pandas as pd
import matplotlib.pyplot as plt
import time

# Spotify API credentials from Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

SCOPE = 'user-library-read user-top-read user-read-recently-played'

# Initialize Spotify OAuth
sp_oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE)

# App Layout and Configuration
st.set_page_config(page_title="VibeCheck", page_icon="🎧", layout="wide", initial_sidebar_state="expanded")
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
    .subheader-text {
        font-size: 1.5em;
        color: #ff4081;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='header-title'>VibeCheck</div>", unsafe_allow_html=True)

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

# Helper Function for Random Background Color Change (Gen Z Touch)
def random_color_bg():
    colors = ["#ff4081", "#00ff7f", "#1e90ff", "#ffd700", "#ff6347", "#8a2be2"]
    return random.choice(colors)

# Enhanced Mood-Based Music Discovery (New Default Page)
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

def filter_liked_songs_by_mood(track_features, feeling, intensity):
    filtered_songs = []
    fallback_songs = []
    
    for track in track_features:
        valence = track.get('valence', 0)
        energy = track.get('energy', 0)
        danceability = track.get('danceability', 0)
        tempo = track.get('tempo', 0)
        score = 0

        if feeling == "Happy":
            score += (valence - 0.6) * 10 + (energy - intensity / 5) * 5
        elif feeling == "Sad":
            score += (0.3 - valence) * 10 + (energy - 0.4) * 5
        elif feeling == "Chill":
            score += (0.4 - energy) * 7 + (danceability - 0.4) * 5
        elif feeling == "Hype":
            score += (energy - 0.7) * 12 + (tempo - 120) * 0.1
        elif feeling == "Romantic":
            score += (valence - 0.5) * 5 + (danceability - 0.4) * 5
        elif feeling == "Adventurous":
            score += danceability * 5 + (tempo - 120) * 0.1

        if score > intensity * 1.2:
            filtered_songs.append(track)
        elif score > intensity * 0.8:
            fallback_songs.append(track)

    return filtered_songs if filtered_songs else fallback_songs

# Listening Time Insights
def get_listening_time_insights(sp):
    st.subheader("Listening Time Insights")
    recent_tracks = sp.current_user_recently_played(limit=50)
    timestamps = [track['played_at'] for track in recent_tracks['items']]
    
    # Convert timestamps to hours for time-based analysis
    time_data = pd.to_datetime(timestamps)
    listening_hours = time_data.dt.hour.value_counts().sort_index()

    # Display insights
    st.write("Your most active listening hours:")
    st.bar_chart(listening_hours)

# Music Tempo Insights
def get_tempo_insights(sp, liked_songs):
    st.subheader("Tempo Insights")
    song_ids = [track['track']['id'] for track in liked_songs]
    audio_features = fetch_audio_features_in_batches(sp, song_ids)
    
    # Calculate average tempo
    tempos = [track['tempo'] for track in audio_features if track is not None]
    avg_tempo = sum(tempos) / len(tempos) if tempos else 0

    st.write(f"Your average song tempo is {avg_tempo:.2f} BPM.")

# Playlist Overlap
def get_playlist_overlap(sp):
    st.subheader("Playlist Overlap")
    playlists = sp.current_user_playlists(limit=10)['items']
    
    playlist_tracks = []
    for playlist in playlists:
        tracks = sp.playlist_tracks(playlist['id'])['items']
        playlist_tracks.extend([track['track']['id'] for track in tracks])

    # Compare liked songs with playlist tracks
    liked_songs = get_all_liked_songs(sp)
    liked_song_ids = [track['track']['id'] for track in liked_songs]
    
    overlap = set(liked_song_ids) & set(playlist_tracks)
    st.write(f"You have {len(overlap)} songs from your liked tracks in public playlists.")

# Genre Evolution Over Time
def get_genre_evolution(sp):
    st.subheader("Genre Evolution Over Time")
    top_artists_long_term = sp.current_user_top_artists(time_range='long_term', limit=50)['items']
    top_artists_short_term = sp.current_user_top_artists(time_range='short_term', limit=50)['items']
    
    long_term_genres = [genre for artist in top_artists_long_term for genre in artist['genres']]
    short_term_genres = [genre for artist in top_artists_short_term for genre in artist['genres']]

    # Calculate genre shifts
    unique_long_term_genres = set(long_term_genres)
    unique_short_term_genres = set(short_term_genres)
    new_genres = unique_short_term_genres - unique_long_term_genres
    
    st.write(f"Your genres are evolving! You've explored {len(new_genres)} new genres recently.")
    st.write(f"New genres: {', '.join(new_genres)}")

# Mainstream vs Niche Insight
def get_niche_vs_mainstream_insight(sp, top_tracks):
    st.subheader("Mainstream vs Niche Insights")
    popularity_scores = [track['popularity'] for track in top_tracks['items']]
    
    avg_popularity = sum(popularity_scores) / len(popularity_scores)
    if avg_popularity > 70:
        st.write("Your music taste is pretty mainstream.")
    else:
        st.write("You're into niche, lesser-known tracks.")

# Enhanced Data Visualization
def plot_genre_distribution(genre_df):
    if len(genre_df) > 0:
        genre_chart = genre_df['Genre'].value_counts().plot(kind='bar', title='Top Genres Distribution', color='skyblue')
        plt.ylabel("Count")
        plt.xlabel("Genres")
        st.pyplot(plt)
    else:
        st.write("No genre data available to display.")

# Personality Page
def personality_page(sp):
    st.header("Building Your Music Personality...")

    top_tracks = sp.current_user_top_tracks(time_range='long_term', limit=50)
    top_genres = [genre for artist in top_tracks['items'] for genre in artist['artists'][0].get('genres', [])]

    genre_preference = random.choice(top_genres) if top_genres else "pop"
    personality_map = {
        "pop": ("Groove Enthusiast", "#ffd700"),
        "rock": ("Melody Explorer", "#ff4081"),
        "indie": ("Rhythm Wanderer", "#00ff7f"),
        "jazz": ("Harmony Seeker", "#1e90ff"),
        "electronic": ("Beat Adventurer", "#8a2be2"),
        "hip hop": ("Vibe Creator", "#ff6347"),
        "classical": ("Tempo Navigator", "#00ced1")
    }

    fun_personality_name, associated_color = personality_map.get(genre_preference, ("Groove Enthusiast", "#ffd700"))

    progress = st.progress(0)
    for i in range(1, 101, 20):
        time.sleep(0.5)
        progress.progress(i)
    progress.empty()

    st.markdown(f'<div class="fun-bg" style="background-color:{associated_color};"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="fun-personality" style="color:{associated_color};">{fun_personality_name}</div>', unsafe_allow_html=True)
    
    st.write(f"As a **{fun_personality_name}**, you vibe with music that takes you places. You're not just listening—you're living.")
    st.write("You love to mix it up, keeping things fresh and never settling for the mainstream. Your playlist is as unique as you are.")

# Main App Layout
if is_authenticated():
    try:
        refresh_token()
        sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

        # Reorganizing the Page Flow
        page = st.sidebar.radio("Navigation", [
            "Vibe Check", 
            "Your Top Hits", 
            "Music Personality", 
            "Listening Insights", 
            "Extra Insights"
        ])

        if page == "Vibe Check":
            discover_music_by_feelings(sp)
        elif page == "Your Top Hits":
            get_top_items_with_insights(sp)
        elif page == "Music Personality":
            personality_page(sp)
        elif page == "Listening Insights":
            get_listening_time_insights(sp)
            get_tempo_insights(sp, get_all_liked_songs(sp))
            get_playlist_overlap(sp)
            get_genre_evolution(sp)
        elif page == "Extra Insights":
            get_niche_vs_mainstream_insight(sp, sp.current_user_top_tracks(time_range='long_term', limit=10))

    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to VibeCheck")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
