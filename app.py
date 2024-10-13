import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import time

# Spotify API credentials from Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

SCOPE = 'user-library-read user-top-read user-read-recently-played'

# Initialize Spotify OAuth
sp_oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE)

# Streamlit App Layout with Sleek Design
st.set_page_config(page_title="Wavvy", page_icon="🌊", layout="centered", initial_sidebar_state="collapsed")

# Custom CSS for modern and interactive design
st.markdown(
    """
    <style>
    body {
        background-color: #f5f5f5;
        color: #000000;
        font-family: 'Roboto', sans-serif;
    }
    .stButton>button {
        background-color: #0073e6;
        color: #ffffff;
        border-radius: 12px;
        font-size: 1rem;
        padding: 0.5rem;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #ff4081;
    }
    .stImage {
        border-radius: 15px;
        margin-bottom: 12px;
    }
    h1, h2, h3 {
        font-weight: 400;
        color: #ff4081;
    }
    .insight-box {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 15px;
        margin-left: 20px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
    }
    .insight-header {
        color: #0073e6;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .insight-detail {
        color: #000000;
        font-size: 1rem;
        margin-top: 10px;
    }
    .fun-personality {
        font-size: 2rem;
        font-weight: bold;
    }
    .fun-bg {
        width: 100%;
        height: 50px;
        margin-bottom: 20px;
        border-radius: 5px;
    }
    .loading {
        font-size: 1.5rem;
        color: #ff4081;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True
)

# Authentication Helpers
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
            st.success("You're authenticated! Refresh to get your music data.")
            if st.button("Refresh Now"):
                st.experimental_set_query_params()
        else:
            auth_url = sp_oauth.get_authorize_url()
            st.markdown(f'<a href="{auth_url}" target="_self" style="color: #ff4081;">Login with Spotify</a>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Authentication error: {e}")

# Fetch all liked songs from the user's library
def get_all_liked_songs(sp):
    liked_songs = []
    results = sp.current_user_saved_tracks(limit=50, offset=0)
    total_songs = results['total']
    
    while len(liked_songs) < total_songs:
        liked_songs.extend(results['items'])
        offset = len(liked_songs)
        results = sp.current_user_saved_tracks(limit=50, offset=offset)
    
    return liked_songs

# Fetch audio features in batches to avoid the 414 error
def fetch_audio_features_in_batches(sp, song_ids):
    features = []
    batch_size = 100  # Spotify's limit for batch requests

    for i in range(0, len(song_ids), batch_size):
        batch = song_ids[i:i + batch_size]
        audio_features = sp.audio_features(tracks=batch)
        features.extend(audio_features)

    return features

# Improved filtering of liked songs by mood and intensity
def filter_liked_songs_by_mood(track_features, feeling, intensity):
    filtered_songs = []
    fallback_songs = []
    
    for track in track_features:
        valence = track.get('valence', 0)
        energy = track.get('energy', 0)
        danceability = track.get('danceability', 0)
        tempo = track.get('tempo', 0)
        score = 0

        # Adjust the scoring to match mood and intensity
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

        # Use more lenient fallback filtering
        if score > intensity * 1.2:
            filtered_songs.append(track)
        elif score > intensity * 0.8:
            fallback_songs.append(track)

    # If no exact matches found, return fallback songs
    return filtered_songs if filtered_songs else fallback_songs

# Recommend new songs based on user's listening habits and mood
def recommend_new_songs_by_mood(sp, recent_tracks, feeling, intensity):
    # Analyze recent listening patterns to match with recommendations
    genres = set([genre for track in recent_tracks for genre in track['track']['artists'][0].get('genres', [])])
    seed_genres = list(genres)[:2] if genres else ["pop"]
    seed_tracks = [track['track']['id'] for track in recent_tracks[:5]] if recent_tracks else None

    # Request recommendations from Spotify based on mood and recent habits
    recommendations = sp.recommendations(seed_tracks=seed_tracks, seed_genres=seed_genres, limit=20)
    
    # Filter recommendations by mood
    song_ids = [track['id'] for track in recommendations['tracks']]
    audio_features = fetch_audio_features_in_batches(sp, song_ids)
    
    filtered_songs = filter_liked_songs_by_mood(audio_features, feeling, intensity)
    
    return filtered_songs

# Mood-Based Music Discovery with enhanced fallback mechanism
def discover_music_by_feelings(sp):
    st.header("Curated Music for Your Mood")
    st.write("Select your mood, and we'll build the perfect playlist.")

    feeling = st.selectbox("What's your vibe today?", ["Happy", "Sad", "Chill", "Hype", "Romantic", "Adventurous"])
    intensity = st.slider(f"How {feeling} are you feeling?", 1, 5)  # Intensity is now between 1-5
    
    # Option to choose between liked songs and new songs
    song_source = st.radio("Pick your song source:", ["Liked Songs", "Discover New Songs"], index=0)

    try:
        if song_source == "Liked Songs":
            liked_songs = get_all_liked_songs(sp)
            if len(liked_songs) > 0:
                random.shuffle(liked_songs)  # Shuffle to avoid bias from first tracks
                song_ids = [track['track']['id'] for track in liked_songs]
                features = fetch_audio_features_in_batches(sp, song_ids)
                filtered_songs = filter_liked_songs_by_mood(features, feeling, intensity)
            else:
                filtered_songs = []
        else:
            # Analyze user's recent listening habits
            recent_tracks = sp.current_user_recently_played(limit=50)['items']
            filtered_songs = recommend_new_songs_by_mood(sp, recent_tracks, feeling, intensity)

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

# Insights Page with Top Songs, Artists, and Genres
def get_top_items_with_insights(sp):
    st.header("Your Top Songs, Artists, and Genres with Creative Insights")

    time_range = st.radio("Select time range", ['This Week', 'This Month', 'This Year'], index=1, key="time_range_radio")
    time_range_map = {'This Week': 'short_term', 'This Month': 'medium_term', 'This Year': 'long_term'}
    spotify_time_range = time_range_map[time_range]

    # Fetch top tracks, artists, and genres
    top_tracks = sp.current_user_top_tracks(time_range=spotify_time_range, limit=10)
    top_artists = sp.current_user_top_artists(time_range=spotify_time_range, limit=5)
    top_genres = [genre for artist in top_artists['items'] for genre in artist['genres'] if 'genres' in artist and artist['genres']]

    col1, col2 = st.columns([3, 1])

    # Display top songs, artists, and genres on the left (col1)
    with col1:
        if top_tracks['items']:
            st.subheader("Your Top Songs")
            for i, track in enumerate(top_tracks['items']):
                song_name = track['name']
                artist_name = track['artists'][0]['name']
                album_cover = track['album']['images'][0]['url']
                st.image(album_cover, width=100, caption=f"{song_name} by {artist_name}")

        if top_artists['items']:
            st.subheader("Your Top Artists")
            for i, artist in enumerate(top_artists['items']):
                artist_name = artist['name']
                artist_cover = artist['images'][0]['url']
                st.image(artist_cover, width=100, caption=f"{artist_name}")

        if top_genres:
            st.subheader("Your Top Genres")
            unique_genres = list(set(top_genres))[:5]
            if unique_genres:
                st.write("You're currently into these genres:")
                for genre in unique_genres:
                    icon = "🎸" if "rock" in genre else "🎶"
                    st.write(f"<span class='genre-icon'>{icon}</span> {genre.capitalize()}", unsafe_allow_html=True)

    # Display insights on the right (col2) inside a box
    with col2:
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        st.markdown('<div class="insight-header">Creative Insights</div>', unsafe_allow_html=True)

        genre_count = len(set(top_genres))
        st.write(f"<div class='insight-detail'>You've explored {genre_count} different genres. You have a broad taste in music!</div>", unsafe_allow_html=True)

        # Interesting insight based on artist discovery
        new_artists = len(set(artist['name'] for artist in top_artists['items']))
        st.write(f"<div class='insight-detail'>You've discovered {new_artists} new artists during this {time_range.lower()}.</div>", unsafe_allow_html=True)

        adventurous_genre = random.choice(unique_genres) if unique_genres else "pop"
        st.write(f"<div class='insight-detail'>Your most adventurous genre is {adventurous_genre.capitalize()}, you're always looking for something unique!</div>", unsafe_allow_html=True)
        
        # A standout insight: Song most played during a specific time
        if top_tracks['items']:
            most_played_song = top_tracks['items'][0]['name']
            st.write(f"<div class='insight-detail'>The song you can't get enough of this {time_range.lower()} is {most_played_song}!</div>", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

# Personality Page with loading effect
def personality_page():
    st.header("Building Your Music Personality...")

    # Add a "loading" effect but no flickering
    progress = st.progress(0)
    for i in range(1, 101, 20):
        time.sleep(0.5)
        progress.progress(i)
    progress.empty()

    # Fun personality name generation with fixed colors
    personality_map = {
        "Melody Explorer": "#ff4081",
        "Groove Enthusiast": "#ffd700",
        "Rhythm Wanderer": "#00ff7f",
        "Harmony Seeker": "#1e90ff",
        "Beat Adventurer": "#8a2be2",   # New Personality
        "Vibe Creator": "#ff6347",      # New Personality
        "Tempo Navigator": "#00ced1"    # New Personality
    }
    
    fun_personality_name, associated_color = random.choice(list(personality_map.items()))

    # Display color visually with a fun background
    st.markdown(f'<div class="fun-bg" style="background-color:{associated_color};"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="fun-personality" style="color:{associated_color};">{fun_personality_name}</div>', unsafe_allow_html=True)
    
    # Personality description in Gen Z lingo
    st.write(f"As a **{fun_personality_name}**, you vibe with music that takes you places. You're not just listening—you're living.")
    st.write("You love to mix it up, keeping things fresh and never settling for the mainstream. Your playlist is as unique as you are.")
    st.write("You're the kind of person who discovers new tracks before anyone else. Keep being the trendsetter you are!")
    
    # Awarding a fun "Music Trophy" based on personality
    music_trophies = {
        "Melody Explorer": "Golden Ear Trophy 🏆",
        "Groove Enthusiast": "Beat King/Queen Crown 👑",
        "Rhythm Wanderer": "Sound Explorer's Badge 🏅",
        "Harmony Seeker": "Harmony Master Medallion 🎖️",
        "Beat Adventurer": "Adventure Beat Trophy 🏆",
        "Vibe Creator": "Vibe Star Medal 🌟",
        "Tempo Navigator": "Tempo Master Cup 🏆"
    }
    
    st.subheader(f"You've earned the {music_trophies[fun_personality_name]}!")

# Main App Flow
if is_authenticated():
    try:
        refresh_token()
        sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

        # Page switching options displayed on screen
        page = st.radio("Choose a Page", [
            "Mood-Based Music Discovery", 
            "Your Top Songs, Artists, and Genres with Insights",
            "Your Listening Personality"
        ], key="main_radio")

        if page == "Mood-Based Music Discovery":
            discover_music_by_feelings(sp)
        elif page == "Your Top Songs, Artists, and Genres with Insights":
            get_top_items_with_insights(sp)
        elif page == "Your Listening Personality":
            personality_page()

    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to **Wavvy**")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
