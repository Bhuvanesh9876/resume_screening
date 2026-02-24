import re
import unicodedata

def normalize_list(items):
    return [item.strip().lower() for item in items if item]

def clean_text(text: str) -> str:
    if not text:
        return ""
    
    text = unicodedata.normalize("NFKC", text)
    
    text = text.replace("\x00", "").replace("\u200b", "").replace("\ufeff", "")
    
    text = text.replace("\xa0", " ").replace("\t", " ")
    
    bullet_chars = r"[\u2022\u2023\u25E6\u2043\u2219\u25AA\u25AB\u25CF\u25CB\u25A0\u25A1●○•◦◼◻▪▫]"
    
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        cleaned_line = line.strip()
        
        cleaned_line = re.sub(rf"^{bullet_chars}\s*", "", cleaned_line)
        
        cleaned_line = re.sub(r"^[-*+]\s+", "", cleaned_line)
        
        cleaned_line = re.sub(r"^\d+[.)]\s+", "", cleaned_line)
        
        cleaned_line = re.sub(r"^[a-z][.)]\s+", "", cleaned_line, flags=re.IGNORECASE)
        
        cleaned_line = re.sub(r"^[ivxIVX]+[.)]\s+", "", cleaned_line)
        
        cleaned_lines.append(cleaned_line)
    text = "\n".join(cleaned_lines)
    
    text = text.lower()
    
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    text = re.sub(r"[ ]{2,}", " ", text)
    
    text = "\n".join(line.strip() for line in text.split("\n"))
    
    text = text.strip()
    
    return text

def validate_text(text: str) -> bool:
    if not text:
        return False
    
    cleaned = clean_text(text)
    if len(cleaned) < 50:
        return False
    
    words = cleaned.split()
    if len(words) < 10:
        return False
    
    return True
