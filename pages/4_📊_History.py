import streamlit as st
from utils.history_store import load_history, delete_history_record, clear_all_history
from core.config import SHORTLIST_THRESHOLD
from utils.auth_manager import restore_session, track_activity
from utils.navbar import render_navbar

restore_session()
track_activity()

if "user" not in st.session_state:
    st.switch_page("pages/0_🔐_Login.py")

render_navbar()

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
        
        # Show job requirements
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            if record.get("qualification"):
                st.write(f"**Required Qualification:** {record.get('qualification')}")
        with col_info2:
            if record.get("required_experience"):
                st.write(f"**Required Experience:** {record.get('required_experience')} years")
            if record.get("year_of_passing"):
                years = record.get("year_of_passing")
                years_str = ", ".join(map(str, years)) if isinstance(years, list) else str(years)
                st.write(f"**Allowed Years:** {years_str}")
        
        # Show skills
        if record.get("must_have_skills"):
            skills = record.get("must_have_skills")
            if isinstance(skills, list):
                st.write(f"**Required Skills:** {', '.join(skills)}")
            else:
                st.write(f"**Required Skills:** {skills}")
        
        # Professional mapping for display
        df_candidates = record.get("candidates", [])
        if isinstance(df_candidates, list) and df_candidates:
            import pandas as pd
            df = pd.DataFrame(df_candidates)
            # Unified rename map for Supabase (candidate_*) and JSON fallback keys
            rename_map = {
                "candidate_name": "Name", "name": "Name",
                "candidate_email": "Email", "email": "Email",
                "candidate_phone": "Phone", "phone": "Phone",
                "final_score": "Score"
            }
            df = df.rename(columns=rename_map)
            # Ensure only relevant columns are shown, dropping internal keys
            cols_to_show = [c for c in ["Name", "Email", "Phone", "Score"] if c in df.columns]
            
            # Format Score as percentage
            if "Score" in df.columns:
                def _fmt_score(val):
                    try:
                        return f"{float(val):.1%}"
                    except Exception:
                        return "" if val is None else str(val)

                df["Score"] = df["Score"].apply(_fmt_score)
                
            st.table(df[cols_to_show])
        else:
            st.info(f"ℹ️ No candidates passed the {record['threshold']:.0%} threshold in this session.")

        # Check if we have saved results for this screening
        full_results = record.get("full_results")
        
        if full_results:
            col1, col2, col3 = st.columns([1.5, 1.5, 1])
        else:
            col1, col2 = st.columns(2)
        
        with col1:
            if full_results:
                 if st.button(
                    "👁️ View Complete Results",
                    key=f"view_{real_index}",
                    type="primary",
                    help="View the full shortlist and analysis for this screening."
                ):
                    # Load saved results directly
                    st.session_state["job_data"] = {
                        "job_title": record.get("job_title", ""),
                        "qualification": record.get("qualification", ""),
                        "year_of_passing": record.get("year_of_passing", []),
                        "required_experience": record.get("required_experience", 0),
                        "must_have_skills": record.get("must_have_skills", []),
                        "good_to_have_skills": record.get("good_to_have_skills", []),
                        "job_description": record.get("job_description", ""),
                    }
                    st.session_state["results"] = full_results
                    st.session_state["history_saved"] = True
                    st.session_state["threshold"] = record.get("threshold", SHORTLIST_THRESHOLD)
                    st.switch_page("pages/3_🧑‍💼_Shortlisted_Candidates.py")
            else:
                 if st.button(
                    "🔄 Re-screen with this config",
                    key=f"rescreen_{real_index}"
                ):
                    # Load job configuration into session state
                    st.session_state["job_data"] = {
                        "job_title": record.get("job_title", ""),
                        "qualification": record.get("qualification", ""),
                        "year_of_passing": record.get("year_of_passing", []),
                        "required_experience": record.get("required_experience", 0),
                        "must_have_skills": record.get("must_have_skills", []),
                        "good_to_have_skills": record.get("good_to_have_skills", []),
                        "job_description": record.get("job_description", ""),
                    }
                    st.session_state["threshold"] = record.get("threshold", SHORTLIST_THRESHOLD)
                    
                    # Clear previous results to force new screening
                    if "results" in st.session_state:
                        del st.session_state["results"]
                    if "history_saved" in st.session_state:
                        del st.session_state["history_saved"]
                    if "autosave_id" in st.session_state:
                        del st.session_state["autosave_id"]
                    
                    st.session_state["config_loaded_from_history"] = True
                    st.switch_page("pages/1_📄_Recruiter_Input.py")
        
        with col2:
            if full_results:
                if st.button(
                    "🔄 Re-screen (New Upload)",
                    help="Start a new screening process using this job config.",
                    key=f"rescreen_new_{real_index}"
                ):
                     # Load job configuration into session state
                    st.session_state["job_data"] = {
                        "job_title": record.get("job_title", ""),
                        "qualification": record.get("qualification", ""),
                        "year_of_passing": record.get("year_of_passing", []),
                        "required_experience": record.get("required_experience", 0),
                        "must_have_skills": record.get("must_have_skills", []),
                        "good_to_have_skills": record.get("good_to_have_skills", []),
                        "job_description": record.get("job_description", ""),
                    }
                    st.session_state["threshold"] = record.get("threshold", SHORTLIST_THRESHOLD)
                    
                    if "results" in st.session_state:
                        del st.session_state["results"]
                    if "history_saved" in st.session_state:
                        del st.session_state["history_saved"]
                    
                    st.session_state["config_loaded_from_history"] = True
                    st.switch_page("pages/1_📄_Recruiter_Input.py")
            else:
                if st.button(
                    "❌ Delete this record",
                    key=f"delete_{real_index}"
                ):
                    delete_history_record(record.get('id'))
                    st.success("History record deleted.")
                    st.rerun()
        
        if full_results:
            with col3:
                if st.button(
                    "❌ Delete this record",
                    key=f"delete_full_{real_index}"
                ):
                    delete_history_record(record.get('id'))
                    st.success("History record deleted.")
                    st.rerun()

st.divider()

# ---------------------------------------------------
# SAFE NAVIGATION
# ---------------------------------------------------
if st.button("➕ Start New Screening"):
    st.switch_page("pages/1_📄_Recruiter_Input.py")
