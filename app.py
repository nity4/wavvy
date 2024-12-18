import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd

# --- Spotify API Credentials ---
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]
SCOPE = "user-library-read playlist-modify-private user-top-read"

# --- Streamlit Page Config ---
st.set_page_config(page_title="MusoMoodify 🎼", page_icon="🎼", layout="wide")

# --- Spotify Authentication ---
def authenticate_spotify():
    """
    Authenticate with Spotify and store the Spotify client in session state.
    """
    if "sp" not in st.session_state:
        auth_manager = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE
        )
        st.session_state["sp"] = spotipy.Spotify(auth_manager=auth_manager)
        st.session_state["authenticated"] = True

# --- Fetch Liked Songs ---
def fetch_liked_songs(sp):
    """
    Fetch user's liked songs and analyze audio features.
    """
    results = sp.current_user_saved_tracks(limit=50)
    songs = []
    for item in results["items"]:
        track = item["track"]
        features = sp.audio_features(track["id"])[0]
        songs.append({
            "name": track["name"],
            "artist": ", ".join(artist["name"] for artist in track["artists"]),
            "id": track["id"],
            "image": track["album"]["images"][0]["url"],
            "valence": features["valence"],
            "energy": features["energy"],
        })
    return pd.DataFrame(songs)

# --- Filter Songs by Mood and Intensity ---
def filter_songs(data, mood, intensity):
    """
    Filter liked songs based on mood and intensity.
    """
    mood_conditions = {
        "Happy": (data["valence"] > 0.6) & (data["energy"] > 0.6),
        "Chill": (data["valence"] > 0.6) & (data["energy"] < 0.5),
        "Energetic": (data["valence"] < 0.5) & (data["energy"] > 0.6),
        "Melancholic": (data["valence"] < 0.5) & (data["energy"] < 0.5)
    }
    filtered = data[mood_conditions[mood] & (data["energy"] >= intensity / 10)]
    return filtered

# --- Create Playlist ---
def create_playlist(sp, name, track_ids):
    """
    Create a new Spotify playlist and add selected songs to it.
    """
    user_id = sp.me()["id"]
    playlist = sp.user_playlist_create(user_id, name, public=False, description="MusoMoodify - Mood Based Playlist")
    sp.playlist_add_items(playlist["id"], track_ids)
    return playlist["external_urls"]["spotify"]

# --- Main App Logic ---
authenticate_spotify()
sp = st.session_state["sp"]

st.title("Page 1: Liked Songs with Mood and Intensity Filters 🎼")

# --- Fetch Liked Songs ---
st.write("Fetching your liked songs...")
liked_songs = fetch_liked_songs(sp)

# --- Mood and Intensity Filters ---
st.sidebar.header("Filter Your Songs 🎚️")
selected_mood = st.sidebar.selectbox("Select a Mood:", ["Happy", "Chill", "Energetic", "Melancholic"])
selected_intensity = st.sidebar.slider("Select Intensity (1-10):", 1, 10, 5)

# --- Filter Songs ---
filtered_songs = filter_songs(liked_songs, selected_mood, selected_intensity)

# --- Display Filtered Songs ---
st.subheader(f"Songs Matching Mood: {selected_mood} with Intensity: {selected_intensity}")
if not filtered_songs.empty:
    for _, song in filtered_songs.iterrows():
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; margin-bottom: 10px; color: white;">
                <img src="{song['image']}" width="80" height="80" style="border-radius: 10px; margin-right: 15px;">
                <div>
                    <p style="margin: 0;"><strong>{song['name']}</strong> by {song['artist']}</p>
                    <p style="margin: 0;">Valence: {song['valence']:.2f} | Energy: {song['energy']:.2f}</p>
                </div>
            </div>
            """, unsafe_allow_html=True
        )
else:
    st.warning("No songs found matching the selected mood and intensity.")

# --- Dynamic Playlist Creation ---
if not filtered_songs.empty:
    st.subheader("🎶 Save Your Filtered Songs as a Playlist")
    playlist_name = st.text_input("Enter a name for your playlist:", f"{selected_mood} Vibes")
    if st.button("Create Playlist"):
        track_ids = filtered_songs["id"].tolist()
        playlist_url = create_playlist(sp, playlist_name, track_ids)
        st.success(f"Playlist '{playlist_name}' created successfully!")
        st.markdown(f"[Open Playlist in Spotify]({playlist_url})")
