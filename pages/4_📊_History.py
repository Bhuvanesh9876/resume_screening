import streamlit as st
from utils.history_store import load_history, delete_history_record, clear_all_history

st.header("📊 Screening History")

history = load_history()

if not history:
    st.info("No screening history available.")
    if st.button("➕ Start New Screening"):
        st.switch_page("pages/1_📄_Recruiter_Input.py")
    st.stop()

# ---------------------------------------------------
# CLEAR ALL HISTORY
# ---------------------------------------------------
if st.button("🗑️ Clear All History"):
    clear_all_history()
    st.success("All history cleared.")
    st.rerun()

st.divider()

# ---------------------------------------------------
# HISTORY RECORDS
# ---------------------------------------------------
for idx, record in enumerate(reversed(history)):
    real_index = len(history) - 1 - idx

    with st.expander(f"{record['job_title']} — {record['timestamp']}"):
        st.write(f"**Threshold:** {record['threshold']}")
        st.write(f"**Shortlisted Candidates:** {record['shortlisted_count']}")
        st.table(record["candidates"])

        if st.button(
            "❌ Delete this record",
            key=f"delete_{real_index}"
        ):
            delete_history_record(real_index)
            st.success("History record deleted.")
            st.rerun()

st.divider()

# ---------------------------------------------------
# SAFE NAVIGATION
# ---------------------------------------------------
if st.button("➕ Start New Screening"):
    st.switch_page("pages/1_📄_Recruiter_Input.py")
