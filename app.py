import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd

# --- Spotify API Credentials ---
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]
SCOPE = "user-library-read"  # Scope for liked songs

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="MusoMoodify 🎼", page_icon="🎼", layout="wide")

# --- Custom CSS for Background and Visuals ---
st.markdown(
    """
    <style>
        body, .stApp {
            background: linear-gradient(to bottom right, black, #1DB954);
            color: white;
        }
        h1, h2, h3 {
            color: white;
            text-align: center;
        }
        .stButton > button {
            background-color: #1DB954;
            color: black;
            font-size: 1em;
            font-weight: bold;
            border-radius: 10px;
        }
        .stButton > button:hover {
            background-color: #1ed760;
        }
        .stTextInput > div > div > input {
            background-color: #222222;
            color: white;
            border-radius: 5px;
            border: 1px solid #1DB954;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Spotify Authentication ---
def authenticate_spotify():
    """Authenticate Spotify and return Spotipy client."""
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    return sp

# --- Main App ---
def main():
    st.markdown("<h1>🎼 MusoMoodify 🎼</h1>", unsafe_allow_html=True)
    st.markdown("<h3>Your Spotify Liked Songs Mood Analyzer</h3>", unsafe_allow_html=True)

    if "sp" not in st.session_state:
        st.session_state["sp"] = authenticate_spotify()
        st.session_state["authenticated"] = True

    # Step 2: Fetch Liked Songs
    if st.session_state["authenticated"]:
        sp = st.session_state["sp"]
        st.success("🎶 Connected to Spotify! Fetching your liked songs...")

        try:
            with st.spinner("🎵 Fetching your liked songs..."):
                results = sp.current_user_saved_tracks(limit=50)
                songs = [
                    {
                        "Name": item["track"]["name"],
                        "Artist": ", ".join([artist["name"] for artist in item["track"]["artists"]]),
                        "Valence": item["track"]["valence"] if "valence" in item["track"] else None,
                        "Energy": item["track"]["energy"] if "energy" in item["track"] else None,
                    }
                    for item in results["items"]
                ]
                songs_df = pd.DataFrame(songs)

                if not songs_df.empty:
                    st.success("🎉 Here are your liked songs:")
                    st.dataframe(songs_df)

                    # Step 3: Mood and Intensity Filtering
                    st.markdown("<h3>Filter Songs by Mood</h3>", unsafe_allow_html=True)
                    mood = st.selectbox(
                        "Select a mood:",
                        ["Happy", "Chill", "Energetic", "Melancholic"]
                    )
                    energy_range = st.slider(
                        "Select energy level:",
                        min_value=0.0, max_value=1.0, value=(0.0, 1.0), step=0.1
                    )

                    # Filtering songs based on mood and energy
                    mood_mapping = {
                        "Happy": lambda row: row["Valence"] > 0.5 and row["Energy"] > 0.5,
                        "Chill": lambda row: row["Valence"] > 0.5 and row["Energy"] <= 0.5,
                        "Energetic": lambda row: row["Valence"] <= 0.5 and row["Energy"] > 0.5,
                        "Melancholic": lambda row: row["Valence"] <= 0.5 and row["Energy"] <= 0.5,
                    }

                    filtered_songs = songs_df[
                        songs_df.apply(mood_mapping[mood], axis=1) &
                        (songs_df["Energy"] >= energy_range[0]) &
                        (songs_df["Energy"] <= energy_range[1])
                    ]

                    if not filtered_songs.empty:
                        st.markdown("### Filtered Songs")
                        st.dataframe(filtered_songs)
                    else:
                        st.warning("No songs match your selected criteria.")

                    # Save playlist (if supported)
                    if st.button("Save Filtered Playlist"):
                        try:
                            track_ids = filtered_songs["ID"].tolist()
                            playlist = sp.user_playlist_create(
                                user=sp.me()["id"],
                                name=f"{mood} Playlist",
                                public=False
                            )
                            sp.user_playlist_add_tracks(playlist_id=playlist["id"], tracks=track_ids)
                            st.success("✅ Playlist created successfully!")
                        except Exception as e:
                            st.error(f"Failed to save playlist: {e}")

                else:
                    st.warning("No liked songs found!")
        except Exception as e:
            st.error(f"Error fetching songs: {e}")

# Run the app
if __name__ == "__main__":
    main()
