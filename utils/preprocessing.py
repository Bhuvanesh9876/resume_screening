import re

def clean_text(text: str) -> str:
    """
    Basic text cleaning for resumes and job descriptions
    """
    if not text:
        return ""

    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()
