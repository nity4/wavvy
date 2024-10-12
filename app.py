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

# Streamlit App Layout
st.set_page_config(page_title="Wavvy 〰", page_icon="〰", layout="centered", initial_sidebar_state="collapsed")

# Initialize session state for token persistence
if 'token_info' not in st.session_state:
    st.session_state['token_info'] = None

# First Page - Welcome Message
st.title("Welcome to Wavvy 〰")
st.write("Wavvy offers you a deep, personal reflection on your emotional journey through music. "
         "Let's discover how your favorite tracks reflect your moods and enhance your well-being.")

st.write("To begin, authorize Wavvy to access your Spotify data.")

# Get the current URL parameters to check for authorization code
query_params = st.experimental_get_query_params()

# If the user has authorized and we have an access token in session_state, use it
if st.session_state['token_info']:
    sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])
    st.success("Spotify Authorization Successful!")
    
    # Fetch Top Tracks from Spotify
    st.header("Your Top Tracks & Emotional Waves 🌊")
    top_tracks = sp.current_user_top_tracks(limit=20)

    track_names = [track['name'] for track in top_tracks['items']]
    track_artists = [track['artists'][0]['name'] for track in top_tracks['items']]

    # Display top tracks
    st.subheader("Your Recent Emotional Journey")
    st.write("Here are your top songs from the last few months, reflecting your mood and emotions.")
    
    df_tracks = pd.DataFrame({'Track': track_names, 'Artist': track_artists})
    st.dataframe(df_tracks)

    # Mock emotional tone analysis (replace with actual analysis or API later)
    mood_data = {
        'Track': track_names,
        'Happiness': [80, 70, 60, 90, 50, 40, 80, 90, 60, 75, 45, 65, 85, 95, 50, 55, 80, 60, 70, 80],
        'Energy': [60, 70, 40, 80, 55, 30, 75, 90, 60, 80, 40, 50, 70, 80, 50, 40, 60, 80, 60, 75],
        'Calmness': [40, 30, 80, 50, 60, 85, 40, 30, 80, 60, 85, 70, 55, 35, 80, 85, 60, 50, 65, 40]
    }
    mood_df = pd.DataFrame(mood_data)

    # Visualize Emotional Journey - Black Background
    st.subheader("Your Emotional WaveMap")
    fig, ax = plt.subplots()
    ax.plot(mood_df['Track'], mood_df['Happiness'], label="Happiness", marker='o', color='yellow')
    ax.plot(mood_df['Track'], mood_df['Energy'], label="Energy", marker='s', color='cyan')
    ax.plot(mood_df['Track'], mood_df['Calmness'], label="Calmness", marker='^', color='magenta')

    # Customize plot appearance
    ax.set_facecolor("black")
    ax.tick_params(axis='x', rotation=90, colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.spines['top'].set_color('white')
    ax.spines['right'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.spines['bottom'].set_color('white')

    plt.title("Your Emotional WaveMap", color='white')
    plt.xlabel("Tracks", color='white')
    plt.ylabel("Emotional Levels", color='white')
    plt.legend(loc="upper left", facecolor='black', edgecolor='white')

    # Show plot
    st.pyplot(fig)

    # Show a summary (Wavvy Wellness Score - mocked here)
    st.subheader("Your Wavvy Wellness Score")
    happiness_score = mood_df['Happiness'].mean()
    calmness_score = mood_df['Calmness'].mean()
    energy_score = mood_df['Energy'].mean()

    st.write(f"**Happiness:** {happiness_score:.2f} / 100")
    st.write(f"**Calmness:** {calmness_score:.2f} / 100")
    st.write(f"**Energy:** {energy_score:.2f} / 100")

    st.write("Based on your recent listening patterns, your **Wavvy Wellness Score** reflects your emotional balance. "
             "Keep riding the emotional waves with your music! 🌊")

elif "code" in query_params:
    # If we have an authorization code in the query parameters, exchange it for an access token
    code = query_params["code"][0]
    token_info = sp_oauth.get_access_token(code)

    # Store the token in session_state
    st.session_state['token_info'] = token_info

    # Provide a simple message for the user to refresh the page manually
    st.write("Spotify authorization successful! Please refresh the page to continue.")
else:
    # If there's no access token, ask the user to authorize with Spotify
    auth_url = sp_oauth.get_authorize_url()
    st.markdown(f'<a href="{auth_url}" target="_self">Click here to authorize with Spotify</a>', unsafe_allow_html=True)
