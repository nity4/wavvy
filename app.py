import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd

# --- Spotify API Credentials ---
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]
SCOPE = "user-library-read"

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="MusoMoodify 🎼", page_icon="🎼", layout="wide")

# --- Spotify OAuth ---
def spotify_auth():
    """Authenticate Spotify and store credentials."""
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_handler=spotipy.cache_handler.StreamlitSessionCacheHandler(
            token_info=st.session_state.get("token_info")
        ),
        show_dialog=False
    )
    return spotipy.Spotify(auth_manager=auth_manager)

# --- Fetch Liked Songs ---
def fetch_liked_songs(sp):
    """Fetch user's liked songs."""
    with st.spinner("🎶 Fetching your liked songs..."):
        results = sp.current_user_saved_tracks(limit=50)
        songs = [
            {
                "Name": item["track"]["name"],
                "Artist": ", ".join([artist["name"] for artist in item["track"]["artists"]]),
            }
            for item in results["items"]
        ]
        return pd.DataFrame(songs)

# --- Main App ---
def main():
    st.markdown("<h1 style='text-align: center;'>🎼 MusoMoodify 🎼</h1>", unsafe_allow_html=True)

    # Check authentication
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    try:
        sp = spotify_auth()
        st.session_state["authenticated"] = True
    except Exception as e:
        st.error("Failed to authenticate with Spotify. Please try again.")
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        st.success("✅ Successfully connected to Spotify!")
        liked_songs_df = fetch_liked_songs(sp)
        if not liked_songs_df.empty:
            st.success("🎵 Here are your liked songs:")
            st.dataframe(liked_songs_df)
        else:
            st.warning("No liked songs found!")
    else:
        st.warning("Please log in with Spotify to continue.")
        if st.button("Log in with Spotify"):
            spotify_auth()
            st.experimental_rerun()

if __name__ == "__main__":
    main()
