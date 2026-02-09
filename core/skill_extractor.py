import re

def extract_skills(text, skill_list):
    text = text.lower()
    found = []

    for skill in skill_list:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text):
            found.append(skill)

    return found
