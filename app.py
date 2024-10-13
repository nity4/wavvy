import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random

# Spotify API credentials from Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Spotify OAuth Scope to access user's full library and other data
SCOPE = 'user-library-read user-top-read user-read-recently-played'

# Initialize Spotify OAuth
sp_oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE)

# Streamlit App Layout with Sleek Design
st.set_page_config(page_title="Wavvy", page_icon="🌊", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for Modern, Visual Appeal
st.markdown(
    """
    <style>
    body {
        background-color: #121212;
        color: #f5f5f5;
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
    .header-text {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #ff4081;
    }
    .subheader-text {
        font-size: 1.25rem;
        color: #ffffff;
        font-weight: 500;
    }
    .icon-genres {
        font-size: 1.25rem;
        margin-right: 10px;
    }
    .spacer {
        margin-top: 2rem;
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

# Mood-Based Music Discovery: Suggest new music based on mood
def mood_based_music_discovery(sp):
    st.markdown('<div class="header-text">Mood-Based Music Discovery</div>', unsafe_allow_html=True)
    st.write("Select your mood, and we'll suggest some songs from your library and new ones based on it.")

    feeling = st.selectbox("What's your vibe today?", ["Happy", "Sad", "Chill", "Hype", "Romantic", "Adventurous"])
    intensity = st.slider(f"How {feeling} are you feeling?", 1, 10)

    try:
        # Fetch user's liked songs
        liked_songs = get_all_liked_songs(sp)
        random.shuffle(liked_songs)
        song_ids = [track['track']['id'] for track in liked_songs]

        # Fetch audio features in batches
        features = fetch_audio_features_in_batches(sp, song_ids)

        # Placeholder for actual mood-based filtering
        # Adjust features according to feeling and intensity (replace with real logic)
        filtered_songs = liked_songs[:10]  # Limit for now, just to display some results

        st.markdown(f"<div class='subheader-text'>Your {feeling.lower()} playlist:</div>", unsafe_allow_html=True)
        for i, song_data in enumerate(filtered_songs):
            song = song_data['track']
            song_name = song['name']
            artist_name = song['artists'][0]['name']
            album_cover = song['album']['images'][0]['url']
            st.image(album_cover, width=150, caption=f"{song_name} by {artist_name}")
        
        st.write("Stay tuned for new song suggestions based on your mood!")
        
    except Exception as e:
        st.error(f"Error curating your playlist: {e}")

# Fetch top songs, artists, and genres with insights
def music_insights(sp, time_range):
    col1, col2 = st.columns(2)

    # Left side: Top Songs, Artists, and Genres
    with col1:
        st.markdown('<div class="header-text">Your Top Songs, Artists & Genres</div>', unsafe_allow_html=True)

        # Fetch top tracks
        top_tracks = sp.current_user_top_tracks(time_range=time_range, limit=10)
        if top_tracks['items']:
            st.markdown('<div class="subheader-text">Top Songs</div>', unsafe_allow_html=True)
            for i, track in enumerate(top_tracks['items']):
                song_name = track['name']
                artist_name = track['artists'][0]['name']
                album_cover = track['album']['images'][0]['url']
                st.image(album_cover, width=150, caption=f"{i+1}. {song_name} by {artist_name}")

        # Fetch top artists
        top_artists = sp.current_user_top_artists(time_range=time_range, limit=5)
        if top_artists['items']:
            st.markdown('<div class="subheader-text">Top Artists</div>', unsafe_allow_html=True)
            for i, artist in enumerate(top_artists['items']):
                artist_name = artist['name']
                artist_cover = artist['images'][0]['url']
                st.image(artist_cover, width=150, caption=f"{i+1}. {artist_name}")

        # Fetch top genres
        if top_artists['items']:
            st.markdown('<div class="subheader-text">Top Genres</div>', unsafe_allow_html=True)
            all_genres = [genre for artist in top_artists['items'] for genre in artist['genres']]
            unique_genres = list(set(all_genres))[:5]  # Limit to 5 unique genres
            if unique_genres:
                genre_icons = {"pop": "🎤", "rock": "🎸", "hip hop": "🎧", "classical": "🎻", "electronic": "🎹"}
                for genre in unique_genres:
                    genre_icon = genre_icons.get(genre.lower(), "🎵")
                    st.write(f"<span class='icon-genres'>{genre_icon}</span>{genre.capitalize()}", unsafe_allow_html=True)

    # Right side: Insights
    with col2:
        st.markdown('<div class="header-text">Music Insights</div>', unsafe_allow_html=True)

        if top_artists['items'] and top_tracks['items']:
            most_played_artist = top_artists['items'][0]['name']
            most_played_song = top_tracks['items'][0]['name']

            st.markdown(f"**Most Played Artist**: {most_played_artist}")
            st.markdown(f"**Most Played Song**: {most_played_song}")

            # Fun insights
            new_artists = len(set(track['artists'][0]['name'] for track in top_tracks['items']))
            st.markdown(f"**New Artists Discovered**: {new_artists}")

            all_genres = [genre for artist in top_artists['items'] for genre in artist['genres']]
            genre_count = len(set(all_genres))
            st.markdown(f"**Unique Genres**: {genre_count}")

            repeat_songs = random.choice(top_tracks['items'])['name']
            st.markdown(f"**Replay Favorite**: {repeat_songs}")
        else:
            st.write("Not enough data to display insights.")

# Music Personality Analysis
def music_personality_analysis(sp):
    st.markdown('<div class="header-text">Discover Your Music Personality</div>', unsafe_allow_html=True)
    st.write("Explore your unique music personality based on your listening habits!")

    try:
        top_tracks = sp.current_user_top_tracks(time_range='long_term', limit=50)
        top_artists = sp.current_user_top_artists(time_range='long_term', limit=50)

        if top_tracks['items'] and top_artists['items']:
            total_artists = len(set(track['artists'][0]['name'] for track in top_tracks['items']))
            all_genres = [genre for artist in top_artists['items'] for genre in artist['genres']]
            genre_count = len(set(all_genres))

            st.markdown(f"**Artist Diversity**: You've listened to **{total_artists}** unique artists!")
            st.markdown(f"**Genre Range**: You enjoy **{genre_count}** different genres of music.")

            st.markdown("### Your Music Personality:")
            if genre_count > 10:
                personality = "Genre Explorer"
                color = "#ff4081"
            elif total_artists > 30:
                personality = "Superfan"
                color = "#0073e6"
            else:
                personality = "Mood Listener"
                color = "#ffcc00"

            st.markdown(f"<div style='color:{color}; font-size:1.5rem;'>You're a **{personality}**!</div>", unsafe_allow_html=True)
            st.write("Your music reflects your passion for diverse genres and unique sounds!")
            
        else:
            st.write("Not enough data to analyze your music personality.")

    except Exception as e:
        st.error(f"Error analyzing your music personality: {e}")

# Main App Flow
if is_authenticated():
    try:
        refresh_token()
        sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

        section = st.radio("Choose an Experience:", [
            "Mood-Based Music Discovery", 
            "Your Music Insights", 
            "Your Music Personality"
        ], key="main_radio")

        time_range = st.radio("Select Time Range:", ['This Week', 'This Month', 'This Year'], index=1)
        time_range_map = {'This Week': 'short_term', 'This Month': 'medium_term', 'This Year': 'long_term'}
        spotify_time_range = time_range_map[time_range]

        if section == "Mood-Based Music Discovery":
            mood_based_music_discovery(sp)
        elif section == "Your Music Insights":
            music_insights(sp, spotify_time_range)
        elif section == "Your Music Personality":
            music_personality_analysis(sp)

    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to **Wavvy**")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
