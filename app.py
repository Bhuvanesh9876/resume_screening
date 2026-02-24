import streamlit as st
from utils.auth_manager import restore_session, track_activity
from utils.navbar import render_navbar

st.set_page_config(
    page_title="AI Resume Screening System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

restore_session()
track_activity()
render_navbar()

# Simple Header
st.title("🎯 AI Resume Screening System")
st.markdown("### Llama-3 Powered Candidate Evaluation with Explainable AI")
st.markdown("---")

# Brief description
st.markdown("""
Screen resumes faster and smarter with AI-powered semantic matching, 
automated skill extraction, and clear explanations for every decision.
""")

st.markdown("")

# Key Features - Simple list
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### ✨ What It Does")
    st.markdown("""
    - 🧠 **Semantic Matching** - Deep understanding of resumes
    - 🔍 **Skill Extraction** - Automatic skill identification
    - 📊 **Smart Scoring** - Multi-factor evaluation
    """)

with col2:
    st.markdown("#### 🚀 Why Use It")
    st.markdown("""
    - ⚡ **Fast** - Process resumes in seconds
    - 📈 **Accurate** - AI-powered analysis
    - 📥 **Export Ready** - CSV, JSON, reports
    """)

st.markdown("---")

# Simple How It Works
st.markdown("### How It Works")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("#### 1️⃣ Define Job")
    st.markdown("Enter requirements and skills")

with col2:
    st.markdown("#### 2️⃣ Upload")
    st.markdown("Add PDF resumes")

with col3:
    st.markdown("#### 3️⃣ AI Process")
    st.markdown("Get instant analysis")

with col4:
    st.markdown("#### 4️⃣ Review")
    st.markdown("See ranked results")

st.markdown("---")

# Big CTA Button
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🚀 Get Started", type="primary", use_container_width=True):
        if "user" not in st.session_state:
            st.switch_page("pages/0_🔐_Login.py")
        else:
            st.switch_page("pages/1_📄_Recruiter_Input.py")

st.markdown("")
st.markdown("<p style='text-align:center;color:#666;'>Fast • Accurate • Easy to Use</p>", unsafe_allow_html=True)
