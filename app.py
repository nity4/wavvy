import streamlit as st

if "spotify" in st.secrets:
    st.write("Spotify secrets loaded successfully!")
    st.write(f"Client ID: {st.secrets['spotify']['client_id']}")
else:
    st.error("Spotify secrets are missing!")
