import json
import os
from datetime import datetime

HISTORY_FILE = "data/history.json"


def _load_raw_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def _save_raw_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def save_history(job_data, threshold, shortlisted_candidates):
    history = _load_raw_history()

    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "job_title": job_data["job_title"],
        "required_experience": job_data["required_experience"],
        "threshold": threshold,
        "shortlisted_count": len(shortlisted_candidates),
        "candidates": [
            {
                "name": c["resume_name"],
                "final_score": c["scores"]["final_score"]
            }
            for c in shortlisted_candidates
        ]
    }

    history.append(record)
    _save_raw_history(history)


def load_history():
    return _load_raw_history()


def delete_history_record(index: int):
    history = _load_raw_history()
    if 0 <= index < len(history):
        history.pop(index)
        _save_raw_history(history)


def clear_all_history():
    _save_raw_history([])
