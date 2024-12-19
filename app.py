import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth

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
    page_icon="\u3030",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Styling
st.markdown("""
    <style>
    body {
        background: linear-gradient(to right, black, #1DB954) !important;
    }
    .stApp {
        background: linear-gradient(to right, black, #1DB954) !important;
    }
    </style>
""", unsafe_allow_html=True)

# Authentication Functions
def is_authenticated():
    return "token_info" in st.session_state and st.session_state["token_info"] is not None

def refresh_token():
    if "token_info" in st.session_state and sp_oauth.is_token_expired(st.session_state["token_info"]):
        token_info = sp_oauth.refresh_access_token(st.session_state["token_info"]["refresh_token"])
        st.session_state["token_info"] = token_info

def authenticate_user():
    query_params = st.experimental_get_query_params()
    if "code" in query_params:
        code = query_params["code"][0]
        try:
            token_info = sp_oauth.get_access_token(code)
            st.session_state["token_info"] = token_info
            st.experimental_set_query_params(**{})
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

# Retrieve liked songs and audio features
@st.cache_data
def get_liked_songs(_sp):
    try:
        results = _sp.current_user_saved_tracks(limit=50)
        liked_songs = []
        track_ids = []

        for item in results["items"]:
            track_ids.append(item["track"]["id"])

        # Fetch audio features in batches
        for i in range(0, len(track_ids), 100):
            batch_ids = track_ids[i:i+100]
            audio_features_batch = _sp.audio_features(batch_ids)
            for features, track in zip(audio_features_batch, results["items"][i:i+100]):
                if features:  # Ensure features are available
                    liked_songs.append({
                        "name": track["track"]["name"],
                        "artist": track["track"]["artists"][0]["name"],
                        "cover": track["track"]["album"]["images"][0]["url"] if track["track"]["album"]["images"] else None,
                        "energy": features.get("energy", 0),
                        "valence": features.get("valence", 0),
                        "tempo": features.get("tempo", 0)
                    })
        return liked_songs
    except spotipy.exceptions.SpotifyException as e:
        st.error(f"Spotify API error: {e}")
        return []

# Filter Songs Based on Mood
def filter_songs(songs, mood, intensity):
    mood_ranges = {
        "Happy": {"valence": (0.6, 1), "tempo": (100, 200)},
        "Calm": {"valence": (0.3, 0.5), "tempo": (40, 100)},
        "Energetic": {"valence": (0.5, 1), "tempo": (120, 200)},
        "Sad": {"valence": (0, 0.3), "tempo": (40, 80)}
    }
    mood_filter = mood_ranges[mood]
    return [
        song for song in songs
        if mood_filter["valence"][0] <= song["valence"] <= mood_filter["valence"][1]
        and mood_filter["tempo"][0] <= song["tempo"] <= mood_filter["tempo"][1]
        and song["energy"] >= (intensity / 5)
    ]

# Display Songs
def display_songs(song_list, title):
    st.write(f"### {title}")
    if song_list:
        for song in song_list:
            col1, col2 = st.columns([1, 4])
            with col1:
                if song["cover"]:
                    st.image(song["cover"], width=80)
            with col2:
                st.write(f"**{song['name']}** by {song['artist']}")
    else:
        st.write("No songs found.")

# Main Logic
if is_authenticated():
    try:
        refresh_token()
        sp = spotipy.Spotify(auth=st.session_state["token_info"]["access_token"])
        tab1, tab2 = st.tabs(["Filter Liked Songs", "Mood Insights"])

        with tab1:
            mood = st.selectbox("Choose your mood:", ["Happy", "Calm", "Energetic", "Sad"])
            intensity = st.slider("Choose intensity:", 1, 5, 3)
            liked_songs = get_liked_songs(sp)
            filtered_songs = filter_songs(liked_songs, mood, intensity)
            display_songs(filtered_songs, "Filtered Liked Songs")

        with tab2:
            st.write("Mood insights coming soon!")

    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    authenticate_user()
