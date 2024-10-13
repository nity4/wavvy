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

# Streamlit App Layout - Set Dark Theme
st.set_page_config(page_title="Wavvy 〰", page_icon="〰", layout="centered", initial_sidebar_state="collapsed")

# Apply Dark Mode CSS
st.markdown(
    """
    <style>
    body {
        background-color: #000000;
        color: black;
    }
    .stButton>button {
        background-color: #ff5f6d;
        color: black;
    }
    .stImage {
        border-radius: 10px;
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
            
            st.success("Authentication successful. Please refresh the page to continue.")
            if st.button("Refresh Now"):
                st.experimental_set_query_params()
        else:
            auth_url = sp_oauth.get_authorize_url()
            st.markdown(f'<a href="{auth_url}" target="_self">Click here to authorize with Spotify</a>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Authentication error: {e}")

# Improved Song Mood Filtering (with more detailed audio features)
def discover_music_by_feelings(sp):
    try:
        st.header("Discover Music Based on Your Feelings")

        # User input for mood and intensity
        feeling = st.selectbox("How are you feeling right now?", ["Happy", "Sad", "Calm", "Energetic"])
        intensity = st.slider(f"How {feeling} are you feeling?", 1, 10)

        # Fetch user's liked songs or discover new songs
        song_type = st.radio("Discover from:", ["My Liked Songs", "New Recommendations"])
        if song_type == "My Liked Songs":
            results = sp.current_user_saved_tracks(limit=50)
            liked_songs = results['items']
        else:
            results = sp.recommendations(seed_genres=['pop', 'rock', 'hip-hop'], limit=50)
            liked_songs = results['tracks']

        # Fetch audio features for songs
        song_ids = [track['track']['id'] for track in liked_songs] if song_type == "My Liked Songs" else [track['id'] for track in liked_songs]
        features = sp.audio_features(tracks=song_ids)

        # Enhanced filtering based on mood and additional audio features
        filtered_songs = []
        for i, song in enumerate(liked_songs):
            feature = features[i]
            if feature:
                valence = feature['valence']
                energy = feature['energy']
                danceability = feature['danceability']
                tempo = feature['tempo']
                
                if feeling == "Happy" and valence > 0.6 and energy >= intensity / 10 and danceability > 0.5:
                    filtered_songs.append(song)
                elif feeling == "Sad" and valence < 0.4 and energy <= intensity / 10 and tempo < 100:
                    filtered_songs.append(song)
                elif feeling == "Calm" and energy < 0.4 and intensity <= 5:
                    filtered_songs.append(song)
                elif feeling == "Energetic" and energy > 0.7 and tempo > 120 and intensity > 5:
                    filtered_songs.append(song)

        if filtered_songs:
            st.write(f"Here are some {feeling.lower()} songs based on your intensity level of {intensity}:")
            for track in filtered_songs:
                album_cover = track['track']['album']['images'][0]['url'] if song_type == "My Liked Songs" else track['album']['images'][0]['url']
                song_name = track['track']['name'] if song_type == "My Liked Songs" else track['name']
                artist_name = track['track']['artists'][0]['name'] if song_type == "My Liked Songs" else track['artists'][0]['name']
                st.image(album_cover, width=150)
                st.write(f"**{song_name}** by *{artist_name}*")
        else:
            st.write("No songs match your mood and intensity right now.")

    except Exception as e:
        st.error(f"Error fetching songs: {e}")

# Comprehensive Insights with Fun Facts
def comprehensive_insights(sp):
    try:
        st.header("Your Comprehensive Music Insights")

        # Fetch top artists and genres
        top_artists = sp.current_user_top_artists(limit=5)
        artist_names = [artist['name'] for artist in top_artists['items']]
        top_genres = [artist['genres'] for artist in top_artists['items']]

        # Display top artists
        st.subheader("Your Top Artists:")
        for artist in top_artists['items']:
            st.image(artist['images'][0]['url'], width=150)
            st.write(f"**{artist['name']}**")

        # Display fun fact about user's music habits
        st.subheader("Fun Fact About You:")
        if "pop" in ', '.join([genre for sublist in top_genres for genre in sublist]):
            st.write(f"🎉 You're a pop lover! Did you know pop songs are scientifically proven to lift your mood?")
        else:
            st.write(f"🎧 You have a diverse taste! You've listened to a wide range of genres recently, keep exploring.")

        # Additional insights on recent listening behavior
        st.subheader("Recent Listening Insights:")
        results = sp.current_user_recently_played(limit=10)
        recent_tracks = results['items']
        total_tracks = len(recent_tracks)
        listening_time = total_tracks * 3

        st.write(f"You've listened to **{total_tracks} tracks** today, totaling about **{listening_time} minutes**.")
        for track in recent_tracks[:5]:
            song_name = track['track']['name']
            album_cover = track['track']['album']['images'][0]['url']
            artist_name = track['track']['artists'][0]['name']
            st.image(album_cover, width=100)
            st.write(f"Track: **{song_name}** by *{artist_name}*")

    except Exception as e:
        st.error(f"Error fetching insights: {e}")

# Expanding Color Visualization Based on Personality
def music_personality_analysis(sp):
    try:
        st.header("Your Music Personality & Color")

        results = sp.current_user_top_tracks(limit=50)
        top_genres = [track['album']['genres'] for track in results['items'] if 'genres' in track['album']]

        if top_genres:
            st.write("Analyzing your music taste...")
            progress_bar = st.progress(0)
            for percent in range(100):
                time.sleep(0.03)
                progress_bar.progress(percent + 1)

            personality_type, color = assign_personality_and_color(top_genres)
            st.write(f"**Your personality type is:** *{personality_type}*")
            st.write(f"**Your associated color is:** *{color}*")

            # Display color visualizations based on personality
            st.markdown(f"<div style='width:100%; height:100px; background-color:{color};'></div>", unsafe_allow_html=True)
        else:
            st.write("You're a mystery! Defaulting to 'Explorer' with color *Green*.")
            st.markdown(f"<div style='width:100%; height:100px; background-color:green;'></div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error analyzing your music personality: {e}")

# Expanded color palette
def assign_personality_and_color(genres):
    genre_string = ', '.join([g for sublist in genres for g in sublist])
    personality_map = {
        "rock": ("Adventurer", "Red"),
        "pop": ("Trendsetter", "Yellow"),
        "jazz": ("Calm", "Blue"),
        "electronic": ("Innovator", "Purple"),
        "hip hop": ("Rebel", "Black"),
        "classical": ("Old Soul", "Gold"),
        "blues": ("Sentimental", "Teal"),
        "indie": ("Dreamer", "Orange"),
        "metal": ("Warrior", "Crimson"),
        "folk": ("Storyteller", "Brown"),
        "reggae": ("Free Spirit", "Green"),
        "country": ("Honest", "Tan")
    }

    for genre, (personality, color) in personality_map.items():
        if genre in genre_string:
            return personality, color
    return "Explorer", "Gray"  # New default color is gray

# Main Flow of the App
if is_authenticated():
    try:
        refresh_token()  # Refresh the token if expired
        sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

        # Main navigation
        section = st.radio("Explore your music journey", [
            "Discover Music Based on Feelings", 
            "Comprehensive Insights", 
            "Music Personality & Color"
        ])

        if section == "Discover Music Based on Feelings":
            discover_music_by_feelings(sp)
        elif section == "Comprehensive Insights":
            comprehensive_insights(sp)
        elif section == "Music Personality & Color":
            music_personality_analysis(sp)

    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to **Wavvy** 〰")
    st.write("Wavvy offers you a personal reflection on your emotional and personality-driven journey through music.")
    authenticate_user()
