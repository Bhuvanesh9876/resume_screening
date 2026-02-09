import re

def extract_experience(text):
    patterns = [
        r"(\d+)\+?\s+years",
        r"(\d+)\+?\s+yrs"
    ]

    years = []

    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        years.extend([int(m) for m in matches])

    return max(years) if years else 0
