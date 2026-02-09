import streamlit as st
from utils.auth_manager import logout

def render_navbar():
    st.markdown("""
    <style>
    .navbar {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 60px;
        background: #0f172a;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 24px;
        z-index: 1000;
        border-bottom: 1px solid #1f2937;
    }
    .navbar-title {
        font-size: 18px;
        font-weight: 600;
        color: white;
    }
    .content-offset {
        margin-top: 80px;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([6, 2])

    with col1:
        st.markdown("<div class='navbar-title'>AI Resume Screening System</div>", unsafe_allow_html=True)

    with col2:
        if "user" in st.session_state:
            if st.button("🚪 Sign Out", key="nav_logout"):
                logout()

    st.markdown("<div class='content-offset'></div>", unsafe_allow_html=True)
