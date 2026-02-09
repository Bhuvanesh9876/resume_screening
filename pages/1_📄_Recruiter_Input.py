import streamlit as st
from supabase_client import supabase

from utils.auth_manager import restore_session, track_activity
from utils.navbar import render_navbar


restore_session()
track_activity()

if "user" not in st.session_state:
    st.switch_page("pages/0_🔐_Auth.py")

render_navbar()


st.header("Recruiter Configuration")

job_title = st.text_input("Job Title")
job_description = st.text_area("Job Description")

required_experience = st.number_input(
    "Required Experience (Years)", min_value=0, step=1
)

must_have_skills = st.text_input("Must-have Skills (comma separated)")
good_to_have_skills = st.text_input("Good-to-have Skills (comma separated)")

if "job_saved" not in st.session_state:
    st.session_state.job_saved = False

# -------- SAVE TO SUPABASE --------
if st.button("Save Job Configuration"):
    if not job_title or not job_description:
        st.error("Job title and description are required.")
    else:
        supabase.table("job_configs").insert({
            "user_id": st.session_state["user"].id,
            "job_title": job_title,
            "job_description": job_description,
            "required_experience": required_experience,
            "must_have_skills": must_have_skills,
            "good_to_have_skills": good_to_have_skills
        }).execute()

        st.session_state.job_saved = True
        st.success("Job configuration saved successfully.")

# -------- NAVIGATION --------
if st.session_state.job_saved:
    if st.button("➡️ Proceed to Resume Processing"):
        st.switch_page("pages/2_⚙️_Processing.py")
