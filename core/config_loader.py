
import json
import os
from typing import Dict, Any

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "config.json")

DEFAULT_CONFIG = {
    "weights": {
        "semantic": 0.5,
        "skill": 0.3,
        "experience": 0.2
    },
    "thresholds": {
        "shortlist": 0.65
    },
    "GROQ_API_KEY": ""
}

def load_config() -> Dict[str, Any]:
    """Load configuration from JSON file, returning defaults if missing or invalid"""
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            
        # Migrate/Merge with defaults to ensure all keys exist
        merged = DEFAULT_CONFIG.copy()
        for section, values in config.items():
            if section in merged and isinstance(values, dict):
                merged[section].update(values)
            else:
                merged[section] = values
                
        return merged
    except Exception:
        return DEFAULT_CONFIG

def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to JSON file"""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception:
        return False

def get_weights() -> Dict[str, float]:
    """Get weight settings"""
    config = load_config()
    return config.get("weights", DEFAULT_CONFIG["weights"])

def get_thresholds() -> Dict[str, float]:
    """Get threshold settings"""
    config = load_config()
    return config.get("thresholds", DEFAULT_CONFIG["thresholds"])
