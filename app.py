import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import time

# Spotify API credentials from Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Define the required scope for Spotify access
scope = "user-library-read user-top-read playlist-read-private"

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

# Custom CSS for app styling
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
    .stMarkdown p, .stMarkdown h3 {
        color: white !important;
    }
    .stSelectbox label, .stSlider label {
        color: white !important;
    }
    .stSelectbox .css-1wa3eu0-placeholder, .stSelectbox .css-2b097c-container {
        color: white !important;
    }
    .stSlider .css-164nlkn .css-qrbaxs {
        color: white !important;
    }
    .stTabs [role="tab"] {
        color: white !important;
    }
    .stTabs [role="tabpanel"] {
        background-color: rgba(0, 0, 0, 0.5) !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# Wvvy logo and title
st.markdown("<div class='header-title'>〰 Wvvy</div>", unsafe_allow_html=True)

# Authentication Functions
def is_authenticated():
    return 'token_info' in st.session_state and st.session_state['token_info'] is not None

def refresh_token():
    if 'token_info' in st.session_state and sp_oauth.is_token_expired(st.session_state['token_info']):
        token_info = sp_oauth.refresh_access_token(st.session_state['token_info']['refresh_token'])
        st.session_state['token_info'] = token_info

def authenticate_user():
    query_params = st.experimental_get_query_params()
    
    if "code" in query_params:
        code = query_params["code"][0]
        try:
            token_info = sp_oauth.get_cached_token()
            if not token_info:
                token_info = sp_oauth.get_access_token(code)
            st.session_state['token_info'] = token_info
            st.experimental_set_query_params()  # Clear query parameters
            st.success("You're authenticated! Click the button below to enter.")
            if st.button("Enter Wvvy"):
                st.experimental_rerun()
        except Exception as e:
            st.error(f"Authentication error: {e}")
    else:
        auth_url = sp_oauth.get_authorize_url()
        st.markdown(
            f'<a href="{auth_url}" class="login-button">Login with Spotify</a>',
            unsafe_allow_html=True
        )

# Helper Function for Handling Spotify API Rate Limit (429 Error)
def handle_spotify_rate_limit(sp_func, *args, max_retries=10, **kwargs):
    retries = 0
    wait_time = 1
    suppressed_warning = False
    while retries < max_retries:
        try:
            return sp_func(*args, **kwargs)
        except spotipy.SpotifyException as e:
            if e.http_status == 429:
                retry_after = int(e.headers.get("Retry-After", wait_time)) if e.headers and "Retry-After" in e.headers else wait_time
                if not suppressed_warning:
                    st.warning(f"Rate limit reached. Retrying after {retry_after} seconds...")
                    suppressed_warning = True
                time.sleep(retry_after)
                retries += 1
                wait_time *= 2
            else:
                st.error(f"Error: {e}")
                break
    return None

# Fetch audio features for a batch of tracks (with 429 handling)
def fetch_audio_features(sp, track_ids):
    audio_features = []
    batch_size = 50  # Fetch in batches of 50 to avoid rate limits
    for i in range(0, len(track_ids), batch_size):
        batch_ids = track_ids[i:i + batch_size]
        features = handle_spotify_rate_limit(sp.audio_features, batch_ids)
        if features:
            audio_features.extend(features)
    return audio_features

# Example function to get liked songs and audio features (with 429 error handling)
def get_liked_songs(sp):
    results = handle_spotify_rate_limit(sp.current_user_saved_tracks, limit=50)
    if not results:
        return []  # Return empty list if retries exceeded
    liked_songs = []
    for item in results['items']:
        track = item['track']
        track_id = track['id']
        audio_features = fetch_audio_features(sp, [track_id])[0]
        liked_songs.append({
            "name": track['name'],
            "artist": track['artists'][0]['name'],
            "cover": track['album']['images'][0]['url'] if track['album']['images'] else None,
            "energy": audio_features["energy"],
            "valence": audio_features["valence"],
            "tempo": audio_features["tempo"]
        })
    return liked_songs

# Enhanced mood classification based on valence and tempo
def filter_songs(songs, mood, intensity):
    mood_ranges = {
        "Happy": {"valence": (0.6, 1), "tempo": (100, 200)},
        "Calm": {"valence": (0.3, 0.5), "tempo": (40, 100)},
        "Energetic": {"valence": (0.5, 1), "tempo": (120, 200)},
        "Sad": {"valence": (0, 0.3), "tempo": (40, 80)}
    }
    
    mood_filter = mood_ranges[mood]
    
    # Apply mood and intensity filtering
    filtered_songs = [
        song for song in songs
        if mood_filter["valence"][0] <= song["valence"] <= mood_filter["valence"][1]
        and mood_filter["tempo"][0] <= song["tempo"] <= mood_filter["tempo"][1]
        and song['energy'] >= (intensity / 5)
    ]
    
    return filtered_songs

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

# Fetch top songs, artists, and genres over time
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
                'popularity': item['popularity'],
                'genres': [artist.get('genres', ['Unknown Genre'])[0] for artist in item['artists']]  # Check for 'genres'
            })
        elif item_type == 'artists':
            items.append({
                'name': item['name'],
                'genres': item.get('genres', ['Unknown Genre']),  # Safely access 'genres' with fallback
                'popularity': item['popularity']
            })
    
    return items

# Display insights based on top songs, artists, and genres
def display_top_insights(sp, time_range='short_term'):
    top_tracks = get_top_items(sp, item_type='tracks', time_range=time_range)
    top_artists = get_top_items(sp, item_type='artists', time_range=time_range)
    
    st.write(f"### Top Insights for {time_range.replace('_', ' ').title()}")

    if top_tracks:
        st.write(f"**Most Listened Song:** {top_tracks[0]['name']} by {top_tracks[0]['artist']}")
        st.write(f"**Top Artist:** {top_artists[0]['name']}")
        st.write(f"**Top Genres:** {', '.join(genre for artist in top_artists for genre in artist['genres'])}")
    else:
        st.write("No top tracks found for this period.")

# Unique Songs Insights: Display unique songs based on popularity
def find_unique_songs(sp):
    top_tracks = get_top_items(sp, item_type='tracks', time_range='medium_term')
    unique_songs = [track for track in top_tracks if track['popularity'] < 50]  # Songs with low popularity

    st.write("### Hidden Gems or Unique Finds")
    if unique_songs:
        for song in unique_songs:
            st.write(f"**{song['name']}** by {song['artist']} (Popularity: {song['popularity']})")
    else:
        st.write("No hidden gems found among your top tracks.")

# Analyze listening depth vs breadth
def analyze_depth_vs_breadth(sp):
    top_artists = get_top_items(sp, item_type='artists', time_range='long_term', limit=50)
    artist_song_count = {artist['name']: handle_spotify_rate_limit(sp.artist_top_tracks, artist['id']) for artist in top_artists}

    total_artists = len(artist_song_count)
    total_songs = sum(len(tracks['tracks']) for tracks in artist_song_count.values())
    avg_songs_per_artist = total_songs / total_artists
    
    st.write(f"### Depth vs Breadth in Your Listening")
    st.write(f"Total Unique Artists: {total_artists}")
    st.write(f"Average Songs Per Artist: {avg_songs_per_artist:.2f}")

    # Visualization: Bar chart showing the number of songs per artist
    artist_names = list(artist_song_count.keys())
    song_counts = [len(tracks['tracks']) for tracks in artist_song_count.values()]
    
    df = pd.DataFrame({'Artist': artist_names, 'Song Count': song_counts})
    st.bar_chart(df.set_index('Artist'))

# Main app logic
if is_authenticated():
    sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

    # Tabs for different features
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Liked Songs", 
        "Top Songs, Artists & Genres", 
        "Unique Songs", 
        "Listening Depth vs Breadth", 
        "Your Music Insights"
    ])

    with tab1:
        mood = st.selectbox("Choose your mood:", ["Happy", "Calm", "Energetic", "Sad"])
        intensity = st.slider("Choose intensity:", 1, 5, 3)
        liked_songs = get_liked_songs(sp)
        if liked_songs:
            filtered_liked_songs = filter_songs(liked_songs, mood, intensity)
            display_songs(filtered_liked_songs, "Your Liked Songs")
        else:
            st.warning("No liked songs available.")

    with tab2:
        time_filter = st.selectbox("Select Time Period:", ["This Week", "This Month", "This Year"])
        time_mapping = {'This Week': 'short_term', 'This Month': 'medium_term', 'This Year': 'long_term'}
        display_top_insights(sp, time_range=time_mapping[time_filter])

    with tab3:
        find_unique_songs(sp)  # Display most unique songs

    with tab4:
        analyze_depth_vs_breadth(sp)  # Analyze depth vs breadth in their listening

    with tab5:
        plot_music_taste_evolution(sp)  # Display music taste evolution over time

else:
    st.write("Please log in to Spotify to view your personalized music insights.")
    authenticate_user()
