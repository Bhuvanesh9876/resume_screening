from core.config_loader import load_config

_config = load_config()
_weights = _config.get("weights", {"semantic": 0.5, "skill": 0.3, "experience": 0.2})
_thresholds = _config.get("thresholds", {"shortlist": 0.65})

SEMANTIC_WEIGHT = _weights.get("semantic", 0.5)
SKILL_WEIGHT = _weights.get("skill", 0.3)
EXPERIENCE_WEIGHT = _weights.get("experience", 0.2)

SHORTLIST_THRESHOLD = _thresholds.get("shortlist", 0.65)

# LLM Configurations for Llama-3 Alignment
LLM_MODEL = "llama-3.3-70b-versatile" # Updated from llama3-8b-8192 (decommissioned)
GROQ_API_KEY = _config.get("GROQ_API_KEY") # Can also be set in .streamlit/secrets.toml
