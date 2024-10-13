import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import matplotlib.pyplot as plt
import time

# Spotify API credentials stored in Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Scope to access user's liked songs and recently played tracks
SCOPE = 'user-library-read user-top-read user-read-recently-played'

# Initialize Spotify OAuth
sp_oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE)

# Streamlit App Layout - Sleek Dark Mode
st.set_page_config(page_title="Wavvy 〰", page_icon="〰", layout="centered", initial_sidebar_state="collapsed")

# Apply CSS for visual appeal and Gen Z-friendly aesthetic
st.markdown(
    """
    <style>
    body {
        background-color: #1a1a1d;
        color: #f5f5f5;
        font-family: 'Roboto', sans-serif;
    }
    .stButton>button {
        background-color: #3f51b5;
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
        font-weight: 300;
        color: #ffffff;
    }
    h1 {
        font-size: 3.5rem;
        margin-bottom: 1rem;
        color: #ff4081;
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
        height: 10px;
        border-radius: 5px;
    }
    .personality-box {
        font-size: 3rem;
        color: #ffffff;
        font-weight: bold;
        margin-bottom: 2rem;
        text-align: center;
    }
    .insight-box {
        font-size: 1.25rem;
        margin-top: 1rem;
        background-color: #292929;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .insight-box p {
        font-size: 1.2rem;
    }
    </style>
    """, unsafe_allow_html=True
)

# Helper functions for authentication
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
            st.success("You're all set! Refresh to see your insights.")
            if st.button("Refresh Now"):
                st.experimental_set_query_params()
        else:
            auth_url = sp_oauth.get_authorize_url()
            st.markdown(f'<a href="{auth_url}" target="_self" style="color: #ff4081;">Click here to authorize with Spotify</a>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Authentication error: {e}")

# Improved Mood-Based Music Discovery
def discover_music_by_feelings(sp):
    st.header("Vibe-Based Music Discovery 🎧")
    st.write("Tell me how you're feeling, and I'll craft the perfect playlist for your mood.")

    # Mood and intensity input
    feeling = st.selectbox("What's your mood today?", ["Happy", "Sad", "Chill", "Hype", "Romantic", "Adventurous"])
    intensity = st.slider(f"How {feeling} are you feeling?", 1, 10, help="Adjust how strongly you're feeling that vibe.")
    
    song_type = st.radio("Pick your source:", ["Shuffle My Liked Songs", "Discover New Vibes"])

    try:
        st.write("Curating the perfect vibe for you...")

        if song_type == "Shuffle My Liked Songs":
            results = sp.current_user_saved_tracks(limit=50)
            liked_songs = results['items']
            random.shuffle(liked_songs)  # Shuffle to add variety
        else:
            # Match recommendations to time of day and personal listening habits
            current_hour = time.localtime().tm_hour
            timeframe = 'morning' if current_hour < 12 else 'afternoon' if current_hour < 18 else 'night'
            seed_artists = [artist['id'] for artist in sp.current_user_top_artists(limit=5)['items']]
            results = sp.recommendations(seed_artists=seed_artists, limit=50)
            liked_songs = results['tracks']

        song_ids = [track['track']['id'] if song_type == "Shuffle My Liked Songs" else track['id'] for track in liked_songs]
        features = sp.audio_features(tracks=song_ids)

        filtered_songs = []
        for i, song in enumerate(liked_songs):
            feature = features[i]
            if feature:
                valence, energy, danceability, tempo, acousticness = feature['valence'], feature['energy'], feature['danceability'], feature['tempo'], feature['acousticness']
                
                # Add more robust mood filtering logic
                if feeling == "Happy" and valence > 0.7 and energy >= intensity / 10:
                    filtered_songs.append(song)
                elif feeling == "Sad" and valence < 0.3 and energy <= intensity / 10 and acousticness > 0.5:
                    filtered_songs.append(song)
                elif feeling == "Chill" and energy < 0.5 and tempo < 100 and acousticness > 0.5:
                    filtered_songs.append(song)
                elif feeling == "Hype" and energy > 0.8 and tempo > 120:
                    filtered_songs.append(song)
                elif feeling == "Romantic" and valence > 0.6 and 60 <= tempo <= 90:
                    filtered_songs.append(song)
                elif feeling == "Adventurous" and danceability > 0.6 and tempo > 100:
                    filtered_songs.append(song)

        if filtered_songs:
            st.subheader(f"Here's your {feeling.lower()} playlist:")
            for track in filtered_songs[:10]:
                song_name = track['track']['name'] if song_type == "Shuffle My Liked Songs" else track['name']
                artist_name = track['track']['artists'][0]['name'] if song_type == "Shuffle My Liked Songs" else track['artists'][0]['name']
                album_cover = track['track']['album']['images'][0]['url'] if song_type == "Shuffle My Liked Songs" else track['album']['images'][0]['url']
                st.image(album_cover, width=150)
                st.write(f"**{song_name}** by *{artist_name}*")
        else:
            st.write(f"No tracks match your {feeling.lower()} vibe right now. Try tweaking the intensity or choosing a different mood.")

    except Exception as e:
        st.error(f"Error curating your vibe: {e}")

# Enhanced Insights with Fun Stats and Data Visualization
def comprehensive_insights(sp):
    st.header("Your Music Insights Dashboard 📊")
    st.write("Dive deep into your listening habits and discover fun insights about yourself.")

    try:
        top_artists = sp.current_user_top_artists(limit=5)
        artist_names = [artist['name'] for artist in top_artists['items']]
        top_genres = [artist['genres'] for artist in top_artists['items']]

        # Display top artists with cool language
        st.subheader("Your Top Artists:")
        for artist in top_artists['items']:
            st.image(artist['images'][0]['url'], width=150)
            st.write(f"**{artist['name']}** - You're vibing with this artist lately!")

        # Top genres data visualization
        genre_count = {}
        for genre_list in top_genres:
            for genre in genre_list:
                genre_count[genre] = genre_count.get(genre, 0) + 1

        if genre_count:
            st.subheader("Your Favorite Genres:")
            fig, ax = plt.subplots()
            ax.bar(genre_count.keys(), genre_count.values(), color='#ff6347')
            plt.xticks(rotation=45, ha='right')
            plt.title("Top Genres", fontsize=16)
            st.pyplot(fig)

        # Fun insights about user’s habits
        results = sp.current_user_recently_played(limit=20)
        recent_tracks = results['items']
        total_tracks = len(recent_tracks)
        listening_time = total_tracks * 3  # Assume 3 minutes per track

        st.subheader("Recent Listening Habits:")
        st.write(f"You've played **{total_tracks} tracks** recently, clocking in about **{listening_time} minutes**.")
        
        # Fun fact: Most listened time of day
        current_hour = time.localtime().tm_hour
        time_of_day = 'morning' if current_hour < 12 else 'afternoon' if current_hour < 18 else 'night'
        st.write(f"🎧 You seem to listen most during the **{time_of_day}**!")

        new_artists_count = len(set(track['track']['artists'][0]['name'] for track in recent_tracks))
        st.write(f"🔍 You've discovered **{new_artists_count} new artists** recently. Keep exploring!")

    except Exception as e:
        st.error(f"Error fetching insights: {e}")

# Dynamic Music Personality and Color Reveal
def music_personality_analysis(sp):
    st.header("Discover Your Music Personality 🧠")
    st.write("Let's analyze your music taste and assign you a unique music personality.")

    try:
        results = sp.current_user_top_tracks(limit=50)
        top_genres = [track['album']['genres'] for track in results['items'] if 'genres' in track['album']]

        if top_genres:
            st.write("Analyzing your music personality...")
            progress_bar = st.progress(0)
            for percent in range(100):
                time.sleep(0.01)
                progress_bar.progress(percent + 1)

            personality_type, color, label = assign_personality_and_color(top_genres)
            st.markdown(f"<div class='personality-box' style='color:{color};'>You're a **{personality_type}**! ({label})</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='width:100%; height:120px; background-color:{color}; border-radius:10px;'></div>", unsafe_allow_html=True)
            st.write(f"Your music color is **{color}**!")

        else:
            st.write("You're a mystery! We couldn't get enough data, so you're an Explorer with a *Gray* personality.")

    except Exception as e:
        st.error(f"Error analyzing your music personality: {e}")

# Updated Color Palette for Personalities
def assign_personality_and_color(genres):
    genre_string = ', '.join([g for sublist in genres for g in sublist])
    personality_map = {
        "rock": ("Adventurer", "#ff3b30", "The Rock Warrior"),
        "pop": ("Trendsetter", "#ffd700", "The Chart Topper"),
        "jazz": ("Calm Soul", "#1e90ff", "The Smooth Operator"),
        "electronic": ("Innovator", "#8a2be2", "The Beat Creator"),
        "hip hop": ("Rebel", "#000000", "The Mic Dropper"),
        "classical": ("Old Soul", "#ffa500", "The Timeless Genius"),
        "blues": ("Sentimental", "#008080", "The Deep Thinker"),
        "indie": ("Dreamer", "#ff6347", "The Free Spirit"),
        "metal": ("Warrior", "#dc143c", "The Riff Master"),
        "folk": ("Storyteller", "#8b4513", "The Poetic Soul"),
        "reggae": ("Free Spirit", "#00ff00", "The Groove Rider"),
        "country": ("Honest Heart", "#deb887", "The True Cowboy")
    }

    for genre, (personality, color, label) in personality_map.items():
        if genre in genre_string:
            return personality, color, label
    return "Explorer", "#808080", "The Wanderer"  # Default if no match

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
    st.write("Your music, your vibe. Get personalized insights, discover tracks that match your mood, and explore your unique music personality.")
    authenticate_user()
