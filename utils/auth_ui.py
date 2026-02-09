import streamlit as st
from supabase_client import supabase

def render_auth_sidebar():
    with st.sidebar:
        st.markdown("### 👤 Account")

        if "user" in st.session_state:
            st.success(st.session_state["user"].email)

            if st.button("🚪 Sign Out", key="signout_btn"):
                supabase.auth.sign_out()
                st.session_state.clear()
                st.switch_page("pages/0_🔐_Auth.py")

        else:
            st.warning("Not logged in")
            if st.button("🔐 Login / Signup"):
                st.switch_page("pages/0_🔐_Auth.py")
