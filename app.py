import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import time

# Spotify API credentials from Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Define the required scope for Spotify access
scope = "user-library-read user-top-read playlist-read-private"

# Set cache path
cache_path = ".cache"

# Function to clear cache
def clear_cache():
    """Clears the OAuth cache to prevent reusing old tokens or authorization codes."""
    if os.path.exists(cache_path):
        os.remove(cache_path)

# Initialize Spotify OAuth object
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=scope,
    cache_path=cache_path
)

# Set Streamlit page configuration
st.set_page_config(
    page_title="Wvvy",
    page_icon="〰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to refresh the token if expired
def refresh_token():
    """Refreshes the token if it has expired."""
    token_info = st.session_state.get('token_info', None)
    if token_info and sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        st.session_state['token_info'] = token_info

# Function to check if the user is authenticated
def is_authenticated():
    """Checks if the user is authenticated and has a valid token."""
    if 'token_info' in st.session_state and st.session_state['token_info']:
        refresh_token()  # Ensure the token is refreshed before using it
        return True
    return False

# Authentication flow
def authenticate_user():
    """Handles Spotify OAuth authentication flow."""
    query_params = st.experimental_get_query_params()  # Use query parameters to get the 'code'

    if "code" in query_params:
        code = query_params["code"][0]
        try:
            # Clear cache before attempting to use the code
            clear_cache()

            # Immediately exchange the authorization code for an access token
            token_info = sp_oauth.get_access_token(code)
            st.session_state['token_info'] = token_info

            # Clear query parameters and rerun the app
            st.experimental_set_query_params()  # Clear query parameters
            st.success("You're authenticated! Click the button below to enter.")
            if st.button("Enter Wvvy"):
                st.experimental_rerun()  # Rerun after successful authentication
        except Exception as e:
            st.error(f"Authentication error: {e}")
    else:
        auth_url = sp_oauth.get_authorize_url()
        st.markdown(
            f'<a href="{auth_url}" class="login-button">Login with Spotify</a>',
            unsafe_allow_html=True
        )

# Helper function to handle Spotify API Rate Limit (HTTP 429 Error)
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
    """Fetches liked songs and their audio features."""
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
    random.shuffle(liked_songs)
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

# Display top insights (Top Songs, Artists, Genres, Insights)
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
    for genre in unique_genres:
        st.write(f"**{genre}**")

    # Insights based on user data only
    st.write("### Fascinating Insights about Your Music:")
    insights = []

    # Top Tracks Popularity
    avg_popularity = round(sum(track['popularity'] for track in top_tracks) / len(top_tracks), 1) if top_tracks else 0
    insights.append(f"Your top tracks have an average popularity of <strong>{avg_popularity}</strong>. You're balancing popular hits and deep cuts.")
    
    # Top Track Energy Levels
    avg_energy = round(sum(track.get('energy', 0.5) for track in top_tracks) / len(top_tracks), 2)
    insights.append(f"The energy levels of your top tracks are at <strong>{avg_energy}</strong>. You love a good balance of upbeat and mellow songs.")
    
    # Unique Genres
    genre_count = len(unique_genres)
    insights.append(f"You explored <strong>{genre_count}</strong> different genres this period. You're musically diverse!")

    # Tempo analysis
    avg_tempo = sum(track.get('tempo', 120) for track in top_tracks) / len(top_tracks) if top_tracks else 120
    insights.append(f"Your favorite songs have an average tempo of <strong>{round(avg_tempo)} BPM</strong>. You're all about that perfect rhythm.")

    # Hidden Gems based on popularity (insight)
    hidden_gems = [track for track in top_tracks if track['popularity'] < 50]  # Example threshold for hidden gems
    hidden_gems_count = len(hidden_gems)
    insights.append(f"You've found <strong>{hidden_gems_count} hidden gems</strong> this time. Keep discovering underrated tracks!")

    # Display insights in a flip-card style
    def display_flip_insights(insights):
        for i in range(0, len(insights), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(insights):
                    with cols[j]:
                        st.markdown(f"""
                        <div class="flip-card">
                            <div class="flip-card-inner">
                                <div class="flip-card-front">
                                    🔥 Hot Insight
                                </div>
                                <div class="flip-card-back">
                                    {insights[i + j]}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

    display_flip_insights(insights)

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

else:
    st.write("Welcome to Wvvy")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
