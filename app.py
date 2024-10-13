# Filter Liked Songs by Mood
def filter_liked_songs_by_mood(track_features, feeling, intensity):
    filtered_songs = []
    fallback_songs = []

    for track in track_features:
        valence = track.get('valence', 0)
        energy = track.get('energy', 0)
        danceability = track.get('danceability', 0)
        tempo = track.get('tempo', 0)

        score = 0  # Base score for filtering
        
        # Apply mood-based logic
        if feeling == "Happy":
            score += (valence - 0.6) * 10 + (energy - intensity / 5) * 5
        elif feeling == "Sad":
            score += (0.3 - valence) * 10 + (energy - 0.4) * 5
        elif feeling == "Chill":
            score += (0.4 - energy) * 7 + (danceability - 0.4) * 5
        elif feeling == "Hype":
            score += (energy - 0.7) * 12 + (tempo - 120) * 0.1
        elif feeling == "Romantic":
            score += (valence - 0.5) * 5 + (danceability - 0.4) * 5
        elif feeling == "Adventurous":
            score += danceability * 5 + (tempo - 120) * 0.1

        # Choose tracks with a score above the intensity threshold
        if score > intensity * 1.2:
            filtered_songs.append(track)
        elif score > intensity * 0.8:
            fallback_songs.append(track)

    # If no strongly matching songs, return fallback songs
    return filtered_songs if filtered_songs else fallback_songs
