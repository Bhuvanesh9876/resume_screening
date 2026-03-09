import streamlit as st
from core.xai_engine_v3 import generate_text_based_xai
from utils.history_store import save_history
from utils.auth_manager import restore_session, track_activity
from utils.navbar import render_navbar
from utils.export_utils import export_to_csv
from datetime import datetime
from core.communication_engine import generate_email_draft
from core.scoring import compute_scores
from core.config import SHORTLIST_THRESHOLD, SEMANTIC_WEIGHT, SKILL_WEIGHT, EXPERIENCE_WEIGHT

restore_session()
track_activity()

if "user" not in st.session_state:
    st.switch_page("pages/0_🔐_Login.py")

render_navbar()

# --- Glassmorphism CSS ---
st.markdown("""
<style>
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
    .gradient-header {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
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
    /* Read-only weight badge */
    .weight-badge {
        background: rgba(79, 172, 254, 0.15);
        border: 1px solid rgba(79, 172, 254, 0.3);
        border-radius: 8px;
        padding: 8px 12px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .weight-name { color: #e0e7ff; font-size: 0.85rem; }
    .weight-val  { color: #4facfe; font-weight: 700; font-size: 0.95rem; }
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
# results already contains ONLY edu-cleared candidates (gated by `continue` in Processing)
total_resumes = len(results)

if "history_saved" not in st.session_state:
    st.session_state.history_saved = False

from core.nlp_engine import NLPEngine

@st.cache_resource
def get_nlp_engine():
    return NLPEngine()

nlp_engine = get_nlp_engine()

def extract_candidate_name(resume_data: dict) -> str:
    if resume_data.get("candidate_name"):
        return resume_data["candidate_name"]
    filename = resume_data.get("resume_name", "Unknown Candidate")
    return filename.replace(".pdf", "").replace(".docx", "").replace("_", " ").title()

# ---------------------------------------------------
# FIXED SCORING WEIGHTS (read-only sidebar display)
# ---------------------------------------------------
# Weights are fixed in config.py — not adjustable by the user.
FIXED_WEIGHTS = {
    "semantic": SEMANTIC_WEIGHT,
    "skill": SKILL_WEIGHT,
    "experience": EXPERIENCE_WEIGHT,
}

with st.sidebar:
    st.markdown("### ⚙️ Scoring Weights")
    st.caption("Fixed scoring criteria — applied across all candidates")
    st.markdown(
        f"""
        <div class="weight-badge">
          <span class="weight-name">🧠 Semantic Alignment</span>
          <span class="weight-val">{SEMANTIC_WEIGHT:.0%}</span>
        </div>
        <div class="weight-badge">
          <span class="weight-name">🔧 Skill Match</span>
          <span class="weight-val">{SKILL_WEIGHT:.0%}</span>
        </div>
        <div class="weight-badge">
          <span class="weight-name">💼 Work Experience</span>
          <span class="weight-val">{EXPERIENCE_WEIGHT:.0%}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("⚙️ Adjust in `core/config.py` to change weights.")

# ---------------------------------------------------
# THRESHOLD SLIDER
# ---------------------------------------------------
if "current_threshold" not in st.session_state:
    st.session_state.current_threshold = SHORTLIST_THRESHOLD

threshold = st.slider(
    "Set Shortlisting Threshold",
    min_value=0.0,
    max_value=1.0,
    value=st.session_state.current_threshold,
    step=0.01,
    key="threshold_slider",
)
st.session_state.current_threshold = threshold

# ---------------------------------------------------
# RE-SCORE with FIXED WEIGHTS (efficient: no per-field re-slicing)
# ---------------------------------------------------
if "last_ranking" not in st.session_state:
    st.session_state.last_ranking = {r["resume_filename"]: i for i, r in enumerate(results)}

updated_results = []
for res in results:
    new_scores = compute_scores(
        semantic_score=res["scores"].get("semantic_score", 0),
        resume_skills=res["skills"],
        resume_experience=res["experience"],
        job_data=job_data,
        resume_text_len=len(res.get("resume_text", "")),
        custom_weights=FIXED_WEIGHTS,
    )
    res_copy = res.copy()
    res_copy["scores"] = new_scores
    updated_results.append(res_copy)

shortlisted = sorted(
    [r for r in updated_results if r["scores"]["final_score"] >= threshold],
    key=lambda x: x["scores"]["final_score"],
    reverse=True,
)
rejected = [r for r in updated_results if r["scores"]["final_score"] < threshold]
current_ranking = {r["resume_filename"]: i for i, r in enumerate(shortlisted)}

# ---------------------------------------------------
# HISTORY SAVE
# ---------------------------------------------------
def handle_save(auto=False):
    try:
        save_history(
            job_data=job_data,
            threshold=threshold,
            shortlisted_candidates=shortlisted,
            all_results=updated_results,
        )
        st.session_state.history_saved = True
        if auto:
            st.toast("💾 Autosaved to History")
        else:
            st.success("✅ Screening results finalized and saved to history!")
    except Exception as e:
        st.error(f"Failed to save history: {e}")

# Trigger autosave once upon initial load from processing
if not st.session_state.get("autosave_done", False):
    handle_save(auto=True)
    st.session_state.autosave_done = True

# ---------------------------------------------------
# SUMMARY METRICS
# ---------------------------------------------------
st.markdown("### 📊 Screening Summary")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Edu Passed", total_resumes)
with col2:
    st.metric("Shortlisted", len(shortlisted))
with col3:
    st.metric("Below Threshold", len(rejected))
with col4:
    avg_score = (
        sum(c["scores"]["final_score"] for c in shortlisted) / len(shortlisted)
        if shortlisted else 0
    )
    st.metric("Avg Quality", f"{avg_score:.1%}")

# ---------------------------------------------------
# COMPARISON TRIGGER
# ---------------------------------------------------
if "comparison_ids" not in st.session_state:
    st.session_state.comparison_ids = set()

if shortlisted:
    st.divider()
    comp_col1, comp_col2 = st.columns([3, 1])
    with comp_col1:
        selected_names = [
            r["resume_filename"]
            for r in shortlisted
            if r["resume_filename"] in st.session_state.comparison_ids
        ]
        st.info(f"**For Comparison**: {', '.join(selected_names) if selected_names else 'None selected (Max 3)'}")
    with comp_col2:
        if st.button("⚖️ Compare Selected", type="primary", use_container_width=True, disabled=len(selected_names) < 2):
            st.session_state.show_comparison = True
            st.rerun()

    st.write("")
    if not st.session_state.history_saved:
        if st.button("💾 Save this Screening to History", type="secondary", use_container_width=True):
            handle_save(auto=False)
    else:
        st.success("💾 Saved to History")

# ---------------------------------------------------
# COMPARISON OVERLAY
# ---------------------------------------------------
if st.session_state.get("show_comparison"):
    st.markdown("---")
    st.markdown("### ⚖️ Side-by-Side Comparison")
    if st.button("✖️ Close Comparison"):
        st.session_state.show_comparison = False
        st.rerun()

    comparison_data = [
        r for r in shortlisted if r["resume_filename"] in st.session_state.comparison_ids
    ][:3]

    if len(comparison_data) >= 2:
        cols = st.columns(len(comparison_data))
        for i, cand in enumerate(comparison_data):
            with cols[i]:
                st.markdown(f"#### {extract_candidate_name(cand)}")
                st.metric("Final Score", f"{cand['scores']['final_score']:.1%}")
                st.progress(cand["scores"]["final_score"])
                st.write("**Score Breakdown:**")
                st.caption(f"Skill:      {cand['scores']['skill_score']:.0%}")
                st.caption(f"Domain:     {cand['scores']['semantic_score']:.0%}")
                st.caption(f"Experience: {cand['scores']['experience_score']:.0%}")
                st.write("**Top Skills:**")
                st.write(", ".join(cand["scores"]["matched_skills"][:5]))
                st.write(f"**Experience:** {cand['experience']} years")
        st.markdown("---")

if not shortlisted:
    st.info("No candidates meet the selected threshold.")
    st.stop()

st.divider()

# ---------------------------------------------------
# CANDIDATE CARDS
# ---------------------------------------------------
st.markdown("### 🏆 Top Candidates")

if "view_resume_target" not in st.session_state:
    st.session_state.view_resume_target = None
if "email_draft_target" not in st.session_state:
    st.session_state.email_draft_target = None
if "draft_content" not in st.session_state:
    st.session_state.draft_content = ""

for rank, candidate in enumerate(shortlisted, start=1):
    name = extract_candidate_name(candidate)
    score = candidate["scores"]["final_score"]
    filename = candidate["resume_filename"]

    old_rank = st.session_state.last_ranking.get(filename)
    current_rank = rank - 1
    rank_indicator = ""
    if old_rank is not None:
        if current_rank < old_rank:
            rank_indicator = f" `↑{old_rank - current_rank}`"
        elif current_rank > old_rank:
            rank_indicator = f" `↓{current_rank - old_rank}`"

    header_col1, header_col2 = st.columns([0.9, 0.1])
    with header_col2:
        is_selected = filename in st.session_state.comparison_ids
        if st.checkbox("Add", key=f"comp_{filename}", value=is_selected):
            if filename not in st.session_state.comparison_ids:
                if len(st.session_state.comparison_ids) < 3:
                    st.session_state.comparison_ids.add(filename)
                    st.rerun()
                else:
                    st.toast("Maximum 3 candidates for comparison")
        else:
            if filename in st.session_state.comparison_ids:
                st.session_state.comparison_ids.remove(filename)
                st.rerun()

    with header_col1:
        explanation = generate_text_based_xai(job_data, candidate)

        with st.expander(f"#{rank} {name} • {score:.1%} Match{rank_indicator}", expanded=(rank == 1)):
            draft_type = "next_steps" if score >= threshold else "rejection"
            col_info, col_ai, col_actions = st.columns([1.2, 1.8, 1])

            with col_info:
                st.markdown(f"#### {score:.1%}")
                st.progress(score)
                st.write(f"**Skills:** {candidate['scores']['skill_score']:.0%} | **Exp:** {candidate['scores']['experience_score']:.0%}")
                st.markdown("---")
                if candidate.get("email"):
                    st.write(f"📧 {candidate['email']}")
                if candidate.get("phone"):
                    st.write(f"📱 {candidate['phone']}")

            with col_ai:
                st.markdown("💡 **AI Recruiter Analysis:**")
                st.info(explanation)

            with col_actions:
                if st.button("📄 View Content", key=f"btn_{rank}", use_container_width=True):
                    st.session_state.view_resume_target = (
                        None if st.session_state.view_resume_target == name else name
                    )
                    st.rerun()

                btn_label = "📧 Draft Next Steps" if draft_type == "next_steps" else "📧 Draft Rejection"
                if st.button(btn_label, key=f"draft_{rank}", use_container_width=True):
                    st.session_state.email_draft_target = name
                    with st.spinner("AI is crafting the perfect message..."):
                        st.session_state.draft_content = generate_email_draft(candidate, job_data, draft_type)
                    st.rerun()

            if st.session_state.email_draft_target == name:
                st.markdown("---")
                st.markdown(f"**AI Generated Draft ({draft_type.replace('_', ' ').title()})**")
                st.text_area("Edit Draft", value=st.session_state.draft_content, height=250, key=f"edit_{rank}")
                st.button("Close Draft", key=f"close_{rank}", on_click=lambda: setattr(st.session_state, "email_draft_target", None))

            if st.session_state.view_resume_target == name:
                st.divider()
                st.markdown("**RAW RESUME TEXT (Excerpt)**")
                st.code(candidate.get("resume_text", "No text found")[:2000], language="text")

st.divider()

# ---------------------------------------------------
# BELOW-THRESHOLD CANDIDATES (score rejected, not edu rejected)
# ---------------------------------------------------
if rejected:
    with st.expander(f"🚫 Below Threshold ({len(rejected)})", expanded=False):
        st.caption("These candidates passed education requirements but scored below your threshold.")
        for i, rej_candidate in enumerate(rejected):
            r_name = extract_candidate_name(rej_candidate)
            r_score = rej_candidate["scores"]["final_score"]

            rc1, rc2 = st.columns([3, 1])
            with rc1:
                st.write(f"**{r_name}** ({r_score:.1%})")
            with rc2:
                if st.button("📧 Draft Rejection", key=f"rej_draft_{i}"):
                    st.session_state.email_draft_target = r_name
                    with st.spinner("AI is crafting the perfect message..."):
                        st.session_state.draft_content = generate_email_draft(rej_candidate, job_data, "rejection")
                    st.rerun()

            if st.session_state.email_draft_target == r_name:
                st.markdown(f"**Rejection Draft for {r_name}**")
                st.text_area("Edit Draft", value=st.session_state.draft_content, height=150, key=f"rej_edit_{i}")
                st.button("Close", key=f"rej_close_{i}", on_click=lambda: setattr(st.session_state, "email_draft_target", None))

st.divider()

# ---------------------------------------------------
# EXPORT OPTIONS
# ---------------------------------------------------
st.subheader("📥 Export Results")

csv_data = export_to_csv(shortlisted, job_data)
job_title = job_data.get("job_title", "Job")
clean_title = "".join(c for c in job_title if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
file_name = f"{clean_title}_Candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

st.download_button(
    label="📊 Download CSV",
    data=csv_data,
    file_name=file_name,
    mime="text/csv",
    type="primary",
)

# ---------------------------------------------------
# NAVIGATION
# ---------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
if st.button("📊 Go to History Dashboard", use_container_width=True):
    st.switch_page("pages/4_📊_History.py")
