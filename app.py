import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import webbrowser

# --- Spotify API Credentials ---
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]
SCOPE = "user-library-read"  # Scope for liked songs

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="MusoMoodify 🎼", page_icon="🎼", layout="wide")

# --- Authenticate with Spotify ---
def get_auth_url():
    """Generate Spotify OAuth URL."""
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    )
    return auth_manager.get_authorize_url()

def fetch_spotify_token(code):
    """Fetch access token using authorization code."""
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    )
    return auth_manager.get_access_token(code)

# --- Main Streamlit App ---
def main():
    st.markdown("<h1 style='text-align: center;'>🎼 MusoMoodify 🎼</h1>", unsafe_allow_html=True)
    st.write("Welcome! Log in with Spotify to explore your liked songs.")

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["auth_code"] = None

    # Step 1: Provide Spotify Authentication URL
    if not st.session_state["authenticated"]:
        st.warning("Please authenticate with Spotify to continue.")
        auth_url = get_auth_url()

        # Manually display the link and open it in a browser
        st.write("Click the link below to log in with Spotify:")
        st.markdown(f"[Login to Spotify]({auth_url})", unsafe_allow_html=True)

        if st.button("Open Spotify Login Page"):
            webbrowser.open(auth_url)

        # Step 2: Input authorization code
        st.info("After logging in, Spotify will provide a code in the URL. Copy and paste it below.")
        code_input = st.text_input("Enter the code from the Spotify URL:", "")

        if code_input:
            try:
                token_info = fetch_spotify_token(code_input)
                if token_info:
                    st.session_state["sp"] = spotipy.Spotify(auth=token_info["access_token"])
                    st.session_state["authenticated"] = True
                    st.success("Successfully connected to Spotify! 🎉")
            except Exception as e:
                st.error(f"Authentication failed: {e}")

    # Step 3: Fetch Liked Songs if Authenticated
    if st.session_state["authenticated"]:
        sp = st.session_state["sp"]
        st.success("✅ Connected to Spotify! Fetching liked songs...")

        try:
            with st.spinner("🎶 Fetching your liked songs..."):
                results = sp.current_user_saved_tracks(limit=50)
                songs = [
                    {
                        "Name": item["track"]["name"],
                        "Artist": ", ".join([artist["name"] for artist in item["track"]["artists"]])
                    }
                    for item in results["items"]
                ]
                if songs:
                    st.dataframe(pd.DataFrame(songs))
                else:
                    st.warning("No liked songs found!")
        except Exception as e:
            st.error(f"Error fetching songs: {e}")

# Run the app
if __name__ == "__main__":
    main()
