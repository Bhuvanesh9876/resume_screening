import os
import json

# File to store remembered email
REMEMBER_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "remembered_email.json")

def save_remembered_email(email: str):
    """Save email to be remembered for next login"""
    os.makedirs(os.path.dirname(REMEMBER_FILE), exist_ok=True)
    with open(REMEMBER_FILE, "w") as f:
        json.dump({"email": email}, f)

def get_remembered_email() -> str:
    """Get the remembered email, or empty string if none"""
    try:
        if os.path.exists(REMEMBER_FILE):
            with open(REMEMBER_FILE, "r") as f:
                data = json.load(f)
                return data.get("email", "")
    except Exception:
        pass
    return ""

def clear_remembered_email():
    """Clear the remembered email"""
    try:
        if os.path.exists(REMEMBER_FILE):
            os.remove(REMEMBER_FILE)
    except Exception:
        pass
