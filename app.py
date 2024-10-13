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

# Listening Time Insights (Daily Listening for the Past Week)
def get_listening_time_insights(sp):
    recent_tracks = sp.current_user_recently_played(limit=50)
    timestamps = [track['played_at'] for track in recent_tracks['items']]
    
    time_data = pd.Series(pd.to_datetime(timestamps))
    daily_listening = time_data.dt.date.value_counts().sort_index()

    daily_minutes = {day: random.randint(20, 120) for day in daily_listening.index}  # Random minutes for demo
    
    return daily_listening, daily_minutes

# Genre Evolution Over Time
def get_genre_evolution(sp):
    top_artists_long_term = sp.current_user_top_artists(time_range='long_term', limit=50)['items']
    top_artists_short_term = sp.current_user_top_artists(time_range='short_term', limit=50)['items']
    
    long_term_genres = [genre for artist in top_artists_long_term for genre in artist['genres']]
    short_term_genres = [genre for artist in top_artists_short_term for genre in artist['genres']]

    # Display Top Genres
    unique_long_term_genres = set(long_term_genres)
    unique_short_term_genres = set(short_term_genres)
    new_genres = unique_short_term_genres - unique_long_term_genres
    
    return unique_long_term_genres, new_genres

# Mainstream vs Niche Insight
def get_niche_vs_mainstream_insight(sp, top_tracks):
    popularity_scores = [track['popularity'] for track in top_tracks['items']]
    
    avg_popularity = sum(popularity_scores) / len(popularity_scores)
    return avg_popularity

# Music Personality Page (Create Profile)
def personality_page(sp):
    st.header("Your Music Personality")

    top_tracks = sp.current_user_top_tracks(time_range='long_term', limit=50)
    top_artists = sp.current_user_top_artists(time_range='long_term', limit=5)
    
    # Listening Time and Track Count
    daily_listening, daily_minutes = get_listening_time_insights(sp)
    
    # Personality Traits and Colors
    genre_names, new_genres = get_genre_evolution(sp)
    genre_list = list(genre_names)
    dominant_genre = random.choice(genre_list) if genre_list else "pop"
    
    personality_map = {
        "pop": ("Groove Enthusiast", "#ffd700"),
        "rock": ("Melody Explorer", "#ff4081"),
        "indie": ("Rhythm Wanderer", "#00ff7f"),
        "jazz": ("Harmony Seeker", "#1e90ff"),
        "electronic": ("Beat Adventurer", "#8a2be2"),
        "hip hop": ("Vibe Creator", "#ff6347"),
        "classical": ("Tempo Navigator", "#00ced1")
    }
    personality_name, color = personality_map.get(dominant_genre, ("Groove Enthusiast", "#ffd700"))

    # Display Personality Name and Color
    st.markdown(f"<div style='background-color:{color}; padding:20px;'><h2>{personality_name}</h2></div>", unsafe_allow_html=True)
    st.write(f"Your music taste shows you're a **{personality_name}**. You vibe with {dominant_genre} music, and you're always on the lookout for something new.")

    # Display Listening Stats (Graph)
    st.subheader("Your Listening Stats Over the Last Week")
    daily_tracks = daily_listening.values
    days = list(daily_listening.index)
    minutes_listened = list(daily_minutes.values())

    fig, ax1 = plt.subplots()

    ax1.set_xlabel("Date")
    ax1.set_ylabel("Minutes Listened", color="tab:blue")
    ax1.bar(days, minutes_listened, color="tab:blue", alpha=0.6)
    
    ax2 = ax1.twinx()
    ax2.set_ylabel("Tracks Played", color="tab:green")
    ax2.plot(days, daily_tracks, color="tab:green", marker='o')

    fig.tight_layout()
    st.pyplot(fig)

    # Personality Insights
    st.subheader("What Your Music Says About You")
    st.write(f"As a **{personality_name}**, you're someone who loves to {dominant_genre} music. Whether it's chilling with some tracks or exploring new genres, your playlist is as unique as you are!")

# Main App Layout
if is_authenticated():
    try:
        refresh_token()
        sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

        # Reorganizing the Page Flow
        page = st.sidebar.radio("Navigation", [
            "Vibe Check", 
            "Your Top Hits", 
            "Music Personality"
        ])

        if page == "Vibe Check":
            discover_music_by_feelings(sp)
        elif page == "Your Top Hits":
            st.header("Your Top Hits and Insights")
            get_top_items_with_insights(sp)
            st.markdown("---")
            insights_rotator(sp)  # Add rotating insights (optional if needed)
        elif page == "Music Personality":
            personality_page(sp)

    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to VibeCheck")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
