# frontend_app/utils/session.py

import streamlit as st

def clear_session():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
