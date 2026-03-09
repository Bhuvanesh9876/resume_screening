import streamlit as st
import json
import os
from datetime import datetime
import uuid
from supabase_client import supabase

HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "history.json")


def _ensure_record_ids(records):
    """Ensure each local JSON history record has a unique id.

    Older versions of the app wrote history records without an `id`, which
    made delete-by-id impossible. This function migrates in-memory records
    and returns (records, changed).
    """
    changed = False
    for record in records:
        if not isinstance(record, dict):
            continue
        if not record.get("id"):
            record["id"] = str(uuid.uuid4())
            changed = True
    return records, changed

def _load_json_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            records = json.load(f)

        if isinstance(records, list):
            records, changed = _ensure_record_ids(records)
            if changed:
                _save_json_history(records)
            return records

        return []
    return []

def _save_json_history(records):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(records, f, indent=2, default=str)

def save_history(job_data, threshold, shortlisted_candidates, all_results=None):

    if "user" not in st.session_state:
        return

    user_id = st.session_state["user"].id

    candidate_list = []
    for c in shortlisted_candidates:
        candidate_list.append({
            "name": c["resume_name"].replace(".pdf", ""),
            "email": c.get("email"),
            "phone": c.get("phone"),
            "final_score": c["scores"]["final_score"]
        })

    is_guest = getattr(st.session_state.get("user"), "id", None) == "guest"

    if supabase is not None and not is_guest:
        try:
            # 1. Create History Record
            history_res = supabase.table("screening_history").insert({
                "user_id": user_id,
                "job_title": job_data["job_title"],
                "job_config_id": job_data.get("job_id"),
                "threshold": threshold,
                "shortlisted_count": len(shortlisted_candidates)
            }).execute()

            history_id = history_res.data[0]["id"]

            # 2. Insert Candidates (Try with new columns first)
            # 2. Insert Candidates 
            # We attempt to insert with 'embedding' first, then fallback to without it.
            # Convert values safely to avoid DB rejects (None -> "", floats strictly cast)
            for candidate in shortlisted_candidates:
                safe_name = candidate.get("resume_name", "Unknown Candidate").replace(".pdf", "")
                safe_email = candidate.get("email") or ""
                safe_phone = candidate.get("phone") or ""
                safe_score = float(candidate["scores"]["final_score"])
                
                try:
                    raw_emb = candidate.get("resume_embedding")
                    emb_list = raw_emb.tolist() if hasattr(raw_emb, "tolist") else raw_emb
                    
                    supabase.table("shortlisted_candidates").insert({
                        "history_id": history_id,
                        "candidate_name": safe_name,
                        "candidate_email": safe_email[:250], # safeguard length
                        "candidate_phone": safe_phone[:50],  # safeguard length
                        "final_score": safe_score,
                        "embedding": emb_list
                    }).execute()
                except Exception as inner_e:
                    print(f"Embedding insert failed: {inner_e}. Falling back to basic insert.")
                    try:
                        supabase.table("shortlisted_candidates").insert({
                            "history_id": history_id,
                            "candidate_name": safe_name,
                            "candidate_email": safe_email[:250],
                            "candidate_phone": safe_phone[:50],
                            "final_score": safe_score
                        }).execute()
                    except Exception as fallback_e:
                        print(f"Basic insert failed for candidate {safe_name}: {fallback_e}")
                        
        except Exception as e:
            st.error(f"❌ Error saving history to Database: {str(e)}")
            print(f"Overall Error saving history: {e}")
            pass

    # Save full results data for complete restoration
    records = _load_json_history()
    records.insert(0, {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "job_title": job_data["job_title"],
        "qualification": job_data.get("qualification", ""),
        "year_of_passing": job_data.get("year_of_passing", []),
        "required_experience": job_data.get("required_experience", 0),
        "must_have_skills": job_data.get("must_have_skills", []),
        "good_to_have_skills": job_data.get("good_to_have_skills", []),
        "job_description": job_data.get("job_description", ""),
        "threshold": threshold,
        "shortlisted_count": len(shortlisted_candidates),
        "candidates": candidate_list,
        "full_results": all_results  # Store complete candidate data
    })
    _save_json_history(records)

def load_history():

    if "user" not in st.session_state:
        return []

    is_guest = getattr(st.session_state.get("user"), "id", None) == "guest"
    user_id = st.session_state["user"].id

    if supabase is not None and not is_guest:
        try:
            # Join with job_configs to get the full details
            history_res = (
                supabase.table("screening_history")
                .select("*, job_configs(*)")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )

            records = []
            for h in history_res.data:
                try:
                    # Try selecting with new columns
                    candidates_res = (
                        supabase.table("shortlisted_candidates")
                        .select("candidate_name, candidate_email, candidate_phone, final_score")
                        .eq("history_id", h["id"])
                        .execute()
                    )
                except Exception:
                    # Fallback: Select old columns only
                    candidates_res = (
                        supabase.table("shortlisted_candidates")
                        .select("candidate_name, final_score")
                        .eq("history_id", h["id"])
                        .execute()
                    )
                
                # Extract job details from the joined table if available
                # Schema: required_qualification, must_have_skills (array), good_to_have_skills (array)
                job_details = h.get("job_configs") or {}
                
                # Parse skills - DB now stores as array, but handle string fallback just in case
                must_have = job_details.get("must_have_skills", [])
                if isinstance(must_have, str):
                    must_have = [s.strip() for s in must_have.split(",") if s.strip()]
                    
                good_to_have = job_details.get("good_to_have_skills", [])
                if isinstance(good_to_have, str):
                   good_to_have = [s.strip() for s in good_to_have.split(",") if s.strip()]

                # Handle job_title (might be in history or joined config)
                display_title = h.get("job_title") or job_details.get("job_title", "Untitled Job")

                # Format timestamp
                timestamp_str = h["created_at"]
                try:
                    # Supabase stores in UTC. Convert to local time (IST +5:30 as per system info)
                    from datetime import timezone, timedelta
                    dt_utc = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    dt_local = dt_utc.astimezone(timezone(timedelta(hours=5, minutes=30)))
                    timestamp_str = dt_local.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass

                records.append({
                    "id": h["id"],
                    "job_config_id": h.get("job_config_id"),
                    "job_title": display_title,
                    "qualification": job_details.get("required_qualification", ""),
                    "year_of_passing": job_details.get("required_year_of_passing", []),
                    "required_experience": job_details.get("required_experience", 0),
                    "must_have_skills": must_have,
                    "good_to_have_skills": good_to_have,
                    "job_description": job_details.get("job_description", ""),
                    "threshold": h["threshold"],
                    "shortlisted_count": h["shortlisted_count"],
                    "timestamp": timestamp_str,
                    "candidates": candidates_res.data
                })
            return records
        except Exception as e:
            print(f"Error loading history: {e}")
            st.error(f"❌ Error loading history: {str(e)}")
            pass

    return _load_json_history()

def get_job_config(job_config_id: str):
    if supabase is None:
        return None
    try:
        res = (
            supabase.table("job_configs")
            .select("*")
            .eq("id", job_config_id)
            .single()
            .execute()
        )
        return res.data
    except Exception:
        return None

def delete_history_record(history_id: str):
    is_guest = False
    try:
        is_guest = getattr(st.session_state.get("user"), "id", None) == "guest"
    except Exception:
        is_guest = False

    if supabase is None or is_guest:
        records = _load_json_history()
        if history_id:
            records = [r for r in records if r.get("id") != history_id]
        _save_json_history(records)
        return

    try:
        # 1. Fetch the history record to get the job_config_id
        history_res = supabase.table("screening_history") \
            .select("job_config_id") \
            .eq("id", history_id) \
            .single() \
            .execute()
        
        job_config_id = history_res.data.get("job_config_id")

        # 2. Delete the history record (candidates will be deleted via ON DELETE CASCADE in DB)
        # Note: shortlisted_candidates table has references screening_history(id) on delete cascade
        supabase.table("screening_history") \
            .delete() \
            .eq("id", history_id) \
            .execute()

        # 3. Delete the job_config if it's not being used by other history records (optional check, 
        # but requested: "delete job_config from the table as well")
        if job_config_id:
            supabase.table("job_configs") \
                .delete() \
                .eq("id", job_config_id) \
                .execute()
    except Exception as e:
        print(f"Error deleting record: {e}")
        pass
def clear_all_history():
    if "user" not in st.session_state:
        return
    
    user_id = st.session_state["user"].id

    # Guest users only use local JSON history, even if Supabase is configured.
    if user_id == "guest":
        _save_json_history([])
        return
    
    if supabase is not None:
        try:
            # 1. Get all history IDs and job_config IDs to clear
            history_res = (
                supabase.table("screening_history")
                .select("id, job_config_id")
                .eq("user_id", user_id)
                .execute()
            )
            
            job_config_ids = [h["job_config_id"] for h in history_res.data if h.get("job_config_id")]
            history_ids = [h["id"] for h in history_res.data]
            
            if history_ids:
                # 2. Delete history records (candidates cascade)
                supabase.table("screening_history") \
                    .delete() \
                    .in_("id", history_ids) \
                    .execute()
            
            if job_config_ids:
                # 3. Delete associated job configs
                supabase.table("job_configs") \
                    .delete() \
                    .in_("id", job_config_ids) \
                    .execute()
        except Exception as e:
            print(f"Error clearing history: {e}")
            pass
    
    _save_json_history([])