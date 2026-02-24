import streamlit as st
from utils.auth_manager import logout

def render_navbar():
    st.markdown("""
        <style>
        .content-offset {margin-top: 1rem;}
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

    with col1:
        st.markdown(
            "<h3 style='margin:0; color: white;'>🎯 AI Resume Screener</h3>",
            unsafe_allow_html=True
        )
    
    with col2:
        if st.button("📄 Job", key="nav_job", use_container_width=True):
            st.switch_page("pages/1_📄_Recruiter_Input.py")
    
    with col3:
        if st.button("⚙️ Process", key="nav_process", use_container_width=True):
            st.switch_page("pages/2_⚙️_Processing.py")
    
    with col4:
        if st.button("📊 History", key="nav_history", use_container_width=True):
            st.switch_page("pages/4_📊_History.py")

    with col5:
        if "user" in st.session_state:
            if st.button("🚪 Logout", key="navbar_logout", use_container_width=True):
                logout()

    st.markdown("<div class='content-offset'></div>", unsafe_allow_html=True)
