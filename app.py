# Refresh Token Function
def refresh_access_token():
    try:
        if "token_info" in st.session_state and "refresh_token" in st.session_state["token_info"]:
            token_info = sp_oauth.refresh_access_token(st.session_state["token_info"]["refresh_token"])
            st.session_state["token_info"] = token_info  # Update session state
            return token_info["access_token"]
        else:
            st.error("No refresh token available. Please log in again.")
            return None
    except Exception as e:
        st.error(f"Failed to refresh access token: {e}")
        return None

# Initialize Spotify Client
def initialize_spotify():
    if "token_info" in st.session_state:
        access_token = st.session_state["token_info"]["access_token"]
        return spotipy.Spotify(auth=access_token)
    return None
