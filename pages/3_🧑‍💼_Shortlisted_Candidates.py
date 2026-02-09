import streamlit as st
from core.xai_engine import generate_xai_explanation
from utils.history_store import save_history
from utils.auth_manager import restore_session, track_activity
from utils.navbar import render_navbar
import streamlit as st

restore_session()
track_activity()

if "user" not in st.session_state:
    st.switch_page("pages/0_🔐_Auth.py")

render_navbar()


st.header("🧑‍💼 Shortlisting & Explainability")

# ---------------------------------------------------
# SAFETY CHECK
# ---------------------------------------------------
if "results" not in st.session_state:
    st.warning("Please process resumes first.")
    st.stop()

results = st.session_state["results"]
total_resumes = len(results)

if "history_saved" not in st.session_state:
    st.session_state.history_saved = False


def extract_candidate_name(filename: str) -> str:
    return (
        filename.replace(".pdf", "")
        .replace("_", " ")
        .replace("-", " ")
        .title()
    )

# ---------------------------------------------------
# 1️⃣ THRESHOLD
# ---------------------------------------------------
threshold = st.slider(
    "Set Shortlisting Threshold",
    min_value=0.0,
    max_value=1.0,
    value=0.65,
    step=0.01
)

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
# 3️⃣ SUMMARY
# ---------------------------------------------------
st.markdown(
    f"""
### 📊 Screening Summary
- **Total resumes uploaded:** {total_resumes}
- **Shortlisted candidates:** {len(shortlisted)}
"""
)

if not shortlisted:
    st.info("No candidates meet the selected threshold.")
    st.stop()

st.divider()

# ---------------------------------------------------
# 4️⃣ CANDIDATE CARDS
# ---------------------------------------------------
st.subheader("🏆 Shortlisted Candidates (Ranked)")

for rank, candidate in enumerate(shortlisted, start=1):
    name = extract_candidate_name(candidate["resume_name"])
    score = candidate["scores"]["final_score"]

    with st.expander(f"{rank}. {name} — Score: {score}"):
        st.markdown("#### 📈 Score Breakdown")
        st.json(candidate["scores"])

        if st.button(
            f"Why was {name} shortlisted?",
            key=f"xai_{rank}"
        ):
            explanation = generate_xai_explanation(
                st.session_state["job_data"],
                candidate
            )

            st.markdown("#### 🧠 Explainability (XAI)")
            st.write(explanation)

st.divider()

# ---------------------------------------------------
# 5️⃣ SAVE TO HISTORY (ACTION)
# ---------------------------------------------------
if st.button("💾 Save this screening to History"):
    save_history(
        job_data=st.session_state["job_data"],
        threshold=threshold,
        shortlisted_candidates=shortlisted
    )
    st.session_state.history_saved = True
    st.success("Screening saved to history.")

# ---------------------------------------------------
# 6️⃣ NAVIGATION (SAFE)
# ---------------------------------------------------
if st.session_state.history_saved:
    if st.button("📊 Go to History Dashboard"):
        st.switch_page("pages/4_📊_History.py")
