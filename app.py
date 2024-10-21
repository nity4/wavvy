import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time

# Spotify API credentials from Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Define the required scope for Spotify access
scope = "user-library-read user-top-read playlist-read-private user-read-recently-played"

# Initialize Spotify OAuth object
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=scope,
    cache_path=".cache"
)

# Set Streamlit page configuration
st.set_page_config(
    page_title="Wvvy",
    page_icon="〰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
    <style>
    body {
        background: linear-gradient(to right, black, #1DB954) !important;
    }
    .stApp {
        background: linear-gradient(to right, black, #1DB954) !important;
    }
    .header-title {
        font-size: 5em;
        font-weight: bold;
        color: white !important;
        text-align: center;
        padding-top: 50px;
        margin-bottom: 20px;
        letter-spacing: 5px;
    }
    .login-button {
        color: white;
        background-color: #1DB954;
        padding: 15px 30px;
        font-size: 1.5em;
        border-radius: 12px;
        text-align: center;
        display: inline-block;
        font-weight: bold;
        margin-top: 30px;
    }
    .personality-card {
        background-color: #1e1e1e;
        color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .personality-color-box {
        width: 50px;
        height: 50px;
        display: inline-block;
        margin-right: 10px;
        border-radius: 50%;
    }
    .insight-box {
        background-color: #333;
        color: white;
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Wvvy logo and title
st.markdown("<div class='header-title'>〰 Wvvy</div>", unsafe_allow_html=True)

# Function to refresh the token if expired
def refresh_token():
    token_info = st.session_state.get('token_info', None)
    if token_info and sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        st.session_state['token_info'] = token_info

# Function to check if the user is authenticated
def is_authenticated():
    if 'token_info' in st.session_state and st.session_state['token_info']:
        refresh_token()  # Ensure token is refreshed before using it
        return True
    return False

# Authentication flow
def authenticate_user():
    query_params = st.experimental_get_query_params()

    if "code" in query_params:
        code = query_params["code"][0]
        try:
            token_info = sp_oauth.get_cached_token()  # Get the cached token if available
            if not token_info:
                token_info = sp_oauth.get_access_token(code)  # Request a new token using the code
            st.session_state['token_info'] = token_info
            st.experimental_set_query_params()  # Clear query parameters after the code is processed
            st.success("You're authenticated! Click the button below to enter.")
            if st.button("Enter Wvvy"):
                st.experimental_rerun()
        except Exception as e:
            st.error(f"Authentication error: {e}")
    else:
        auth_url = sp_oauth.get_authorize_url()  # Generate authorization URL
        st.markdown(
            f'<a href="{auth_url}" class="login-button">Login with Spotify</a>',
            unsafe_allow_html=True
        )

# Helper Function for Handling Spotify API Rate Limit (429 Error)
def handle_spotify_rate_limit(sp_func, *args, max_retries=10, **kwargs):
    retries = 0
    wait_time = 1
    while retries < max_retries:
        try:
            return sp_func(*args, **kwargs)
        except spotipy.SpotifyException as e:
            if e.http_status == 429:
                retry_after = int(e.headers.get("Retry-After", wait_time)) if e.headers and "Retry-After" in e.headers else wait_time
                st.warning(f"Rate limit reached. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                retries += 1
                wait_time *= 2
            else:
                st.error(f"Error: {e}")
                break
    return None

# Fetch liked songs and audio features
def get_liked_songs(sp):
    results = handle_spotify_rate_limit(sp.current_user_saved_tracks, limit=50)
    if not results:
        return []  # Return empty list if retries exceeded
    liked_songs = []
    for item in results['items']:
        track = item['track']
        audio_features = handle_spotify_rate_limit(sp.audio_features, [track['id']])[0]
        liked_songs.append({
            "name": track['name'],
            "artist": track['artists'][0]['name'],
            "cover": track['album']['images'][0]['url'] if track['album']['images'] else None,
            "energy": audio_features["energy"],
            "valence": audio_features["valence"],
            "tempo": audio_features["tempo"],
            "popularity": track['popularity']
        })
    return liked_songs

# Function to display songs with their cover images
def display_songs(song_list, title):
    st.write(f"### {title}")
    if song_list:
        for song in song_list:
            col1, col2 = st.columns([1, 4])
            with col1:
                if song["cover"]:
                    st.image(song["cover"], width=80)
                else:
                    st.write("No cover")
            with col2:
                st.write(f"**{song['name']}** by {song['artist']}")
    else:
        st.write("No songs found.")

# Fetch top items for insights
def get_top_items(sp, item_type='tracks', time_range='short_term', limit=10):
    if item_type == 'tracks':
        results = handle_spotify_rate_limit(sp.current_user_top_tracks, time_range=time_range, limit=limit)
    elif item_type == 'artists':
        results = handle_spotify_rate_limit(sp.current_user_top_artists, time_range=time_range, limit=limit)
    items = []
    for item in results['items']:
        if item_type == 'tracks':
            items.append({
                'name': item['name'],
                'artist': item['artists'][0]['name'],
                'popularity': item.get('popularity', 0),
                'cover': item['album']['images'][0]['url'] if item['album']['images'] else None,
                'tempo': item.get('tempo', 120)
            })
        elif item_type == 'artists':
            items.append({
                'name': item['name'],
                'genres': item.get('genres', ['Unknown Genre']),
                'cover': item['images'][0]['url'] if item['images'] else None
            })
    return items

# Display top songs and artists insights
def display_top_insights(sp, time_range='short_term'):
    top_tracks = get_top_items(sp, item_type='tracks', time_range=time_range)
    top_artists = get_top_items(sp, item_type='artists', time_range=time_range)
    
    st.write(f"### Top Insights for {time_range.replace('_', ' ').title()}")

    # Display top songs with cover images
    if top_tracks:
        st.write("### Top Songs")
        for track in top_tracks:
            col1, col2 = st.columns([1, 4])
            with col1:
                st.image(track['cover'], width=80)
            with col2:
                st.write(f"**{track['name']}** by {track['artist']}")
    
    # Display top artists with their cover images
    if top_artists:
        st.write("### Top Artists")
        for artist in top_artists:
            col1, col2 = st.columns([1, 4])
            with col1:
                st.image(artist['cover'], width=80)
            with col2:
                st.write(f"**{artist['name']}** - {', '.join(artist['genres'])}")

    # Display top genres
    st.write("### Top Genres")
    genres = [artist['genres'][0] for artist in top_artists if artist['genres']]
    unique_genres = set(genres)
    genre_list = ', '.join(unique_genres)
    st.markdown(f"<div class='insight-box'><strong>Genres Explored:</strong> {genre_list}</div>", unsafe_allow_html=True)

    # Fascinating insights based on the user's top songs
    if top_tracks:
        avg_popularity = round(sum(track['popularity'] for track in top_tracks) / len(top_tracks), 1) if top_tracks else 0
        avg_energy = round(sum(track.get('energy', 0.5) for track in top_tracks) / len(top_tracks), 2)
        avg_tempo = round(sum(track.get('tempo', 120) for track in top_tracks) / len(top_tracks), 1)
        hidden_gems = [track for track in top_tracks if track['popularity'] < 50]

        # Display insights in well-formatted boxes
        st.write("### Fascinating Insights")
        st.markdown(f"<div class='insight-box'><strong>Average Popularity of Top Songs:</strong> {avg_popularity}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='insight-box'><strong>Average Energy of Top Songs:</strong> {avg_energy}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='insight-box'><strong>Average Tempo of Top Songs:</strong> {avg_tempo} BPM</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='insight-box'><strong>Hidden Gems (Less Popular Tracks):</strong> {len(hidden_gems)} discovered</div>", unsafe_allow_html=True)

# Function to analyze listening behavior
def analyze_listening_behavior(sp):
    top_artists = get_top_items(sp, item_type='artists', time_range='long_term', limit=50)
    total_artists = len(top_artists)
    
    # Estimate total songs based on top artist data
    top_tracks = get_top_items(sp, item_type='tracks', time_range='long_term', limit=50)
    total_songs = len(top_tracks)

    avg_songs_per_artist = total_songs / total_artists if total_artists else 0

    if avg_songs_per_artist > 30:
        return "Deep Diver", "blue", "You're all about depth—diving deep into a few artists and their entire discographies."
    elif total_artists > 40:
        return "Explorer", "green", "You're a breadth explorer, constantly seeking new artists and sounds."
    else:
        return "Balanced Listener", "yellow", "You strike the perfect balance between exploring new music and sticking to your favorites."

# Fetch recent listening data and calculate behavioral insights
def fetch_recently_played(sp):
    results = handle_spotify_rate_limit(sp.current_user_recently_played, limit=50)
    if not results:
        return 0, 0
    total_songs = len(results['items'])
    total_minutes = sum([item['track']['duration_ms'] for item in results['items']]) / (1000 * 60)  # Convert ms to minutes
    return total_songs, total_minutes

# Display music personality profile
def display_music_personality(sp):
    # Analyze listening behavior and determine personality type
    personality, color, description = analyze_listening_behavior(sp)
    
    # Fetch recent listening data
    total_songs_this_week, total_minutes_this_week = fetch_recently_played(sp)
    
    st.write(f"### Your Music Personality Profile")
    st.markdown(f"""
    <div class="personality-card">
        <h2>Personality Summary</h2>
        <p><strong>Personality Name</strong>: {personality}</p>
        <div class="personality-color-box" style="background-color: {color}; display: inline-block;"></div>
        <strong>Personality Color</strong>: {color.capitalize()}</p>
        <p>{description}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="personality-card">
        <h2>Weekly Listening Stats</h2>
        <p><strong>Total Tracks This Week:</strong> {total_songs_this_week}</p>
        <p><strong>Total Minutes Listened This Week:</strong> {total_minutes_this_week} minutes</p>
    </div>
    """, unsafe_allow_html=True)

# Main app logic
if is_authenticated():
    sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

    # Tabs for different features
    tab1, tab2, tab3 = st.tabs([
        "Liked Songs & New Discoveries", 
        "Top Songs, Artists & Genres", 
        "Your Music Personality"
    ])

    with tab1:
        option = st.radio("Choose Option:", ["Liked Songs", "Discover New Songs"])
        mood = st.selectbox("Choose your mood:", ["Happy", "Calm", "Energetic", "Sad"])
        intensity = st.slider("Choose intensity:", 1, 5, 3)

        if option == "Liked Songs":
            liked_songs = get_liked_songs(sp)
            if liked_songs:
                filtered_liked_songs = [song for song in liked_songs if song['energy'] > 0.5]  # example filter
                display_songs(filtered_liked_songs, "Your Liked Songs")
            else:
                st.warning("No liked songs available.")
        else:
            st.warning("Discover New Songs feature not implemented.")

    with tab2:
        time_filter = st.selectbox("Select Time Period:", ["This Week", "This Month", "This Year"])
        time_mapping = {'This Week': 'short_term', 'This Month': 'medium_term', 'This Year': 'long_term'}
        display_top_insights(sp, time_range=time_mapping[time_filter])

    with tab3:
        display_music_personality(sp)
    
else:
    st.write("Welcome to Wvvy")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
