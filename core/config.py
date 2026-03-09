import json
import os

def load_config():
    """Load configuration from JSON file or environment."""
    config_path = os.path.join("data", "config.json")
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

_config = load_config()
_weights = _config.get("weights", {"semantic": 0.5, "skill": 0.3, "experience": 0.2})
_thresholds = _config.get("thresholds", {"shortlist": 0.65})

SEMANTIC_WEIGHT = _weights.get("semantic", 0.5)
SKILL_WEIGHT = _weights.get("skill", 0.3)
EXPERIENCE_WEIGHT = _weights.get("experience", 0.2)

SHORTLIST_THRESHOLD = _thresholds.get("shortlist", 0.65)

# LLM Configurations for Llama-3 Alignment
LLM_MODEL = "llama-3.3-70b-versatile"
GROQ_API_KEY = _config.get("GROQ_API_KEY") 
