import streamlit as st
import time
from supabase_client import supabase

SESSION_KEY = "supabase_session"
MAX_IDLE_SECONDS = 1800  # 30 minutes

def restore_session():
    if "user" in st.session_state:
        return

    session = st.session_state.get(SESSION_KEY)
    if session:
        try:
            supabase.auth.set_session(
                session["access_token"],
                session["refresh_token"]
            )
            st.session_state["user"] = supabase.auth.get_user().user
        except:
            st.session_state.clear()

def save_session(auth_response):
    st.session_state["user"] = auth_response.user
    st.session_state[SESSION_KEY] = {
        "access_token": auth_response.session.access_token,
        "refresh_token": auth_response.session.refresh_token
    }
    st.session_state["last_active"] = time.time()

def track_activity():
    now = time.time()
    last = st.session_state.get("last_active", now)

    if now - last > MAX_IDLE_SECONDS:
        logout()

    st.session_state["last_active"] = now

def logout():
    supabase.auth.sign_out()
    st.session_state.clear()
    st.switch_page("pages/0_🔐_Auth.py")
