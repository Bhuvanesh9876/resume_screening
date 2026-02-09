import streamlit as st
from utils.auth_manager import restore_session, track_activity
from utils.navbar import render_navbar

st.set_page_config(
    page_title="AI Resume Screening System",
    layout="wide",
    initial_sidebar_state="collapsed"
)

restore_session()
track_activity()
render_navbar()

st.markdown("""
<h1>Welcome to AI Resume Screening</h1>
<p>Semantic Matching · Skill Reasoning · Explainable AI</p>
""", unsafe_allow_html=True)

if st.button("🚀 Get Started"):
    if "user" not in st.session_state:
        st.switch_page("pages/0_🔐_Auth.py")
    else:
        st.switch_page("pages/1_📄_Recruiter_Input.py")
