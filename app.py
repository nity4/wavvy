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
        elif section == "Wellness Insights":  # Make sure this string is fully closed
            musical_wellness()  # Call the corresponding function

    except Exception as e:
        st.error(f"Error loading the app: {e}")

else:
    st.write("Welcome to **Wavvy** 〰")
    st.write("Wavvy offers you a personal reflection on your emotional and personality-driven journey through music.")
    authenticate_user()
