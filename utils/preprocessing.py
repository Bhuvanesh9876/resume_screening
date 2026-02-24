import re
import unicodedata

def clean_text(text: str) -> str:
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)

    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = text.replace("\ufeff", "")

    text = text.replace("\xa0", " ").replace("\u200b", "")
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\u2019", "'")
    
    bullet_chars = "•◦●○◼◻▪▫■□▸▹►▻"
    for bc in bullet_chars:
        text = text.replace(bc, "-")

    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    text = text.replace("\r\n", "\n").replace("\r", "\n")

    text = re.sub(r"\n{3,}", "\n\n", text)

    text = re.sub(r"[ \t]+", " ", text)

    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    text = re.sub(r"page\s*\d+\s*(?:of\s*\d+)?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"curriculum\s*vitae", "", text, flags=re.IGNORECASE)

    return text.strip()

def clean_text_flat(text: str) -> str:
    text = clean_text(text)
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def validate_resume_text(text: str) -> bool:
    if not text:
        return False
    
    cleaned = clean_text(text)
    if len(cleaned) < 50:
        return False
    
    words = cleaned.split()
    if len(words) < 10:
        return False
    
    return True
