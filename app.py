import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import random
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
    scope=scope
)

# Set Streamlit page configuration
st.set_page_config(page_title="Spot-YourMood-ify", layout="wide")

# Custom CSS for black and green-Spotify theme with white heading
st.markdown(
    """
    <style>
    body {
        background: linear-gradient(to right, black, #1DB954);
        color: white;
    }
    .stApp {
        background: linear-gradient(to right, black, #1DB954);
        color: white;
    }
    h1, h2, h3, h4, h5, h6 {
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Function to refresh token if expired
def refresh_token():
    token_info = st.session_state.get('token_info', None)
    if token_info and sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        st.session_state['token_info'] = token_info

# Function to check if the user is authenticated
def is_authenticated():
    return 'token_info' in st.session_state and st.session_state['token_info']

def authenticate_user():
    query_params = st.experimental_get_query_params()
    if "code" in query_params:
        code = query_params["code"][0]
        token_info = sp_oauth.get_access_token(code)
        st.session_state['token_info'] = token_info
        # Clear query parameters indirectly by resetting the URL
        st.write("<script>history.replaceState({}, '', window.location.pathname);</script>", unsafe_allow_html=True)
        st.success("Authentication successful! Please reload the page.")
        return
    else:
        auth_url = sp_oauth.get_authorize_url()
        st.markdown(f'<a href="{auth_url}" target="_self" class="button">Login with Spotify</a>', unsafe_allow_html=True)


# Fetch all liked songs and analyze based on mood and intensity
def get_all_liked_songs(sp, mood=None, intensity=None):
    results = []
    offset = 0
    mood_valence_map = {"Happy": 0.8, "Chill": 0.5, "Energetic": 0.7, "Reflective": 0.3}
    mood_energy_map = {"Happy": 0.7, "Chill": 0.4, "Energetic": 0.9, "Reflective": 0.2}

    valence_target = mood_valence_map.get(mood, None)
    energy_target = mood_energy_map.get(mood, None)

    while True:
        tracks = sp.current_user_saved_tracks(limit=50, offset=offset)
        if not tracks['items']:
            break
        for item in tracks['items']:
            track = item['track']
            features = sp.audio_features([track['id']])
            if features and features[0]:
                feature = features[0]
                if (not mood or abs(feature['valence'] - valence_target) < 0.2) and \
                   (not intensity or abs(feature['energy'] - (intensity / 5)) < 0.2):
                    results.append({
                        'name': track['name'],
                        'artist': track['artists'][0]['name'],
                        'cover': track['album']['images'][0]['url'] if track['album']['images'] else None
                    })
        offset += 50
    return results

# Function to analyze mood-based insights
def analyze_mood_and_insights(sp):
    top_tracks = sp.current_user_top_tracks(limit=50, time_range='medium_term')['items']
    mood_counts = {"Happy": 0, "Chill": 0, "Energetic": 0, "Reflective": 0}
    artist_contributions = {}

    for track in top_tracks:
        features = sp.audio_features([track['id']])
        if features and features[0]:
            feature = features[0]
            valence = feature['valence']
            energy = feature['energy']
            if valence > 0.7 and energy > 0.6:
                mood_counts['Happy'] += 1
            elif valence < 0.4 and energy < 0.5:
                mood_counts['Reflective'] += 1
            elif energy > 0.7:
                mood_counts['Energetic'] += 1
            else:
                mood_counts['Chill'] += 1
            
            artist = track['artists'][0]['name']
            artist_contributions[artist] = artist_contributions.get(artist, 0) + 1

    mood_of_week = max(mood_counts, key=mood_counts.get)
    top_artist = max(artist_contributions, key=artist_contributions.get)

    return mood_counts, mood_of_week, top_artist

if is_authenticated():
    refresh_token()
    sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

    # Page navigation at the top
    selected_page = st.radio("Navigate", ["Filter Liked Songs", "Mood Insights & Therapy"], horizontal=True)

    if selected_page == "Filter Liked Songs":
        st.title("Filter Liked Songs")

        mood = st.selectbox("Choose your mood", ["Happy", "Chill", "Energetic", "Reflective"])
        intensity = st.slider("Choose intensity", 1, 5, 3)

        filtered_songs = get_all_liked_songs(sp, mood, intensity)
        st.write("### Filtered Songs")
        for song in filtered_songs:
            col1, col2 = st.columns([1, 4])
            with col1:
                if song['cover']:
                    st.image(song['cover'], width=80)
            with col2:
                st.write(f"**{song['name']}** by {song['artist']}")

    elif selected_page == "Mood Insights & Therapy":
        st.title("Mood Insights & Therapy Overview")

        mood_counts, mood_of_week, top_artist = analyze_mood_and_insights(sp)

        st.write("### Mood Snapshot")
        st.write(f"**Mood of the Week:** {mood_of_week} (Top Artist: {top_artist})")
        st.write("Mood Breakdown:")
        for mood, count in mood_counts.items():
            st.write(f"{mood}: {count} tracks")

        st.write("### Fun Insights")
        st.write("**What Your Music Says About You:**")
        st.write(f"You're a {mood_of_week} personality! Your top tracks show your affinity for {mood_of_week.lower()} vibes.")
        
        st.write("### Interactive Mood Input")
        selected_mood = st.selectbox("How are you feeling now?", ["Happy", "Chill", "Energetic", "Reflective"])
        if st.button("Get Playlist Recommendation"):
            recommendations = get_all_liked_songs(sp, mood=selected_mood, intensity=3)
            st.write(f"### Recommended Songs for {selected_mood} Mood")
            for song in recommendations:
                st.write(f"**{song['name']}** by {song['artist']}")

else:
    st.title("Welcome to Spot-YourMood-ify")
    authenticate_user()
