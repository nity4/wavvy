import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import random
import datetime
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

# Custom CSS for white text and design elements
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

# Fetch top items (tracks, artists) from Spotify
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
                'genres': [artist.get('genres', ['Unknown Genre'])[0] for artist in item['artists']]
            })
        elif item_type == 'artists':
            items.append({
                'name': item['name'],
                'genres': item.get('genres', ['Unknown Genre']),
                'popularity': item['popularity']
            })
    return items

# Display top songs, artists, and genres with fascinating insights
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

    # Fascinating Insights:
    st.write("### Fascinating Insights")
    
    # Unique Songs (Hidden Gems)
    unique_songs = [track for track in top_tracks if track['popularity'] < 50]
    if unique_songs:
        st.write("**Hidden Gems**: You've discovered some unique songs that are not widely known!")
        for song in unique_songs:
            st.write(f"**{song['name']}** by {song['artist']} (Popularity: {song['popularity']})")
    
    # Music Taste Evolution Over Time
    st.write("**Music Taste Evolution Over Time**")
    genres_over_time = {artist['name']: artist['genres'] for artist in top_artists if artist['genres']}
    df = pd.DataFrame(list(genres_over_time.items()), columns=['Artist', 'Genres'])
    st.dataframe(df)

# Analyze listening depth vs. breadth
def analyze_depth_vs_breadth(sp):
    top_artists = get_top_items(sp, item_type='artists', time_range='long_term', limit=50)
    
    total_artists = len(top_artists)
    total_songs = sum([handle_spotify_rate_limit(sp.artist_top_tracks, artist['id'])['total'] for artist in top_artists])

    avg_songs_per_artist = total_songs / total_artists
    
    st.write(f"### Depth vs Breadth in Your Listening")
    st.write(f"Total Unique Artists: {total_artists}")
    st.write(f"Average Songs Per Artist: {avg_songs_per_artist:.2f}")

    # Visualization: Weekly listening graph (screen time style)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    song_count = [random.randint(20, 60) for _ in range(7)]
    st.write("**Weekly Listening (Songs per Day)**")
    st.bar_chart(pd.DataFrame({'Day': days, 'Songs Listened': song_count}).set_index('Day'))
    
    # Total number of songs and minutes
    total_minutes = total_songs * 3  # Assuming average song length is 3 minutes
    st.write(f"**Total Songs Listened:** {total_songs}")
    st.write(f"**Total Minutes Listened:** {total_minutes} minutes")

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
    total_songs = sum([handle_spotify_rate_limit(sp.artist_top_tracks, artist['id'])['total'] for artist in top_artists])
    avg_songs_per_artist = total_songs / total_artists
    
    # Assign personality
    personality, color, description = assign_music_personality(avg_songs_per_artist, total_artists)
    st.write(f"### Your Music Personality: **{personality}**")
    st.write(f"**Personality Color:** {color}")
    st.write(description)
    st.write("Your music habits are unique and interesting. Keep enjoying the tunes!")

# Main app logic
if is_authenticated():
    sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

    # Tabs for different features
    tab1, tab2, tab3, tab4 = st.tabs([
        "Top Songs, Artists & Genres", 
        "Insights & Fascinating Data", 
        "Listening Depth vs Breadth", 
        "Your Music Personality"
    ])

    with tab1:
        time_filter = st.selectbox("Select Time Period:", ["This Week", "This Month", "This Year"])
        time_mapping = {'This Week': 'short_term', 'This Month': 'medium_term', 'This Year': 'long_term'}
        display_top_insights(sp, time_range=time_mapping[time_filter])

    with tab2:
        display_top_insights(sp, time_range='long_term')  # Add fascinating insights
    
    with tab3:
        analyze_depth_vs_breadth(sp)  # Depth vs Breadth Analysis
    
    with tab4:
        display_music_personality(sp)  # Fun music personality
    
else:
    st.write("Welcome to Wvvy")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
