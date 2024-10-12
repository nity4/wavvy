import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

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

# Define a function to display top tracks with album covers
def display_top_tracks(sp):
    st.header("Your Top Tracks & Albums 🎶")
    top_tracks = sp.current_user_top_tracks(limit=10)
    for track in top_tracks['items']:
        album_cover = track['album']['images'][0]['url']
        track_name = track['name']
        artist_name = track['artists'][0]['name']
        st.image(album_cover, width=150)
        st.write(f"**{track_name}** by *{artist_name}*")
        st.write("---")

# Define a function to show emotional insights (simplified bar charts)
def display_emotional_insights():
    st.header("Emotional Insights 🎧")
    st.write("Here are your emotional insights based on your recent listening:")
    
    # Example data for emotional analysis
    emotional_data = {
        'Track': ['Song 1', 'Song 2', 'Song 3', 'Song 4'],
        'Happiness': [80, 60, 90, 75],
        'Energy': [50, 70, 85, 65],
        'Calmness': [60, 55, 40, 80]
    }
    df_emotions = pd.DataFrame(emotional_data)

    # Plot simplified horizontal bar charts for emotional insights
    for i, row in df_emotions.iterrows():
        st.write(f"**{row['Track']}**")
        st.write("Emotional Scores:")
        st.write(f"Happiness: {row['Happiness']} | Energy: {row['Energy']} | Calmness: {row['Calmness']}")
        st.bar_chart(pd.DataFrame([row[['Happiness', 'Energy', 'Calmness']]]))

# Define a function to display the Wavvy Wellness Score
def display_wavvy_wellness():
    st.header("Your Wavvy Wellness Score 🌟")
    st.write("Based on your recent emotional journey through music, here’s your wellness score:")
    
    # Example wellness score
    happiness_score = 75
    calmness_score = 65
    energy_score = 70
    avg_wellness_score = (happiness_score + calmness_score + energy_score) / 3
    
    st.metric(label="Overall Wellness Score", value=f"{avg_wellness_score:.2f}/100")
    st.write("This score reflects your emotional balance based on your recent listening habits. Keep riding the waves of your emotions through music!")

# Main Flow of the App
if st.session_state['token_info']:
    sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])
    
    # Use a radio button to move between sections
    section = st.radio("Explore your music journey", ["Top Tracks", "Emotional Insights", "Wellness Score"])

    if section == "Top Tracks":
        display_top_tracks(sp)
    elif section == "Emotional Insights":
        display_emotional_insights()
    elif section == "Wellness Score":
        display_wavvy_wellness()

elif "code" in st.experimental_get_query_params():
    code = st.experimental_get_query_params()["code"][0]
    token_info = sp_oauth.get_access_token(code)
    st.session_state['token_info'] = token_info
    st.experimental_rerun()

else:
    st.write("Welcome to **Wavvy** 〰")
    st.write("Wavvy offers you a personal reflection on your emotional journey through music.")
    auth_url = sp_oauth.get_authorize_url()
    st.markdown(f'<a href="{auth_url}" target="_self">Click here to authorize with Spotify</a>', unsafe_allow_html=True)
