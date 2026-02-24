"""
Contact Extractor Module

This module handles the extraction of contact information (name, email, phone)
from resume text using regex patterns and heuristics.
"""

import re
from typing import Dict

_HEADER_SKIP = {
    "resume", "cv", "curriculum", "vitae", "objective", "summary",
    "profile", "contact", "details", "information", "personal",
    "phone", "email", "address", "linkedin", "github", "portfolio",
    "mobile", "tel", "website", "http", "https", "www",
}

_TITLE_WORDS = {
    "software", "engineer", "developer", "senior", "junior", "lead",
    "manager", "designer", "analyst", "intern", "consultant", "architect",
    "data", "scientist", "full", "stack", "front", "back", "end",
    "devops", "cloud", "machine", "learning", "project", "product",
    "experience", "education", "skills", "certifications", "work",
    "professional", "technical", "references", "achievements",
}

def extract_email(text: str) -> str:
    """
    Extract the first valid email address found in the text.
    Handles standard emails and some obfuscated formats.
    """
    if not text:
        return ""

    # Pre-process text to remove weird spacing issues sometimes found in PDFs
    # e.g. "email @ domain . com" -> "email@domain.com"
    clean_text = text.replace(" @ ", "@").replace(" . ", ".")

    # 1. Strict regex for standard emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, clean_text)
    if match:
        return match.group(0)

    # 2. Relaxed regex trying to catch "Email: <value>" patterns
    # Matches "Email: john.doe at car.com" type obfuscation or just labeled lines
    label_pattern = r"(?:Email|E-mail)\s*[:\-]?\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})"
    match = re.search(label_pattern, text, re.IGNORECASE)
    if match:
        return match.group(1)

    return ""

def extract_phone(text: str) -> str:
    """
    Extract the first valid phone number found in the text using multiple patterns.
    """
    if not text:
        return ""
    patterns = [
        r"(?:\+?\d{1,3}[\s\-\.]?)?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}",  # 123-456-7890
        r"\+?\d{1,3}[\s\-\.]?\d{10}",  # +91 9876543210 (International with separator)
        r"\+?\d{1,3}[\s\-\.]?\d{5}[\s\-\.]?\d{5}",  # +91 98765 43210 (Common split)
        r"\+?\d{1,3}[\s\-\.]?\d{4}[\s\-\.]?\d{6}",  # +91 9876 543210
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            return match.group(0).strip()
    return ""

def normalize_phone(phone_text: str) -> str:
    """
    Normalize phone number to format: +91 XXXXXXXXXX.
    Falls back to original text if standard formats aren't matched.
    """
    if not phone_text:
        return ""

    # Remove all non-numeric chars except +
    cleaned = re.sub(r'[^0-9+]', '', phone_text)

    # Case 1: 10 digit number (e.g. 9876543210) -> +91 9876543210
    if len(cleaned) == 10 and cleaned.isdigit():
        return f"+91 {cleaned}"

    # Case 2: 12 digits starting with 91 (e.g. 919876543210) -> +91 9876543210
    if len(cleaned) == 12 and cleaned.startswith("91") and cleaned.isdigit():
        return f"+91 {cleaned[2:]}"

    # Case 3: +91 prefix (e.g. +919876543210) -> +91 9876543210
    if cleaned.startswith("+91") and len(cleaned) == 13:
        return f"+91 {cleaned[3:]}"

    # Return original if doesn't match standard patterns
    return phone_text

def extract_name(text: str) -> str:
    """
    Attempt to extract the candidate's name from the header (first few lines)
    using heuristics and forbidden word lists.
    """
    if not text:
        return ""

    lines = text.strip().split("\n")

    for line in lines[:15]:
        line = line.strip()
        if not line or len(line) < 2 or len(line) > 60:
            continue

        if re.search(r"@|http|www\.|\.com|\.org|\.net", line, re.IGNORECASE):
            continue
        if re.search(r"\d{5,}", line):
            continue

        words = line.split()
        lower_words = {w.lower().rstrip(":.,") for w in words}
        if lower_words & _HEADER_SKIP:
            continue
        if lower_words & _TITLE_WORDS and len(lower_words & _TITLE_WORDS) >= len(words) // 2:
            continue

        clean_words = [w for w in words if re.match(r"^[A-Za-z.\-']+$", w)]
        if len(clean_words) >= 1 and len(clean_words) <= 4 and len(clean_words) == len(words):
            if any(w[0].isupper() for w in clean_words):
                name = " ".join(clean_words)
                if len(clean_words) == 1 and clean_words[0].lower() in _HEADER_SKIP | _TITLE_WORDS:
                    continue
                return name.title()

    return ""

def extract_contact_info(text: str) -> Dict[str, str]:
    """
    Extract name, email, and phone from text and return as a dictionary.
    """
    if not text:
        return {"name": "", "email": "", "phone": ""}
    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": normalize_phone(extract_phone(text)),
    }
