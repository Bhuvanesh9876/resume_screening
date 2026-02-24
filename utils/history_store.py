import streamlit as st
import json
import os
from datetime import datetime
from supabase_client import supabase

HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "history.json")

def _load_json_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
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

    if supabase is not None:
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
            try:
                for candidate in shortlisted_candidates:
                    # Convert embedding to list for JSON/Supabase compatibility if it's a numpy array
                    raw_emb = candidate.get("resume_embedding")
                    emb_list = raw_emb.tolist() if hasattr(raw_emb, "tolist") else raw_emb

                    supabase.table("shortlisted_candidates").insert({
                        "history_id": history_id,
                        "candidate_name": candidate["resume_name"].replace(".pdf", ""),
                        "candidate_email": candidate.get("email"),
                        "candidate_phone": candidate.get("phone"),                    
                        "final_score": candidate["scores"]["final_score"],
                        "embedding": emb_list  # Added pgvector support
                    }).execute()
            except Exception as e:
                # Fallback: Insert without embedding if schema update isn't run yet
                print(f"Fallback insert due to schema/embedding error: {e}")
                for candidate in shortlisted_candidates:
                    supabase.table("shortlisted_candidates").insert({
                        "history_id": history_id,
                        "candidate_name": candidate["resume_name"].replace(".pdf", ""),
                        "final_score": candidate["scores"]["final_score"]
                    }).execute()
                    
        except Exception as e:
            st.error(f"❌ Error saving history to database: {str(e)}")
            print(f"Error saving history: {e}")
            pass

    # Save full results data for complete restoration
    records = _load_json_history()
    records.insert(0, {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "job_title": job_data["job_title"],
        "qualification": job_data.get("qualification", ""),
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

    user_id = st.session_state["user"].id

    if supabase is not None:
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
                    # Convert ISO format to readable string
                    # e.g. 2023-10-27T10:00:00.000Z -> 2023-10-27 10:00
                    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    timestamp_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass

                records.append({
                    "id": h["id"],
                    "job_config_id": h.get("job_config_id"),
                    "job_title": display_title,
                    "qualification": job_details.get("required_qualification", ""),
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
    if supabase is None:
        records = _load_json_history()
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