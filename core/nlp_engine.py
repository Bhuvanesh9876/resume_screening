"""
NLP Engine Module

This module handles Natural Language Processing tasks for the resume screening application.
It uses spaCy for Entity Recognition and RapidFuzz for fuzzy string matching to
identify skills, entities, and candidate names.
"""

import re
from typing import List, Set, Optional
import spacy
from spacy.language import Language
import streamlit as st
from rapidfuzz import process, fuzz
from core.embedding_engine import EmbeddingEngine

# Load NLP model once
@st.cache_resource
def load_nlp() -> Language:
    """Load the spaCy NLP model, downloading it if necessary."""
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        # Fallback if not downloaded
        from spacy.cli import download
        download("en_core_web_sm")
        return spacy.load("en_core_web_sm")

class NLPEngine:
    """
    Engine for performing NLP tasks extraction and validation.
    """

    STOP_WORDS = {
        "experience", "skills", "education", "project", "work", "role", "team", "company"
    }

    SKIP_TERMS = {
        "resume", "curriculum", "vitae", "cv", "profile", "summary", "contact",
        "details", "email", "phone", "address", "human", "resources", "recruitment",
        "experience", "education", "skills", "projects", "professional", "summary",
        "objective", "work", "history", "career", "job", "position", "role",
        "candidate", "application", "applicant", "cover", "letter"
    }

    TECH_TERMS = {
        "java", "python", "javascript", "typescript", "c++", "c#", "html", "css",
        "sql", "nosql", "react", "angular", "vue", "node", "aws", "azure",
        "docker", "kubernetes", "linux", "unix", "machine learning",
        "deep learning", "data science", "artificial intelligence", "ai", "ml",
        "dl", "nlp", "computer vision", "software engineer", "developer",
        "programmer", "analyst", "frontend", "backend", "fullstack", "devops",
        "cloud", "engineer", "architect", "manager", "product", "project",
        "scrum", "agile", "jira", "git", "github", "gitlab", "bitbucket",
        "testing", "selenium", "cypress", "jest", "pytest", "junit", "mocha",
        "pandas", "numpy", "tensorflow", "pytorch", "keras", "scikit-learn",
        "matplotlib", "seaborn", "tableau", "power bi", "excel", "word",
        "powerpoint", "outlook", "sharepoint", "salesforce", "sap", "oracle",
        "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "cassandra",
        "dynamodb", "sqlite", "mariadb", "spring", "spring boot", "django",
        "flask", "fastapi", "ruby", "rails", "php", "laravel", "swift",
        "kotlin", "android", "ios", "react native", "flutter", "xamarin",
        "ionic", "unity", "unreal", "game", "blockchain", "crypto",
        "smart contracts", "solidity", "web3", "cybersecurity", "network",
        "security", "penetration", "hacking", "encryption", "algorithms",
        "data structures"
    }

    def __init__(self):
        """Initialize the NLP engine with spaCy model and embedding engine."""
        self.nlp = load_nlp()
        self.embedder = EmbeddingEngine()

    def extract_entities(self, text: str) -> Set[str]:
        """
        Extract potential skills using NER and pattern matching.
        Focuses on ORG (Organizations/Companies/Frameworks), PRODUCT, and WORK_OF_ART.
        """
        doc = self.nlp(text)
        candidates = set()

        # 1. Named Entity Recognition
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT", "WORK_OF_ART", "GPE", "LANGUAGE"]:
                clean_ent = self._clean_term(ent.text)
                if self._is_valid_candidate(clean_ent):
                    candidates.add(clean_ent)

        # 2. Pattern Matching (Noun Phrases that look technical)
        # Look for terms like "AWS Lambda", "Google Cloud", "React Native"
        for chunk in doc.noun_chunks:
            clean_chunk = self._clean_term(chunk.text)
            if 2 <= len(clean_chunk.split()) <= 3 and self._is_valid_candidate(clean_chunk):
                candidates.add(clean_chunk)

        return candidates

    def _clean_term(self, term: str) -> str:
        """Clean a term by removing special characters."""
        return re.sub(r'[^a-zA-Z0-9\s\+\#\.]', '', term).strip()

    def _is_valid_candidate(self, term: str) -> bool:
        """Check if a term is a valid skill candidate."""
        if not term or len(term) < 2:
            return False
        if term.lower() in self.STOP_WORDS:
            return False
        if term.isdigit():  # skip years like '2020'
            return False
        return True

    def validate_skills(self, candidates: Set[str], known_skills: List[str]) -> List[str]:
        """
        Validate extracted candidates against a known skill database using fuzzy matching.
        This bridges the gap between 'extracted text' and 'actual skill'.
        """
        validated = set()

        # Optimize by set lookups first (case-insensitive)
        known_map = {k.lower(): k for k in known_skills}

        for cand in candidates:
            cand_lower = cand.lower()

            # Direct match
            if cand_lower in known_map:
                validated.add(known_map[cand_lower])
                continue

            # Fuzzy match (expensive, use sparingly or with limited threshold)
            # Only fuzzy match if it looks promising
            match = process.extractOne(cand_lower, list(known_map.keys()), scorer=fuzz.ratio)
            if match and match[1] >= 90:  # Very High confidence only to avoid false positives
                validated.add(known_map[match[0]])

        return list(validated)

    def extract_candidate_name_from_text(self, text: str) -> str:
        """
        Extract the candidate's name using Regex patterns and NER with strict heuristics.
        """
        if not text:
            return ""

        # 1. Regex Pattern: Look for "Name: ..." explicit labels
        name_match = re.search(
            r"(?:Name|Candidate Name)\s*[:\-]\s*([A-Za-z\s\.]+)",
            text[:1000],
            re.IGNORECASE
        )
        if name_match:
            candidate = name_match.group(1).strip()
            # Sanity check: 2-4 words, reasonable length
            if 3 <= len(candidate) <= 40 and 1 < len(candidate.split()) < 5:
                # Avoid capturing headers like "Name: Email:"
                if not any(char.isdigit() for char in candidate):
                    return candidate.title()

        # 2. Heuristic Scan of Top Lines (Title Case Filter)
        # Scan first 10 non-empty lines for identifying the name
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        header_lines = lines[:10]

        # Strategy A: Use SpaCy on the header text specifically
        header_text = "\n".join(header_lines)
        best_name = self._extract_name_with_ner(header_text)
        if best_name:
            return best_name

        # Strategy B: Fallback - First line that looks like a name
        return self._extract_name_fallback(header_lines)

    def _extract_name_with_ner(self, header_text: str) -> str:
        """Attempt to extract name using NER on the header text."""
        doc = self.nlp(header_text)

        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text.strip()

                # Filter 1: Length and Character check
                if len(name) < 3 or len(name) > 40:
                    continue
                if not re.match(r"^[a-zA-Z\s\.\-']+$", name):
                    continue

                # Filter 2: Common Keyword Check
                if any(w.lower() in self.SKIP_TERMS for w in name.split()):
                    continue

                # Filter 5: Technical Term Check (Deep check)
                if name.lower() in self.TECH_TERMS:
                    continue
                # Only skip if the *entire* name is composed of tech terms if strict
                # Let's be strict: if any part of the name is a known tech keyword
                if any(w.lower() in self.TECH_TERMS for w in name.split()):
                    continue

                # Filter 3: Must look like a name (Title Case usually)
                if not name[0].isupper():
                    continue

                # Filter 4: Emails often get caught as PERSON by mistake if model is weak
                if "@" in name or ".com" in name.lower():
                    continue

                # Filter 6: Minimum Word Count
                if len(name.split()) < 2:
                    continue

                # If we passed all filters, this is a strong candidate
                return name.title()
        return ""

    def _extract_name_fallback(self, header_lines: List[str]) -> str:
        """Fallback strategy: checks top lines for name-like patterns."""
        # If NER fails, trust the document structure. Name is usually top line.
        for line in header_lines[:3]:
            # Regex: Alphabetic, maybe spaces/dots, 3-30 chars
            if re.match(r"^[a-zA-Z\s\.\-']+$", line):
                # Must be Title Case or ALL CAPS
                if line.istitle() or line.isupper():
                    # Check forbidden terms again
                    if not any(w.lower() in self.SKIP_TERMS for w in line.split()):
                        # Length check: 2 to 4 words usually
                        if 2 <= len(line.split()) <= 4:
                            return line.title()
        return ""
