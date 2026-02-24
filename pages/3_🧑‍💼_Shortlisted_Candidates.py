import streamlit as st
from core.xai_engine_v3 import generate_text_based_xai
from utils.history_store import save_history
from utils.auth_manager import restore_session, track_activity
from utils.navbar import render_navbar
from utils.export_utils import export_to_csv, export_to_json, generate_summary_report, export_for_email
from datetime import datetime

restore_session()
track_activity()

if "user" not in st.session_state:
    st.switch_page("pages/0_🔐_Login.py")

render_navbar()

# --- Glassmorphism CSS ---
st.markdown("""
<style>
    /* Glass card style */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Header gradient text */
    .gradient-header {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    
    /* Metrics */
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #e0e7ff;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="gradient-header">🧑‍💼 Shortlisted Candidates</div>', unsafe_allow_html=True)

# ---------------------------------------------------
# SAFETY CHECK
# ---------------------------------------------------
if "results" not in st.session_state or "job_data" not in st.session_state:
    st.warning("⚠️ No active screening session found. Redirecting to input...")
    st.button("Go to Job Configuration", on_click=lambda: st.switch_page("pages/1_📄_Recruiter_Input.py"))
    st.stop()

results = st.session_state["results"]
job_data = st.session_state["job_data"]
total_resumes = len(results)

if "history_saved" not in st.session_state:
    st.session_state.history_saved = False

from core.nlp_engine import NLPEngine

@st.cache_resource
def get_nlp_engine():
    return NLPEngine()

nlp_engine = get_nlp_engine()

def extract_candidate_name(resume_data: dict) -> str:
    # 1. Use the pre-extracted name from processing
    if resume_data.get("candidate_name"):
        return resume_data["candidate_name"]
        
    # 2. Fallback to filename if needed
    filename = resume_data.get("resume_name", "Unknown Candidate")
    return filename.replace(".pdf", "").replace(".docx", "").replace("_", " ").title()

# ---------------------------------------------------
# 1️⃣ THRESHOLD
# ---------------------------------------------------
from core.config import SHORTLIST_THRESHOLD

# Move threshold to session state for persistence
if "current_threshold" not in st.session_state:
    st.session_state.current_threshold = SHORTLIST_THRESHOLD

threshold = st.slider(
    "Set Shortlisting Threshold",
    min_value=0.0,
    max_value=1.0,
    value=st.session_state.current_threshold,
    step=0.01,
    key="threshold_slider"
)
st.session_state.current_threshold = threshold

# ---------------------------------------------------
# 2️⃣ FILTER + SORT
# ---------------------------------------------------
shortlisted = [
    r for r in results
    if r["scores"]["final_score"] >= threshold
]

shortlisted = sorted(
    shortlisted,
    key=lambda x: x["scores"]["final_score"],
    reverse=True
)

# ---------------------------------------------------
# 🔄 AUTOSAVE Logic
# ---------------------------------------------------
if "autosave_done" not in st.session_state:
    st.session_state.autosave_done = False

if not st.session_state.autosave_done and shortlisted:
    try:
        save_history(
            job_data=job_data,
            threshold=threshold,
            shortlisted_candidates=shortlisted,
            all_results=results
        )
        st.session_state.autosave_done = True
        st.toast(f"✅ Screening auto-saved to history", icon="💾")
    except Exception as e:
        print(f"Autosave failure: {e}")

# ---------------------------------------------------
# 3️⃣ SUMMARY
# ---------------------------------------------------
st.markdown("### 📊 Screening Summary")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Resumes", total_resumes)
with col2:
    st.metric("Shortlisted", len(shortlisted))
with col3:
    st.metric("Rejected", total_resumes - len(shortlisted))
with col4:
    avg_score = sum(c["scores"]["final_score"] for c in shortlisted) / len(shortlisted) if shortlisted else 0
    st.metric("Avg Quality", f"{avg_score:.1%}")

if not shortlisted:
    st.info("No candidates meet the selected threshold.")
    st.stop()

st.divider()

# ---------------------------------------------------
# 4️⃣ CANDIDATE CARDS
# ---------------------------------------------------
st.markdown("### 🏆 Top Candidates")

# Track which resume to show using a single state key to avoid complex rank-based keys
if "view_resume_target" not in st.session_state:
    st.session_state.view_resume_target = None

for rank, candidate in enumerate(shortlisted, start=1):
    name = extract_candidate_name(candidate)
    score = candidate["scores"]["final_score"]
    
    # Generate explanation
    explanation = generate_text_based_xai(job_data, candidate)
    
    with st.expander(f"#{rank} {name} • {score:.0%} Match", expanded=(rank==1)):
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.markdown(f"#### {score:.0%}")
            st.progress(score)
            st.divider()
            
            # Mini metrics
            st.info(f"**Skills:** {candidate['scores']['skill_score']:.0%}")
            st.info(f"**Experience:** {candidate['scores']['experience_score']:.0%}")
            
            # Contact
            if candidate.get("email"):
                st.write(f"📧 {candidate['email']}")
            if candidate.get("phone"):
                st.write(f"📱 {candidate['phone']}")
            
            # Toggle Button
            if st.button(f"📄 View Content", key=f"btn_{rank}"):
                if st.session_state.view_resume_target == name:
                    st.session_state.view_resume_target = None
                else:
                    st.session_state.view_resume_target = name
                st.rerun()

        with c2:
            st.markdown("##### 💡 AI Assessment")
            st.info(explanation)
            
            # Show resume content if targeted
            if st.session_state.view_resume_target == name:
                st.divider()
                st.markdown("**RAW RESUME TEXT (Excerpt)**")
                st.code(candidate.get("resume_text", "No text found")[:2000], language="text")

st.divider()

# ---------------------------------------------------
# 5️⃣ EXPORT OPTIONS
# ---------------------------------------------------
st.subheader("📥 Export Results")

# Only keeping CSV export as requested to remove others
csv_data = export_to_csv(shortlisted, st.session_state["job_data"])
# Generate filename with job title
job_title = st.session_state["job_data"].get("job_title", "Job")
clean_title = "".join(c for c in job_title if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
file_name = f"{clean_title}_Candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

st.download_button(
    label="📊 Download CSV",
    data=csv_data,
    file_name=file_name,
    mime="text/csv",
    type="primary"
)

# ---------------------------------------------------
# 7️⃣ NAVIGATION (SAFE)
# ---------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
if st.button("📊 Go to History Dashboard", use_container_width=True):
    st.switch_page("pages/4_📊_History.py")
