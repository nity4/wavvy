import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time

# Spotify API credentials from Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Define the required scope for Spotify access
scope = "user-library-read user-top-read playlist-read-private user-read-private"

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

# Custom CSS for UI customization
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
        text-decoration: none;
        display: inline-block;
        font-weight: bold;
        margin-top: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# Wvvy logo and title
st.markdown("<div class='header-title'>\u3030 Wvvy</div>", unsafe_allow_html=True)

# Authentication Functions
def is_authenticated():
    return "token_info" in st.session_state and st.session_state["token_info"] is not None

def refresh_token():
    if "token_info" in st.session_state and sp_oauth.is_token_expired(st.session_state["token_info"]):
        try:
            token_info = sp_oauth.refresh_access_token(st.session_state["token_info"]["refresh_token"])
            st.session_state["token_info"] = token_info
        except Exception as e:
            st.error(f"Token refresh failed: {e}")

def authenticate_user():
    query_params = st.query_params

    if "code" in query_params:
        code = query_params["code"][0]
        try:
            # Attempt to exchange the code for an access token
            token_info = sp_oauth.get_access_token(code)
            if not token_info:
                raise ValueError("Invalid or expired authorization code.")
            
            # Store the token in session state
            st.session_state["token_info"] = token_info
            st.experimental_set_query_params(**{})  # Clear query params
            st.success("You're authenticated! Click the button below to enter.")
            
            if st.button("Enter Wvvy"):
                st.experimental_rerun()

        except spotipy.exceptions.SpotifyException as e:
            st.error(f"Spotify API error during authentication: {e}")
        except ValueError as e:
            st.error(f"Authorization failed: {e}")
        except Exception as e:
            st.error(f"Unexpected error during authentication: {e}")

    else:
        # Generate and display the Spotify login URL
        auth_url = sp_oauth.get_authorize_url()
        st.markdown(
            f'<a href="{auth_url}" class="login-button">Login with Spotify</a>',
            unsafe_allow_html=True
        )


# Safe API call with retries
def safe_api_call(api_call, retries=3, delay=2, *args, **kwargs):
    for attempt in range(retries):
        try:
            return api_call(*args, **kwargs)
        except spotipy.exceptions.SpotifyException as e:
            st.warning(f"Retrying after Spotify API error: {e}")
            time.sleep(delay * (2 ** attempt))
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            break
    return None

# Retrieve liked songs and audio features
@st.cache_data
def get_liked_songs(_sp):
    try:
        results = _sp.current_user_saved_tracks(limit=50)
        liked_songs = []
        track_ids = [item["track"]["id"] for item in results["items"] if item["track"]]

        for i in range(0, len(track_ids), 10):
            batch_ids = [id for id in track_ids[i:i + 10] if id]
            audio_features_batch = safe_api_call(_sp.audio_features, batch_ids)

            if audio_features_batch:
                for features, track in zip(audio_features_batch, results["items"][i:i + 10]):
                    if features:
                        liked_songs.append({
                            "name": track["track"]["name"],
                            "artist": track["track"]["artists"][0]["name"],
                            "cover": track["track"]["album"]["images"][0]["url"] if track["track"]["album"]["images"] else None,
                            "energy": features.get("energy", 0),
                            "valence": features.get("valence", 0),
                            "tempo": features.get("tempo", 0),
                        })
                    else:
                        st.warning(f"No audio features for track: {track['track']['name']}")
        return liked_songs
    except spotipy.exceptions.SpotifyException as e:
        st.error(f"Spotify API error: {e}")
        return []
    except Exception as e:
        st.error(f"Unexpected error occurred: {e}")
        return []

# Filter songs by mood and intensity
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

# Display songs
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

# Display mood insights
def mood_insights():
    st.write("## Mood Insights")
    mood_breakdown = {
        "Happy": 40,
        "Chill": 30,
        "Energetic": 20,
        "Reflective": 10
    }
    st.write("### Mood Snapshot")
    for mood, percentage in mood_breakdown.items():
        st.write(f"{mood}: {percentage}%")

# Main app logic
if is_authenticated():
    try:
        refresh_token()
        sp = spotipy.Spotify(auth=st.session_state["token_info"]["access_token"])

        tab1, tab2 = st.tabs(["Filter Liked Songs", "Mood Insights"])

        with tab1:
            mood = st.selectbox("Choose your mood:", ["Happy", "Calm", "Energetic", "Sad"])
            intensity = st.slider("Choose intensity:", 1, 5, 3)

            liked_songs = get_liked_songs(sp)
            filtered_liked_songs = filter_songs(liked_songs, mood, intensity)
            display_songs(filtered_liked_songs, "Filtered Liked Songs")

        with tab2:
            mood_insights()

    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to Wvvy")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
