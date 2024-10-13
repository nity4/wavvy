import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time

# Spotify API credentials stored in Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Scope to access user's liked songs and recently played tracks
SCOPE = 'user-library-read user-top-read user-read-recently-played'

# Initialize Spotify OAuth
sp_oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE)

# Streamlit App Layout - Dark Theme with a Modern, Gen Z vibe
st.set_page_config(page_title="Wavvy 〰", page_icon="〰", layout="centered", initial_sidebar_state="collapsed")

# Apply Modern, Sleek CSS for a more engaging visual experience
st.markdown(
    """
    <style>
    body {
        background-color: #1f1f1f;
        color: #ffffff;
        font-family: 'Roboto', sans-serif;
    }
    .stButton>button {
        background-color: #3f51b5;
        color: #ffffff;
        border-radius: 8px;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #ff4081;
    }
    .stImage {
        border-radius: 12px;
        margin-bottom: 10px;
    }
    h1, h2, h3 {
        font-weight: 300;
        color: #ffffff;
    }
    h1 {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    h2 {
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    h3 {
        font-size: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .progress-bar {
        background-color: #3f51b5;
        height: 8px;
        border-radius: 4px;
    }
    </style>
    """, unsafe_allow_html=True
)

# Initialize session state for token persistence
if 'token_info' not in st.session_state:
    st.session_state['token_info'] = None

# Helper function to check if the user is authenticated
def is_authenticated():
    return st.session_state['token_info'] is not None

# Helper function to check if the token is expired and refresh if needed
def refresh_token():
    if st.session_state['token_info']:
        if sp_oauth.is_token_expired(st.session_state['token_info']):
            token_info = sp_oauth.refresh_access_token(st.session_state['token_info']['refresh_token'])
            st.session_state['token_info'] = token_info

# Function to authenticate user with Spotify
def authenticate_user():
    try:
        if "code" in st.experimental_get_query_params():
            code = st.experimental_get_query_params()["code"][0]
            token_info = sp_oauth.get_access_token(code)
            st.session_state['token_info'] = token_info

            # Clear the code parameter from the URL after successful authentication
            st.experimental_set_query_params(code=None)
            
            st.success("You're all set! Refresh to see your insights.")
            if st.button("Refresh Now"):
                st.experimental_set_query_params()
        else:
            auth_url = sp_oauth.get_authorize_url()
            st.markdown(f'<a href="{auth_url}" target="_self" style="color: #ff4081; text-decoration: none;">Authorize with Spotify</a>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error during authentication: {e}")

# Improved Song Mood Filtering with Better Audio Features and Transitions
def discover_music_by_feelings(sp):
    st.header("Mood-Based Music Discovery 🎧")
    st.write("Let's vibe out to music that matches how you're feeling. Just set the mood, and we'll take care of the playlist.")

    # Mood and intensity input
    feeling = st.selectbox("What's your mood today?", ["Happy", "Sad", "Chill", "Hype"])
    intensity = st.slider(f"How {feeling} are you feeling?", 1, 10, help="Adjust the intensity slider to match your current vibe.")
    
    song_type = st.radio("What kind of tracks are you looking for?", ["My Liked Songs", "Discover New Music"])
    
    # Spotify Data Fetching and Audio Feature Analysis
    try:
        st.write("Fetching songs that match your vibe...")

        if song_type == "My Liked Songs":
            results = sp.current_user_saved_tracks(limit=50)
            liked_songs = results['items']
        else:
            results = sp.recommendations(seed_genres=['pop', 'rock', 'hip-hop', 'indie'], limit=50)
            liked_songs = results['tracks']

        # Fetch audio features
        song_ids = [track['track']['id'] for track in liked_songs] if song_type == "My Liked Songs" else [track['id'] for track in liked_songs]
        features = sp.audio_features(tracks=song_ids)

        filtered_songs = []
        for i, song in enumerate(liked_songs):
            feature = features[i]
            if feature:
                valence, energy, danceability, tempo = feature['valence'], feature['energy'], feature['danceability'], feature['tempo']

                if feeling == "Happy" and valence > 0.7 and energy >= intensity / 10:
                    filtered_songs.append(song)
                elif feeling == "Sad" and valence < 0.4 and energy <= intensity / 10:
                    filtered_songs.append(song)
                elif feeling == "Chill" and energy < 0.5 and tempo < 100:
                    filtered_songs.append(song)
                elif feeling == "Hype" and energy > 0.7 and tempo > 120:
                    filtered_songs.append(song)

        if filtered_songs:
            st.subheader(f"Here's a {feeling} playlist for you:")
            for track in filtered_songs:
                song_name = track['track']['name'] if song_type == "My Liked Songs" else track['name']
                artist_name = track['track']['artists'][0]['name'] if song_type == "My Liked Songs" else track['artists'][0]['name']
                album_cover = track['track']['album']['images'][0]['url'] if song_type == "My Liked Songs" else track['album']['images'][0]['url']
                st.image(album_cover, width=150)
                st.write(f"**{song_name}** by *{artist_name}*")
        else:
            st.write(f"Couldn't find anything that fits your vibe right now.")

    except Exception as e:
        st.error(f"Something went wrong while fetching songs: {e}")

# Enhanced Comprehensive Insights with Real-Time Visualizations and Fun Facts
def comprehensive_insights(sp):
    st.header("Your Music Insights Dashboard 🔥")
    st.write("Here's a deeper look into your recent listening habits, your go-to artists, and some fun facts along the way.")

    try:
        # Fetch top artists and genres
        top_artists = sp.current_user_top_artists(limit=5)
        artist_names = [artist['name'] for artist in top_artists['items']]
        top_genres = [artist['genres'] for artist in top_artists['items']]

        # Display top artists
        st.subheader("Your Top Artists:")
        for artist in top_artists['items']:
            st.image(artist['images'][0]['url'], width=150)
            st.write(f"**{artist['name']}**")

        # Display a fun fact about the user's listening behavior
        st.subheader("Did you know?")
        if "pop" in ', '.join([genre for sublist in top_genres for genre in sublist]):
            st.write("You're a certified pop enthusiast! You’ve been vibing with some of the happiest, most energetic tracks in your library.")
        else:
            st.write("You've got eclectic taste! You’re always discovering new sounds and genres.")

        # Recent listening history with total listening time
        st.subheader("Recent Listening History:")
        results = sp.current_user_recently_played(limit=10)
        recent_tracks = results['items']
        total_tracks = len(recent_tracks)
        listening_time = total_tracks * 3

        st.write(f"You've played **{total_tracks} tracks** recently, for about **{listening_time} minutes**.")
        for track in recent_tracks[:5]:
            song_name = track['track']['name']
            artist_name = track['track']['artists'][0]['name']
            album_cover = track['track']['album']['images'][0]['url']
            st.image(album_cover, width=100)
            st.write(f"**{song_name}** by *{artist_name}*")

        # Fun fact about new artists
        new_artists_count = len(set(track['track']['artists'][0]['name'] for track in recent_tracks))
        st.subheader("Expand Your Horizons:")
        st.write(f"You’ve discovered **{new_artists_count} new artists** recently. Keep exploring those fresh sounds!")

    except Exception as e:
        st.error(f"Error while fetching insights: {e}")

# Expanded Music Personality and Color Visualization with New Colors and Effects
def music_personality_analysis(sp):
    st.header("Discover Your Music Personality")
    st.write("Based on your top genres and tracks, we've mapped out a personality that matches your unique taste in music.")

    try:
        results = sp.current_user_top_tracks(limit=50)
        top_genres = [track['album']['genres'] for track in results['items'] if 'genres' in track['album']]

        if top_genres:
            st.write("Analyzing your taste...")
            progress_bar = st.progress(0)
            for percent in range(100):
                time.sleep(0.01)
                progress_bar.progress(percent + 1)

            personality_type, color = assign_personality_and_color(top_genres)
            st.write(f"You're a **{personality_type}**, and your music color is **{color}**!")

            # Display visual cue for music color
            st.markdown(f"<div style='width:100%; height:120px; background-color:{color}; border-radius:10px;'></div>", unsafe_allow_html=True)
        else:
            st.write("You're a mystery! We couldn't get enough data, so we'll call you an Explorer with a *Gray* personality.")

    except Exception as e:
        st.error(f"Error analyzing your music personality: {e}")

# Updated Color Palette for Personalities
def assign_personality_and_color(genres):
    genre_string = ', '.join([g for sublist in genres for g in sublist])
    personality_map = {
        "rock": ("Adventurer", "#ff3b30"),
        "pop": ("Trendsetter", "#ffd700"),
        "jazz": ("Calm Soul", "#1e90ff"),
        "electronic": ("Innovator", "#8a2be2"),
        "hip hop": ("Rebel", "#000000"),
        "classical": ("Old Soul", "#ffa500"),
        "blues": ("Sentimental", "#008080"),
        "indie": ("Dreamer", "#ff6347"),
        "metal": ("Warrior", "#dc143c"),
        "folk": ("Storyteller", "#8b4513"),
        "reggae": ("Free Spirit", "#00ff00"),
        "country": ("Honest Heart", "#deb887")
    }

    for genre, (personality, color) in personality_map.items():
        if genre in genre_string:
            return personality, color
    return "Explorer", "#808080"  # Default gray if no genre matches

# Main App Flow
if is_authenticated():
    try:
        refresh_token()  # Refresh token if expired
        sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

        section = st.radio("What would you like to explore today?", [
            "Mood-Based Music Discovery", 
            "Your Music Insights", 
            "Your Music Personality"
        ])

        if section == "Mood-Based Music Discovery":
            discover_music_by_feelings(sp)
        elif section == "Your Music Insights":
            comprehensive_insights(sp)
        elif section == "Your Music Personality":
            music_personality_analysis(sp)

    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to **Wavvy** 〰")
    st.write("Your music, your vibe. Get personalized insights, discover songs that fit your mood, and explore your unique music personality.")
    authenticate_user()
