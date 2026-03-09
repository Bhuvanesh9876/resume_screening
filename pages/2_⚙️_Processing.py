import streamlit as st
import json
import os
from datetime import datetime
from core.text_extractor import extract_text
from core.embedding_engine import EmbeddingEngine
from core.skill_extractor import extract_skills, get_default_skills
from core.experience_extractor import extract_experience
from core.qualification_extractor import extract_qualifications, match_qualification
from core.contact_extractor import extract_contact_info
from core.scoring import compute_scores
from core.hybrid_extractor import llm_extraction_fallback, merge_extracted_data
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
    "Upload Resumes (PDF, DOCX, TXT, Images)",
    type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if "processing_done" not in st.session_state:
    st.session_state.processing_done = False

if st.button("🚀 Process Resumes", type="primary"):
    if not uploaded_resumes:
        st.error("Please upload at least one resume.")
        st.stop()

    embedder = EmbeddingEngine()
    jd_embedding = embedder.embed_query(job_data["job_description"])

    # Pre-compute the expanded skill pool once (not per resume)
    all_potential_skills = list(set(
        job_data["must_have_skills"] +
        job_data["good_to_have_skills"] +
        get_default_skills()
    ))

    required_qual = job_data.get("qualification", "None")
    required_years = job_data.get("year_of_passing", [])

    # Only edu-cleared candidates are appended to results (via continue below)
    results = []

    extraction_dir = os.path.join("data", "extractions")
    os.makedirs(extraction_dir, exist_ok=True)

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, resume in enumerate(uploaded_resumes):
        status_text.text(f"Processing: {resume.name} ({i+1}/{len(uploaded_resumes)})")
        progress_bar.progress((i + 1) / len(uploaded_resumes))

        text = extract_text(resume)

        if not text or not text.strip():
            st.warning(f"⚠️ Could not extract text from {resume.name}. Skipping.")
            continue

        resume_embedding = embedder.embed_resume(text)
        semantic_score = float(jd_embedding @ resume_embedding)

        skills = extract_skills(text, all_potential_skills)
        exp_data = extract_experience(text)
        experience = exp_data["years"]
        projects = exp_data["projects"]

        # Education check
        qualifications = extract_qualifications(text)
        qualification_match = match_qualification(qualifications, required_qual, required_years)

        # ── Save a quick extraction record for debugging ──
        safe_filename = "".join([c if c.isalnum() else "_" for c in resume.name])
        json_path = os.path.join(extraction_dir, f"{safe_filename}.json")
        try:
            with open(json_path, "w") as f:
                json.dump({
                    "timestamp": str(datetime.now()),
                    "filename": resume.name,
                    "education": qualifications,
                    "qualification_match": qualification_match,
                    "raw_text_preview": text[:1000],
                }, f, indent=4)
        except Exception:
            pass

        # ── HARD GATE: Reject if degree or year doesn't match ──
        if required_qual and required_qual != "None":
            if not qualification_match.get("matched"):
                st.error(f"**🚫 Rejected: {resume.name}**\n\n*Reason:* {qualification_match.get('details')}")
                continue  # Never reaches results.append() — hard stop here

        # Contact extraction
        contact_info = extract_contact_info(text)

        heuristic_data = {
            "name": contact_info.get("name"),
            "email": contact_info.get("email"),
            "phone": contact_info.get("phone"),
            "linkedin": contact_info.get("linkedin"),
            "github": contact_info.get("github"),
            "portfolio": contact_info.get("portfolio"),
            "skills": skills,
            "experience": experience,
            "projects": projects,
        }

        # LLM fallback if critical data is missing
        if not heuristic_data["name"] or len(heuristic_data["skills"]) < 3:
            status_text.text(f"Deep Scanning: {resume.name} (LLM Fallback)")
            llm_data = llm_extraction_fallback(text)
            if llm_data:
                heuristic_data = merge_extracted_data(heuristic_data, llm_data)
                skills = heuristic_data["skills"]
                experience = heuristic_data["experience"]

        candidate_name = heuristic_data["name"] or resume.name

        scores = compute_scores(
            semantic_score,
            set(skills),
            experience,
            job_data,
            resume_text_len=len(text)
        )

        # Overwrite extraction JSON with full data
        try:
            with open(json_path, "w") as f:
                json.dump({
                    "timestamp": str(datetime.now()),
                    "candidate_name": candidate_name,
                    "filename": resume.name,
                    "email": heuristic_data.get("email"),
                    "phone": heuristic_data.get("phone"),
                    "skills": skills,
                    "experience_years": experience,
                    "education": qualifications,
                    "qualification_match": qualification_match,
                    "scores": scores,
                    "raw_text_preview": text[:1000],
                }, f, indent=4)
        except Exception as e:
            print(f"Error saving extraction JSON: {e}")

        results.append({
            "resume_name": candidate_name,
            "resume_filename": resume.name,
            "resume_text": text,
            "resume_embedding": resume_embedding,
            "email": heuristic_data.get("email"),
            "phone": heuristic_data.get("phone"),
            "linkedin": heuristic_data.get("linkedin"),
            "github": heuristic_data.get("github"),
            "portfolio": heuristic_data.get("portfolio"),
            "skills": skills,
            "experience": experience,
            "projects": heuristic_data.get("projects", []),
            "qualifications": qualifications,
            "qualification_match": qualification_match,
            "scores": scores,
        })

    status_text.empty()
    progress_bar.empty()

    # Store only edu-gated results (continue already filtered out failures)
    st.session_state["results"] = results
    st.session_state.processing_done = True

    # Reset downstream state
    st.session_state.history_saved = False
    st.session_state.comparison_ids = set()
    st.session_state.show_comparison = False
    st.session_state.view_resume_target = None

    total = len(uploaded_resumes)
    passed = len(results)
    edu_fail = total - passed
    st.success(f"✅ Processed {total} resume(s): **{passed} passed** education check, **{edu_fail} rejected**.")

if st.session_state.processing_done:
    if st.button("📊 View Shortlisted Candidates", type="primary"):
        st.switch_page("pages/3_🧑‍💼_Shortlisted_Candidates.py")
