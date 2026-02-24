import streamlit as st
from core.text_extractor import extract_text_from_pdf
from core.embedding_engine import EmbeddingEngine
from core.skill_extractor import extract_skills
from core.experience_extractor import extract_experience
from core.skill_extractor import extract_skills
from core.experience_extractor import extract_experience
from core.qualification_extractor import extract_qualifications, match_qualification
from core.contact_extractor import extract_contact_info
from core.scoring import compute_scores
from utils.auth_manager import restore_session, track_activity
from utils.navbar import render_navbar

restore_session()
track_activity()

if "user" not in st.session_state:
    st.switch_page("pages/0_🔐_Login.py")

render_navbar()

st.header("⚙️ Resume Processing")

if "job_data" not in st.session_state:
    st.warning("Please complete job configuration first.")
    if st.button("📄 Go to Job Configuration"):
        st.switch_page("pages/1_📄_Recruiter_Input.py")
    st.stop()

job_data = st.session_state["job_data"]
st.info(f"**Job:** {job_data.get('job_title', 'N/A')} | **Experience:** {job_data.get('required_experience', 0)}+ years")

uploaded_resumes = st.file_uploader(
    "Upload Resumes (PDF)", type=["pdf"], accept_multiple_files=True
)

if "processing_done" not in st.session_state:
    st.session_state.processing_done = False

if st.button("🚀 Process Resumes", type="primary"):
    if not uploaded_resumes:
        st.error("Please upload at least one resume.")
        st.stop()

    embedder = EmbeddingEngine()
    jd_embedding = embedder.embed_query(job_data["job_description"])

    results = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, resume in enumerate(uploaded_resumes):
        status_text.text(f"Processing: {resume.name}")
        progress_bar.progress((i + 1) / len(uploaded_resumes))
        
        text = extract_text_from_pdf(resume)
        
        if not text or not text.strip():
            st.warning(f"⚠️ Could not extract text from {resume.name}. Skipping.")
            continue

        resume_embedding = embedder.embed_resume(text)
        semantic_score = float(jd_embedding @ resume_embedding)

        # Accuracy Fix: Use BOTH job skills AND all known default skills
        # This allows capturing skills the candidate has that weren't explicitly requested
        from core.skill_extractor import get_default_skills
        all_potential_skills = list(set(
            job_data["must_have_skills"] + 
            job_data["good_to_have_skills"] + 
            get_default_skills()
        ))
        
        skills = extract_skills(
            text,
            all_potential_skills
        )
        experience = extract_experience(text)
        
        # Extract qualifications
        qualifications = extract_qualifications(text)
        required_qual = job_data.get("qualification", "")
        qualification_match = match_qualification(qualifications, required_qual)

        # Extract contact info
        contact_info = extract_contact_info(text)
        candidate_name = contact_info.get("name") or resume.name

        scores = compute_scores(
            semantic_score,
            set(skills),
            experience,
            job_data
        )

        results.append({
            "resume_name": candidate_name,  # Use extracted name or fallback to filename
            "resume_filename": resume.name, # Keep original filename reference
            "resume_text": text,
            "resume_embedding": resume_embedding, # Store raw embedding for pgvector
            "email": contact_info.get("email"),
            "phone": contact_info.get("phone"),
            "skills": skills,
            "experience": experience,
            "qualifications": qualifications,
            "qualification_match": qualification_match,
            "scores": scores
        })

    status_text.empty()
    progress_bar.empty()
    
    st.session_state["results"] = results
    st.session_state.processing_done = True
    
    # Reset history_saved so that Shortlisted Candidates page triggers a new autosave
    if "history_saved" in st.session_state:
        st.session_state.history_saved = False
        
    st.success(f"✅ Processed {len(results)} resume(s) successfully!")

if st.session_state.processing_done:
    if st.button("📊 View Shortlisted Candidates", type="primary"):
        st.switch_page("pages/3_🧑‍💼_Shortlisted_Candidates.py")
