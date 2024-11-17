        st.header("Hourly Listening Trends")
        listening_hours, listening_weekdays = fetch_behavioral_data(sp)
        
        # Hourly Listening Chart
        fig, ax = plt.subplots()
        listening_hours.sort_index().plot(kind="bar", ax=ax, color="#1DB954")
        ax.set_title("Hourly Listening Trends")
        ax.set_xlabel("Hour of the Day")
        ax.set_ylabel("Tracks Played")
        st.pyplot(fig)

        st.header("Weekly Listening Trends")
        
        # Weekly Listening Chart
        fig, ax = plt.subplots()
        listening_weekdays.sort_index().plot(kind="bar", ax=ax, color="#1DB954")
        ax.set_title("Weekly Listening Trends")
        ax.set_xlabel("Day of the Week (0=Monday, 6=Sunday)")
        ax.set_ylabel("Tracks Played")
        st.pyplot(fig)

        # Personalized Music Personality Gift
        peak_hour = listening_hours.idxmax()
        if peak_hour >= 18:
            personality = "🎶 Night Owl"
            description = "You thrive in the nighttime melodies and vibe when the world sleeps."
        elif peak_hour < 12:
            personality = "☀️ Morning Melodist"
            description = "Your mornings are powered by rhythms, fueling your energy for the day."
        else:
            personality = "🌇 Daytime Dreamer"
            description = "You groove during the day, making every moment a music video."

        st.markdown(f"""
            <div class="gift-box">
                Your Music Personality: {personality}
            </div>
            <div class="personalized-box">
                {description}
            </div>
        """, unsafe_allow_html=True)

else:
    st.write("Please log in to access your Spotify data.")
