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

# Streamlit App Layout - Sleek Dark Mode with Modern Touches
st.set_page_config(page_title="Wavvy", page_icon="🌊", layout="centered", initial_sidebar_state="collapsed")

# Apply CSS for modern, clean, and highly visual design
st.markdown(
    """
    <style>
    body {
        background-color: #0f0f0f;
        color: #e5e5e5;
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
        border-radius: 10px;
        margin-bottom: 20px;
    }
    h1, h2, h3 {
        font-weight: 400;
        color: #e5e5e5;
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
    .personality-box {
        font-size: 3rem;
        color: #ffffff;
        font-weight: bold;
        margin-bottom: 2rem;
        text-align: center;
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
            st.success("Authentication successful! Please refresh to dive into your insights.")
            if st.button("Refresh Now"):
                st.experimental_set_query_params()
        else:
            auth_url = sp_oauth.get_authorize_url()
            st.markdown(f'<a href="{auth_url}" target="_self" style="color: #ff4081;">Click here to log in with Spotify</a>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Authentication error: {e}")

# Enhanced Mood-Based Music Discovery
def discover_music_by_feelings(sp):
    st.header("Curated Music for Every Mood")
    st.write("Tell us how you're feeling and we'll craft a playlist that perfectly fits your vibe.")

    # Mood and intensity input
    feeling = st.selectbox("How are you feeling today?", ["Happy", "Sad", "Chill", "Hype", "Romantic", "Adventurous"])
    intensity = st.slider(f"How {feeling} are you feeling?", 1, 10, help="Slide to match your mood intensity.")

    song_type = st.radio("Looking for something familiar or new?", ["Shuffle My Liked Songs", "Discover New Vibes"])

    try:
        st.write("Curating your playlist based on your mood...")

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
            st.write(f"No tracks match your {feeling.lower()} vibe right now. Try tweaking the intensity or picking a different mood.")

    except Exception as e:
        st.error(f"Error curating your vibe: {e}")

# Enhanced Insights with Fun Stats and Data Without Graphs
def comprehensive_insights(sp):
    st.header("Your Music Journey: Insights")
    st.write("Here's a deeper dive into your music habits. Let's explore what makes your taste unique.")

    try:
        # Fetch user's top artists and genres
        top_artists = sp.current_user_top_artists(limit=5)
        artist_names = [artist['name'] for artist in top_artists['items']]
        top_genres = [artist['genres'] for artist in top_artists['items']]

        # Fetch recently played tracks
        recent_tracks = sp.current_user_recently_played(limit=20)
        total_tracks = len(recent_tracks['items'])
        listening_time = total_tracks * 3  # Assuming each track is ~3 minutes long

        # Fun insights about user's listening habits
        st.subheader("Recent Listening Stats")
        st.write(f"Tracks Played: {total_tracks}")
        st.write(f"Estimated Listening Time: {listening_time} minutes")

        # Fun fact: Favorite listening time
        current_hour = time.localtime().tm_hour
        time_of_day = 'morning' if current_hour < 12 else 'afternoon' if current_hour < 18 else 'night'
        st.write(f"Most Active Listening Time: You seem to vibe the most during the {time_of_day}.")

        # Top 5 Artists and Genres
        st.subheader("Your Top 5 Artists")
        if artist_names:
            for i, artist in enumerate(artist_names):
                st.write(f"{i+1}. {artist}")
        else:
            st.write("We couldn't fetch your top artists. Explore more music to see your top artists here!")

        st.subheader("Your Go-To Genres")
        if top_genres:
            all_genres = [genre for sublist in top_genres for genre in sublist]
            unique_genres = list(set(all_genres))[:5]  # Limit to 5 unique genres
            st.write("You seem to explore these genres:")
            for genre in unique_genres:
                st.write(f"- {genre.capitalize()}")
        else:
            st.write("We're still discovering your genre preferences. Keep listening to find out!")

        # Show average track energy level based on recently played tracks
        energy_levels = [sp.audio_features(track['track']['id'])[0]['energy'] for track in recent_tracks['items']]
        avg_energy = sum(energy_levels) / len(energy_levels) if energy_levels else 0
        energy_description = get_energy_description(avg_energy)

        st.subheader("Your Vibe Energy")
        st.write(f"Your recently played tracks are {energy_description} with an average energy level of {avg_energy:.2f}.")

        # Insightful Fun Fact: New Artists Discovery
        new_artists_count = len(set(track['track']['artists'][0]['name'] for track in recent_tracks['items']))
        st.write(f"New Artists Discovered: You've found {new_artists_count} new artists recently! Keep exploring.")

    except Exception as e:
        st.error(f"Error fetching insights: {e}")

# Helper function to describe the energy of the user's tracks
def get_energy_description(energy_level):
    if energy_level < 0.4:
        return "pretty chill"
    elif 0.4 <= energy_level < 0.7:
        return "a balanced mix"
    else:
        return "high energy, ready to party!"

# Dynamic Music Personality and Color Reveal
def music_personality_analysis(sp):
    st.header("Discover Your Music Personality")
    st.write("Let's analyze your music taste and assign you a unique music personality.")

    try:
        # Fetch top tracks and extract genres from albums
        results = sp.current_user_top_tracks(limit=50)
        top_genres = [track['album'].get('genres', []) for track in results['items'] if 'genres' in track['album']]

        # Flatten the list of genres
        top_genres = [genre for sublist in top_genres for genre in sublist]

        # Backup plan: if no genres found from tracks, use top artists' genres
        if not top_genres:
            st.write("Not enough genre data from your tracks, fetching your top artists for genre analysis...")
            top_artists = sp.current_user_top_artists(limit=5)
            top_genres = [genre for artist in top_artists['items'] for genre in artist.get('genres', [])]

        # Analyze music personality based on genres
        if top_genres:
            st.write("Analyzing your music personality...")
            progress_bar = st.progress(0)
            for percent in range(100):
                time.sleep(0.01)
                progress_bar.progress(percent + 1)

            # Assign personality based on the available genres
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
    st.write("Welcome to **Wavvy** 🌊")
    st.write("Discover your unique music journey, explore tracks that match your mood, and unlock your personalized music personality.")
    authenticate_user()
