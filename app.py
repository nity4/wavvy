import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import pandas as pd
import time
import matplotlib.pyplot as plt

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

# Custom CSS for styling: white text and smaller music icon
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
    .song-cover, .artist-cover, .genre-icon {
        margin-right: 10px;
    }
    .stMarkdown, .stMarkdown p, .stMarkdown h3, .stSelectbox label, .stSlider label {
        color: white !important;
    }
    img.genre-icon {
        width: 30px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Wvvy logo and title
st.markdown("<div class='header-title'>〰 Wvvy</div>", unsafe_allow_html=True)

# Authentication Functions
def is_authenticated():
    return 'token_info' in st.session_state and st.session_state['token_info'] is not None

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
            "tempo": audio_features["tempo"]
        })
    random.shuffle(liked_songs)
    return liked_songs

# Discover new songs based on user’s top tracks, artists, and genres
def get_new_discoveries(sp):
    top_tracks = handle_spotify_rate_limit(sp.current_user_top_tracks, time_range="medium_term", limit=5)
    top_artists = handle_spotify_rate_limit(sp.current_user_top_artists, time_range="medium_term", limit=5)
    
    if not top_tracks or not top_artists:
        return []

    seed_tracks = [track['id'] for track in top_tracks['items'][:3]]
    seed_genres = [artist['genres'][0] for artist in top_artists['items'] if artist['genres']][:2]
    
    recommendations = handle_spotify_rate_limit(sp.recommendations, seed_tracks=seed_tracks, seed_genres=seed_genres, limit=50)
    
    if not recommendations:
        return []
    
    new_songs = []
    for track in recommendations['tracks']:
        audio_features = handle_spotify_rate_limit(sp.audio_features, [track['id']])[0]
        new_songs.append({
            "name": track['name'],
            "artist": track['artists'][0]['name'],
            "cover": track['album']['images'][0]['url'] if track['album']['images'] else None,
            "energy": audio_features["energy"],
            "valence": audio_features["valence"],
            "tempo": audio_features["tempo"]
        })
    random.shuffle(new_songs)
    return new_songs

# Filter songs based on mood and intensity
def filter_songs(songs, mood, intensity):
    mood_ranges = {
        "Happy": {"valence": (0.6, 1), "tempo": (100, 200)},
        "Calm": {"valence": (0.3, 0.5), "tempo": (40, 100)},
        "Energetic": {"valence": (0.5, 1), "tempo": (120, 200)},
        "Sad": {"valence": (0, 0.3), "tempo": (40, 80)}
    }
    mood_filter = mood_ranges[mood]
    filtered_songs = [
        song for song in songs
        if mood_filter["valence"][0] <= song["valence"] <= mood_filter["valence"][1]
        and mood_filter["tempo"][0] <= song["tempo"] <= mood_filter["tempo"][1]
        and song['energy'] >= (intensity / 5)
    ]
    return filtered_songs

# Display liked and new songs
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
                'cover': item['album']['images'][0]['url'] if item['album']['images'] else None
            })
        elif item_type == 'artists':
            items.append({
                'name': item['name'],
                'genres': item.get('genres', ['Unknown Genre']),
                'cover': item['images'][0]['url'] if item['images'] else None
            })
    return items

# Display top songs, artists, and genres with insights
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
    # Convert genres to a list (instead of a set)
    genres = [artist['genres'][0] for artist in top_artists if artist['genres']]
    unique_genres = set(genres)
    for genre in unique_genres:
        st.write(f"**{genre}**")

    # Personalized Insights at the End
    st.write("### Fascinating Insights about Your Music:")
    # Count the most listened genre by using list and count
    most_listened_genre = max(genres, key=genres.count)
    st.write(f"**You listen to {most_listened_genre} the most!** This shows you really enjoy a specific kind of vibe.")
    st.write("**Your top artist** is deeply connected to your mood — seems like you listen to them no matter how you're feeling!")
    
# Analyze listening depth vs. breadth
def analyze_depth_vs_breadth(sp):
    top_artists = get_top_items(sp, item_type='artists', time_range='long_term', limit=50)
    
    total_artists = len(top_artists)
    total_songs = sum([random.randint(50, 200) for _ in range(total_artists)])  # Simulated data
    avg_songs_per_artist = total_songs / total_artists
    
    st.write(f"### Depth vs Breadth in Your Listening")
    st.write(f"Total Unique Artists: {total_artists}")
    st.write(f"Average Songs Per Artist: {avg_songs_per_artist:.2f}")

    # Visualization: Weekly listening graph (screen time style)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    song_count = [random.randint(20, 60) for _ in range(7)]
    
    # Matplotlib visualization for appealing chart
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(days, song_count, color='lightblue')
    ax.set_title('Songs Listened per Day (This Week)')
    ax.set_ylabel('Number of Songs')
    ax.set_xlabel('Day of the Week')
    st.pyplot(fig)
    
    # Total number of songs and minutes
    total_minutes = total_songs * 3  # Assuming average song length is 3 minutes
    st.write(f"**Total Songs This Week:** {total_songs}")
    st.write(f"**Total Minutes This Week:** {total_minutes} minutes")

# Fun personality feature based on listening habits
def assign_music_personality(avg_songs_per_artist, total_artists):
    if avg_songs_per_artist > 30:
        return "Deep Diver", "blue", "You explore artists deeply, diving into their discography."
    elif total_artists > 40:
        return "Explorer", "green", "You love discovering new artists and exploring a wide range of music."
    else:
        return "Balanced Listener", "yellow", "You strike a balance between exploring new music and diving deep into favorite artists."

def display_music_personality(sp):
    top_artists = get_top_items(sp, item_type='artists', time_range='long_term', limit=50)
    
    total_artists = len(top_artists)
    total_songs = sum([random.randint(50, 200) for _ in range(total_artists)])
    avg_songs_per_artist = total_songs / total_artists
    
    personality, color, description = assign_music_personality(avg_songs_per_artist, total_artists)
    st.write(f"### Your Music Personality: **{personality}**")
    st.write(f"**Personality Color:** {color}")
    st.write(description)
    st.write("Your music habits are unique and interesting. Keep enjoying the tunes!")

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
                filtered_liked_songs = filter_songs(liked_songs, mood, intensity)
                display_songs(filtered_liked_songs, "Your Liked Songs")
            else:
                st.warning("No liked songs available.")
        else:
            new_songs = get_new_discoveries(sp)
            if new_songs:
                filtered_new_songs = filter_songs(new_songs, mood, intensity)
                display_songs(filtered_new_songs, "New Song Discoveries")
            else:
                st.warning("No new discoveries available.")

    with tab2:
        time_filter = st.selectbox("Select Time Period:", ["This Week", "This Month", "This Year"])
        time_mapping = {'This Week': 'short_term', 'This Month': 'medium_term', 'This Year': 'long_term'}
        display_top_insights(sp, time_range=time_mapping[time_filter])

    with tab3:
        analyze_depth_vs_breadth(sp)
        display_music_personality(sp)
    
else:
    st.write("Welcome to Wvvy")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
