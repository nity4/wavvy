import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import matplotlib.pyplot as plt

# Spotify API credentials stored in Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Scope to access user's top tracks and recently played
SCOPE = 'user-top-read user-read-recently-played'

# Initialize Spotify OAuth
sp_oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE)

# Streamlit App Layout - Set Dark Theme
st.set_page_config(page_title="Wavvy 〰", page_icon="〰", layout="centered", initial_sidebar_state="collapsed")

# Apply Dark Mode CSS
st.markdown(
    """
    <style>
    body {
        background-color: #1c1c1e;
        color: white;
    }
    .stButton>button {
        background-color: #ff5f6d;
        color: white;
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

# Helper function to authenticate user
def authenticate_user():
    try:
        if "code" in st.experimental_get_query_params():
            code = st.experimental_get_query_params()["code"][0]
            token_info = sp_oauth.get_access_token(code)
            st.session_state['token_info'] = token_info
            st.experimental_rerun()
        else:
            auth_url = sp_oauth.get_authorize_url()
            st.markdown(f'<a href="{auth_url}" target="_self">Click here to authorize with Spotify</a>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Authentication error: {e}")

# Main function for Personality-Based Music Discovery
def personality_based_recommendations(sp):
    try:
        st.header("Discover Music Based on Your Personality 🎧")

        # User input for personality and current mood
        personality_type = st.selectbox("Choose your personality type", ["Adventurous", "Calm", "Energetic", "Reflective"])
        current_mood = st.slider("How are you feeling right now? (1 = Low Energy, 10 = High Energy)", 1, 10, 5)

        st.write(f"Based on your personality ({personality_type}) and your current mood ({current_mood}), here are some recommended tracks for you:")

        # Fetch top track recommendations based on personality and mood
        try:
            recommended_tracks = sp.recommendations(seed_genres=['pop', 'chill'], limit=5)
            for track in recommended_tracks['tracks']:
                album_cover = track['album']['images'][0]['url']
                track_name = track['name']
                artist_name = track['artists'][0]['name']
                st.image(album_cover, width=150)
                st.write(f"**{track_name}** by *{artist_name}*")
                st.write("---")
        except Exception as e:
            st.error(f"Error fetching recommendations from Spotify: {e}")
            return
    except Exception as e:
        st.error(f"An error occurred in personality-based recommendations: {e}")

# Function for Predictive Music Recommendation Engine (Life Soundtrack)
def predictive_recommendations():
    try:
        st.header("Your Predictive Life Soundtrack 🎶")
        st.write("Based on upcoming life events or patterns, here’s a soundtrack tailored for your future.")
        
        # User selects life events or moods
        life_events = st.multiselect("Select upcoming events or moods:", ["Vacation", "Work Deadline", "Workout", "Relaxation"])

        for event in life_events:
            st.write(f"For your {event}, here are some tracks to match the vibe:")
            st.write("🎵 Song 1 by Artist A")
            st.write("🎵 Song 2 by Artist B")
            st.write("🎵 Song 3 by Artist C")
            st.write("---")
    except Exception as e:
        st.error(f"Error in predictive recommendations: {e}")

# Function for Music Archetypes and Identity Mapping
def music_archetypes():
    try:
        st.header("Explore Your Musical Archetype 🎭")
        st.write("Based on your listening habits, you fall into the following music archetype:")
        
        # Example archetypes and their descriptions
        archetypes = {"Adventurer": "You love exploring new genres.", "Nostalgic": "You revisit the classics.", "Trendsetter": "You lead music trends."}
        selected_archetype = "Adventurer"
        st.write(f"**You are an {selected_archetype}**: {archetypes[selected_archetype]}")

        st.write("Here are some music recommendations that fit your archetype:")
        st.write("🎧 Track 1 by Artist A")
        st.write("🎧 Track 2 by Artist B")
        st.write("🎧 Track 3 by Artist C")
        st.write("---")
    except Exception as e:
        st.error(f"Error in music archetypes: {e}")

# Function for Deep Social Connectivity and Music Sharing
def social_connectivity(sp):
    try:
        st.header("Connect and Share with Friends 🎶")
        st.write("Share your current music vibe with friends or discover what they are listening to.")

        # Mock example of shared playlists
        friends = ["Friend 1", "Friend 2", "Friend 3"]
        shared_playlist = st.selectbox("Choose a friend to view their shared playlist:", friends)

        st.write(f"Here’s what {shared_playlist} is listening to:")
        st.write("🎧 Track 1 by Artist X")
        st.write("🎧 Track 2 by Artist Y")
        st.write("🎧 Track 3 by Artist Z")
        st.write("You can sync your playlist with theirs and listen together!")

        # Option to share your current vibe
        if st.button("Share My Vibe"):
            st.write("Your current vibe has been shared with your friends!")
    except Exception as e:
        st.error(f"Error in social connectivity: {e}")

# Function for Hyper-Intelligent Music Journaling
def music_journaling():
    try:
        st.header("Your Music Journal 📓")
        st.write("Document your emotional journey through music.")

        # Automatically generated journal entry (mocked for now)
        st.write("**Entry for today:**")
        st.write("You listened to relaxing tracks like Song A by Artist X in the morning, which helped you stay focused.")
        st.write("In the afternoon, you switched to upbeat music to energize yourself for your workout.")

        # Option for users to add their own journal notes
        st.text_area("Add your personal reflection on today's music journey:", "")
        
        if st.button("Save Journal Entry"):
            st.write("Your journal entry has been saved!")
    except Exception as e:
        st.error(f"Error in music journaling: {e}")

# Function for Musical Wellness Insights
def musical_wellness():
    try:
        st.header("Musical Wellness Insights 🌿")
        st.write("Here’s how your music choices are impacting your emotional and mental wellness.")
        
        # Example wellness scores (these would be based on deeper data)
        wellness_data = {
            'Metric': ['Happiness', 'Calmness', 'Energy'],
            'Score': [78, 65, 80]
        }
        df_wellness = pd.DataFrame(wellness_data)

        st.bar_chart(df_wellness.set_index('Metric'))
        st.write("Your music has contributed to a good balance of energy and calmness this week.")
    except Exception as e:
        st.error(f"Error in musical wellness insights: {e}")

# Main Flow of the App
if is_authenticated():
    try:
        sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

        # Main navigation
        section = st.radio("Explore your music journey", [
            "Personality-Based Recommendations", 
            "Predictive Soundtrack", 
            "Music Archetypes", 
            "Social Connectivity", 
            "Music Journaling", 
            "Wellness Insights"
        ])

        if section == "Personality-Based Recommendations":
            personality_based_recommendations(sp)
        elif section == "Predictive Soundtrack":
            predictive_recommendations()
        elif section == "Music Archetypes":
            music_archetypes()
        elif section == "Social Connectivity":
            social_connectivity(sp)
        elif section == "Music Journaling":
            music_journaling()
        elif section == "Wellness
