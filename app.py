import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import matplotlib.pyplot as plt
import time

# Spotify API credentials from Streamlit Secrets
CLIENT_ID = st.secrets["spotify"]["client_id"]
CLIENT_SECRET = st.secrets["spotify"]["client_secret"]
REDIRECT_URI = st.secrets["spotify"]["redirect_uri"]

# Spotify OAuth Scope to access user's full library and other data
SCOPE = 'user-library-read user-top-read user-read-recently-played'

# Initialize Spotify OAuth
sp_oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE)

# Streamlit App Layout with Sleek Design
st.set_page_config(page_title="Wavvy", page_icon="🌊", layout="centered", initial_sidebar_state="collapsed")

# Custom CSS for Modern, Visual Appeal
st.markdown(
    """
    <style>
    body {
        background-color: #121212;
        color: #f5f5f5;
        font-family: 'Roboto', sans-serif;
    }
    .stButton>button {
        background-color: #0073e6;
        color: #ffffff;
        border-radius: 12px;
        font-size: 1rem;
        padding: 0.5rem;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #ff4081;
    }
    .stImage {
        border-radius: 15px;
        margin-bottom: 12px;
    }
    h1, h2, h3 {
        font-weight: 400;
        color: #ff4081;
    }
    h1 {
        font-size: 3.5rem;
        margin-bottom: 1rem;
    }
    h2 {
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    h3 {
        font-size: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .album-cover {
        display: inline-block;
        margin: 10px;
        text-align: center;
    }
    .artist-cover {
        width: 150px;
        height: 150px;
        border-radius: 50%;
    }
    </style>
    """, unsafe_allow_html=True
)

# Authentication Helpers
def is_authenticated():
    return st.session_state.get('token_info') is not None

def refresh_token():
    if st.session_state['token_info']:
        if sp_oauth.is_token_expired(st.session_state['token_info']):
            token_info = sp_oauth.refresh_access_token(st.session_state['token_info']['refresh_token'])
            st.session_state['token_info'] = token_info

def authenticate_user():
    try:
        if "code" in st.experimental_get_query_params():
            code = st.experimental_get_query_params()["code"][0]
            token_info = sp_oauth.get_access_token(code)
            st.session_state['token_info'] = token_info
            st.experimental_set_query_params(code=None)
            st.success("You're authenticated! Refresh to get your music data.")
            if st.button("Refresh Now"):
                st.experimental_set_query_params()
        else:
            auth_url = sp_oauth.get_authorize_url()
            st.markdown(f'<a href="{auth_url}" target="_self" style="color: #ff4081;">Login with Spotify</a>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Authentication error: {e}")

# Fetch all liked songs from the user's library
def get_all_liked_songs(sp):
    liked_songs = []
    results = sp.current_user_saved_tracks(limit=50, offset=0)
    total_songs = results['total']
    
    while len(liked_songs) < total_songs:
        liked_songs.extend(results['items'])
        offset = len(liked_songs)
        results = sp.current_user_saved_tracks(limit=50, offset=offset)
    
    return liked_songs

# Fetch audio features in batches to avoid the 414 error
def fetch_audio_features_in_batches(sp, song_ids):
    features = []
    batch_size = 100  # Spotify's limit for batch requests

    for i in range(0, len(song_ids), batch_size):
        batch = song_ids[i:i + batch_size]
        audio_features = sp.audio_features(tracks=batch)
        features.extend(audio_features)

    return features

# Refined mood-based filtering
def filter_songs_by_mood(track_features, feeling, intensity):
    filtered_songs = []
    
    for i, track in enumerate(track_features):
        valence = track.get('valence', 0)
        energy = track.get('energy', 0)
        tempo = track.get('tempo', 0)
        danceability = track.get('danceability', 0)
        acousticness = track.get('acousticness', 0)
        liveness = track.get('liveness', 0)
        speechiness = track.get('speechiness', 0)
        instrumentalness = track.get('instrumentalness', 0)

        # Initialize a score for each track
        score = 0
        
        # Modify scoring based on mood
        if feeling == "Happy":
            score += (valence - 0.7) * 10
            score += (energy - (intensity / 10)) * 5
            score += (tempo - 100) * 2
            score += (liveness - 0.5) * 2
        
        elif feeling == "Sad":
            score += (0.3 - valence) * 10
            score += (acousticness - 0.5) * 7  # Stronger weight for acousticness
            score -= (energy - (0.3 * intensity / 10)) * 5  # Reduce energy sharply

        elif feeling == "Chill":
            score += (0.5 - energy) * 7  # Prioritize low energy
            score += (tempo < 100) * 2  # Lower tempo is better
            score += instrumentalness * 2
        
        elif feeling == "Hype":
            score += (energy - 0.8) * 12  # Strong focus on energy
            score += (tempo - 120) * 5
            score += danceability * 3  # More danceability for hype
        
        elif feeling == "Romantic":
            score += (valence - 0.6) * 5
            score += (tempo >= 60 and tempo <= 90) * 6  # Emphasize a narrower tempo range
            score += acousticness * 3  # Add more weight to acoustic for intimacy

        elif feeling == "Adventurous":
            score += danceability * 5
            score += (tempo - 100) * 4
            score += instrumentalness * 3  # Experimental tracks get a boost

        # Filter by intensity scaling
        if score > intensity * 1.8:  # Tighten the threshold for filtering
            filtered_songs.append(track)
    
    return filtered_songs
# Fetch top songs, artists, and genres with time range filter and fun insights
def get_top_items(sp):
    st.header("Your Top Songs, Artists, and Genres")
    
    # Allow users to select time range for insights
    time_range = st.radio("Select time range", ['This Week', 'This Month', 'This Year'], index=1)
    
    time_range_map = {
        'This Week': 'short_term',
        'This Month': 'medium_term',
        'This Year': 'long_term'
    }
    
    spotify_time_range = time_range_map[time_range]
    st.write(f"Showing data for: **{time_range}**")

    # Fetch top tracks
    top_tracks = sp.current_user_top_tracks(time_range=spotify_time_range, limit=10)
    if top_tracks['items']:
        st.subheader("Your Top Songs")
        for i, track in enumerate(top_tracks['items']):
            song_name = track['name']
            artist_name = track['artists'][0]['name']
            album_cover = track['album']['images'][0]['url']
            st.image(album_cover, width=150, caption=f"{i+1}. {song_name} by {artist_name}")
    else:
        st.write(f"No top songs for {time_range}.")

    # Fetch top artists
    top_artists = sp.current_user_top_artists(time_range=spotify_time_range, limit=5)
    if top_artists['items']:
        st.subheader("Your Top Artists")
        for i, artist in enumerate(top_artists['items']):
            artist_name = artist['name']
            artist_cover = artist['images'][0]['url']
            st.image(artist_cover, width=150, caption=f"{i+1}. {artist_name}")
    else:
        st.write(f"No top artists for {time_range}.")

    # Fetch top genres from top artists
    if top_artists['items']:
        st.subheader("Your Top Genres")
        all_genres = [genre for artist in top_artists['items'] for genre in artist['genres']]
        unique_genres = list(set(all_genres))[:5]  # Limit to 5 unique genres

        if unique_genres:
            st.write("You're currently into these genres:")
            for genre in unique_genres:
                st.write(f"🎶 - {genre.capitalize()}")
        else:
            st.write(f"No genres found for {time_range}.")
    else:
        st.write(f"No top genres for {time_range}.")

# Fun insights pop-up after data is loaded
def show_fun_insights(sp, top_artists, top_tracks, time_range):
    st.write(f"Fun insights for **{time_range}**:")

    most_played_artist = top_artists['items'][0]['name'] if top_artists['items'] else 'Unknown Artist'
    most_played_song = top_tracks['items'][0]['name'] if top_tracks['items'] else 'Unknown Song'

    st.toast(f"Your most played artist of {time_range} is **{most_played_artist}** with the song **{most_played_song}**.")
    
    # Fun fact: Number of new artists discovered
    new_artists = len(set(track['artists'][0]['name'] for track in top_tracks['items']))
    st.toast(f"You've discovered **{new_artists}** new artists this {time_range.lower()}.")

    # Fun fact: Genre diversity
    all_genres = [genre for artist in top_artists['items'] for genre in artist['genres']]
    genre_count = len(set(all_genres))
    st.toast(f"Your listening span covered **{genre_count}** unique genres!")

    # Fun fact: Song replay habit
    repeat_songs = random.choice(top_tracks['items'])['name'] if top_tracks['items'] else None
    if repeat_songs:
        st.toast(f"You seem to love replaying **{repeat_songs}** quite a bit!")

# Updated comprehensive insights with time range filter and fun facts
def comprehensive_insights(sp):
    st.header("Your Music Insights")

    try:
        # Fetch user's top items based on time range selection
        time_range = st.radio("Select time range", ['This Week', 'This Month', 'This Year'], index=1)
        spotify_time_range = {'This Week': 'short_term', 'This Month': 'medium_term', 'This Year': 'long_term'}[time_range]

        top_artists = sp.current_user_top_artists(time_range=spotify_time_range, limit=5)
        top_tracks = sp.current_user_top_tracks(time_range=spotify_time_range, limit=10)

        # Display top items
        get_top_items(sp)

        # Show fun insights (pass the time_range variable)
        show_fun_insights(sp, top_artists, top_tracks, time_range)

    except Exception as e:
        st.error(f"Error fetching insights: {e}")

# Mood-Based Music Discovery
def discover_music_by_feelings(sp):
    st.header("Curated Music for Your Mood")
    st.write("Select your mood, and we'll build the perfect playlist.")

    feeling = st.selectbox("What's your vibe today?", ["Happy", "Sad", "Chill", "Hype", "Romantic", "Adventurous"])
    intensity = st.slider(f"How {feeling} are you feeling?", 1, 10)

    try:
        # Fetch recommended or liked songs, based on user selection
        liked_songs = get_all_liked_songs(sp)
        random.shuffle(liked_songs)
        song_ids = [track['track']['id'] for track in liked_songs]

        # Fetch audio features in batches to avoid URL length issues
        features = fetch_audio_features_in_batches(sp, song_ids)

        # Apply filters based on mood and intensity
        filtered_songs = filter_songs_by_mood(features, feeling, intensity)

        if filtered_songs:
            st.subheader(f"Here's your {feeling.lower()} playlist:")
            for i, feature in enumerate(filtered_songs[:10]):
                song = liked_songs[i]['track']
                song_name = song['name']
                artist_name = song['artists'][0]['name']
                album_cover = song['album']['images'][0]['url']
                st.image(album_cover, width=150, caption=f"{song_name} by {artist_name}")
        else:
            st.write(f"No tracks match your {feeling.lower()} vibe right now. Try tweaking the intensity or picking a different mood.")

    except Exception as e:
        st.error(f"Error curating your playlist: {e}")

# Comprehensive insights and stats
def comprehensive_insights(sp):
    st.header("Your Music Journey: Insights")

    try:
        # Fetch user's top artists and genres
        top_artists = sp.current_user_top_artists(limit=5)
        top_tracks = sp.current_user_top_tracks(limit=10)

        # Show insights as toast pop-ups
        show_fun_insights(sp, top_artists, top_tracks)

    except Exception as e:
        st.error(f"Error fetching insights: {e}")

# Music Personality and Color Assignment
def assign_personality_and_color(genres):
    genre_string = ', '.join([g for sublist in genres for g in sublist])
    personality_map = {
        "rock": ("Adventurer", "#ff3b30", "The Rock Warrior"),
        "pop": ("Trendsetter", "#ffd700", "The Chart Topper"),
        "jazz": ("Calm Soul", "#1e90ff", "The Smooth Operator"),
        "electronic": ("Innovator", "#8a2be2", "The Beat Creator"),
        "hip hop": ("Rebel", "#000000", "The Mic Dropper"),
        "classical": ("Old Soul", "#ffa500", "The Timeless Genius"),
        "blues": ("Sentimental", "#008080", "The Deep Thinker"),
        "indie": ("Dreamer", "#ff6347", "The Free Spirit"),
        "metal": ("Warrior", "#dc143c", "The Riff Master"),
        "folk": ("Storyteller", "#8b4513", "The Poetic Soul"),
        "reggae": ("Free Spirit", "#00ff00", "The Groove Rider"),
        "country": ("Honest Heart", "#deb887", "The True Cowboy")
    }

    for genre, (personality, color, label) in personality_map.items():
        if genre in genre_string:
            return personality, color, label
    return "Explorer", "#808080", "The Wanderer"  # Default if no match

# Music Personality Analysis
def music_personality_analysis(sp):
    st.header("Discover Your Music Personality")
    st.write("Let's analyze your music taste and assign you a unique music personality.")

    try:
        # Fetch top tracks and extract genres from albums
        results = sp.current_user_top_tracks(limit=50)
        top_genres = [track['album'].get('genres', []) for track in results['items'] if 'genres' in track['album']]

        # Flatten the list of genres
        top_genres = [genre for sublist in top_genres for genre in sublist]

        # Backup plan: if no genres found from tracks, use top artists' genres
        if not top_genres:
            st.write("Not enough genre data from your tracks, fetching your top artists for genre analysis...")
            top_artists = sp.current_user_top_artists(limit=5)
            top_genres = [genre for artist in top_artists['items'] for genre in artist.get('genres', [])]

        # Analyze music personality based on genres
        if top_genres:
            st.write("Analyzing your music personality...")
            progress_bar = st.progress(0)
            for percent in range(100):
                time.sleep(0.01)
                progress_bar.progress(percent + 1)

            # Assign personality based on the available genres
            personality_type, color, label = assign_personality_and_color(top_genres)
            st.markdown(f"<div class='personality-box' style='color:{color};'>You're a **{personality_type}**! ({label})</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='width:100%; height:120px; background-color:{color}; border-radius:10px;'></div>", unsafe_allow_html=True)
            st.write(f"Your music color is {color}!")
        else:
            st.write("You're a mystery! We couldn't get enough data, so you're an Explorer with a Gray personality.")

    except Exception as e:
        st.error(f"Error analyzing your music personality: {e}")

# Main App Flow
if is_authenticated():
    try:
        refresh_token()
        sp = spotipy.Spotify(auth=st.session_state['token_info']['access_token'])

        section = st.radio("Choose an Experience:", [
            "Mood-Based Music Discovery", 
            "Your Music Insights", 
            "Your Music Personality"
        ])

        if section == "Mood-Based Music Discovery":
            discover_music_by_feelings(sp)
        elif section == "Your Music Insights":
            comprehensive_insights(sp)
        elif section == "Your Music Personality":
            music_personality_analysis(sp)

    except Exception as e:
        st.error(f"Error loading the app: {e}")
else:
    st.write("Welcome to **Wavvy**")
    st.write("Login to explore your personalized music experience.")
    authenticate_user()
