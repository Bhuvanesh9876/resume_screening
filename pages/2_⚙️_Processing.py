import streamlit as st
from core.text_extractor import extract_text_from_pdf
from core.embedding_engine import EmbeddingEngine
from core.skill_extractor import extract_skills
from core.experience_extractor import extract_experience
from core.scoring import compute_scores
from utils.auth_manager import restore_session, track_activity
from utils.navbar import render_navbar
import streamlit as st

restore_session()
track_activity()

if "user" not in st.session_state:
    st.switch_page("pages/0_🔐_Auth.py")

render_navbar()

st.header("Resume Upload & Processing")

if "job_data" not in st.session_state:
    st.warning("Please complete recruiter configuration first.")
    st.stop()

uploaded_resumes = st.file_uploader(
    "Upload Resumes (PDF)", type=["pdf"], accept_multiple_files=True
)

if "processing_done" not in st.session_state:
    st.session_state.processing_done = False

if st.button("Process Resumes"):
    if not uploaded_resumes:
        st.error("Please upload at least one resume.")
        st.stop()

    embedder = EmbeddingEngine()
    job_data = st.session_state["job_data"]
    jd_embedding = embedder.embed_query(job_data["job_description"])

    results = []

    with st.spinner("Processing resumes..."):
        for resume in uploaded_resumes:
            text = extract_text_from_pdf(resume)
            resume_embedding = embedder.embed_resume(text)
            semantic_score = float(jd_embedding @ resume_embedding)

            skills = extract_skills(
                text,
                job_data["must_have_skills"] + job_data["good_to_have_skills"]
            )
            experience = extract_experience(text)

            scores = compute_scores(
                semantic_score,
                set(skills),
                experience,
                job_data
            )

            results.append({
                "resume_name": resume.name,
                "resume_text": text,
                "skills": skills,
                "experience": experience,
                "scores": scores
            })

    st.session_state["results"] = results
    st.session_state.processing_done = True
    st.success("Resume processing completed successfully.")

if st.session_state.processing_done:
    if st.button("➡️ View Shortlisted Candidates"):
        st.switch_page("pages/3_🧑‍💼_Shortlisted_Candidates.py")
