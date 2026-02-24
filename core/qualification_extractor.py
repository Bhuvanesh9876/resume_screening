"""
Qualification Extractor Module

Extracts educational qualifications and degrees from resume text.
"""

import re
from typing import List, Dict, Optional, Any

# Common degree patterns
DEGREE_PATTERNS = [
    # Doctoral degrees
    r'\b(Ph\.?D\.?|Doctor of Philosophy|Doctorate|D\.Phil\.?)\b',
    r'\b(Ed\.?D\.?|Doctor of Education)\b',
    r'\b(M\.?D\.?|Doctor of Medicine)\b',
    r'\b(J\.?D\.?|Juris Doctor)\b',
    r'\b(D\.?B\.?A\.?|Doctor of Business Administration)\b',

    # Master's degrees
    r'\b(M\.?S\.?|Master of Science|Masters? of Science|M\.?Sc\.?)\b',
    r'\b(M\.?A\.?|Master of Arts|Masters? of Arts)\b',
    r'\b(M\.?B\.?A\.?|Master of Business Administration)\b',
    r'\b(M\.?E\.?|M\.?Eng\.?|Master of Engineering|Masters? of Engineering)\b',
    r'\b(M\.?Tech\.?|Master of Technology)\b',
    r'\b(M\.?C\.?A\.?|Master of Computer Applications)\b',
    r'\b(M\.?Com\.?|Master of Commerce)\b',
    r'\b(M\.?Ed\.?|Master of Education)\b',
    r'\b(M\.?Phil\.?|Master of Philosophy)\b',
    r'\b(M\.?F\.?A\.?|Master of Fine Arts)\b',
    r'\b(L\.?L\.?M\.?|Master of Laws)\b',
    r'\b(M\.?P\.?H\.?|Master of Public Health)\b',
    r'\b(M\.?P\.?A\.?|Master of Public Administration)\b',

    # Bachelor's degrees
    r'\b(B\.?S\.?|Bachelor of Science|Bachelors? of Science|B\.?Sc\.?)\b',
    r'\b(B\.?A\.?|Bachelor of Arts|Bachelors? of Arts)\b',
    r'\b(B\.?E\.?|B\.?Eng\.?|Bachelor of Engineering|Bachelors? of Engineering)\b',
    r'\b(B\.?Tech\.?|Bachelor of Technology)\b',
    r'\b(B\.?B\.?A\.?|Bachelor of Business Administration)\b',
    r'\b(B\.?C\.?A\.?|Bachelor of Computer Applications)\b',
    r'\b(B\.?Com\.?|Bachelor of Commerce)\b',
    r'\b(B\.?Ed\.?|Bachelor of Education)\b',
    r'\b(B\.?F\.?A\.?|Bachelor of Fine Arts)\b',
    r'\b(L\.?L\.?B\.?|Bachelor of Laws)\b',
    r'\b(B\.?Arch\.?|Bachelor of Architecture)\b',
    r'\b(B\.?Pharm\.?|Bachelor of Pharmacy)\b',

    # Associate degrees
    r'\b(A\.?S\.?|Associate of Science|A\.?S\.?c\.?)\b',
    r'\b(A\.?A\.?|Associate of Arts)\b',
    r'\b(A\.?A\.?S\.?|Associate of Applied Science)\b',

    # Diploma and Certificate
    r'\b(Diploma|Post[- ]?Graduate Diploma|PG Diploma|PGDM|PGDCA)\b',
    r'\b(Certificate|Professional Certificate|Certification)\b',
]

# Fields of study
FIELDS_OF_STUDY = [
    "Computer Science", "Information Technology", "IT", "Software Engineering",
    "Computer Engineering", "Data Science", "Artificial Intelligence", "AI",
    "Machine Learning", "Cybersecurity", "Information Systems",
    "Electrical Engineering", "Electronics", "Mechanical Engineering",
    "Civil Engineering", "Chemical Engineering", "Aerospace Engineering",
    "Biomedical Engineering", "Industrial Engineering",
    "Business Administration", "Business Management", "Finance", "Accounting",
    "Economics", "Marketing", "Human Resources", "HR", "Operations Management",
    "Mathematics", "Statistics", "Physics", "Chemistry", "Biology",
    "Psychology", "Sociology", "Political Science", "History", "English",
    "Communications", "Journalism", "Public Relations",
    "Graphic Design", "Fine Arts", "Architecture", "Music",
    "Medicine", "Nursing", "Pharmacy", "Public Health",
    "Law", "Education", "Library Science",
]

# Educational institutions indicators
INSTITUTION_INDICATORS = [
    r'\b(University|College|Institute|School|Academy)\b',
    r'\b(IIT|IIM|NIT|BITS|MIT|Stanford|Harvard|Oxford|Cambridge)\b',
]

# Degree level hierarchy
DEGREE_LEVELS = {
    'doctorate': [
        'Ph.D', 'PhD', 'Doctor', 'Doctorate', 'Ed.D', 'M.D', 'J.D', 'D.B.A'
    ],
    'masters': [
        'M.S', 'MS', 'M.A', 'MA', 'MBA', 'M.E', 'M.Eng', 'M.Tech',
        'MCA', 'M.Com', 'M.Ed', 'M.Phil', 'MFA', 'LLM', 'MPH', 'MPA'
    ],
    'bachelors': [
        'B.S', 'BS', 'B.A', 'BA', 'B.E', 'B.Eng', 'B.Tech', 'BBA',
        'BCA', 'B.Com', 'B.Ed', 'BFA', 'LLB', 'B.Arch', 'B.Pharm'
    ],
    'associate': ['A.S', 'AS', 'A.A', 'AA', 'AAS'],
    'diploma': ['Diploma', 'PG Diploma', 'PGDM', 'PGDCA'],
    'certificate': ['Certificate', 'Certification'],
}


def extract_qualifications(resume_text: str) -> Dict[str, Any]:
    """
    Extract educational qualifications from resume text.

    Args:
        resume_text: Raw text from resume

    Returns:
        Dictionary containing:
        - degrees: List of extracted degrees
        - fields: List of fields of study
        - institutions: List of educational institutions
        - highest_degree: The highest degree level found
        - qualification_text: Combined qualification string
    """
    if not resume_text:
        return {
            "degrees": [],
            "fields": [],
            "institutions": [],
            "highest_degree": None,
            "qualification_text": ""
        }

    text_original = resume_text

    # Extract degrees
    degrees = []
    for pattern in DEGREE_PATTERNS:
        matches = re.findall(pattern, text_original, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]
            cleaned = match.strip()
            if cleaned and cleaned not in degrees:
                degrees.append(cleaned)

    # Extract fields of study
    fields = []
    for field in FIELDS_OF_STUDY:
        if re.search(r'\b' + re.escape(field) + r'\b', text_original, re.IGNORECASE):
            if field not in fields:
                fields.append(field)

    # Extract institutions (look for lines containing university/college keywords)
    institutions = []
    lines = text_original.split('\n')
    for line in lines:
        for pattern in INSTITUTION_INDICATORS:
            if re.search(pattern, line, re.IGNORECASE):
                # Clean the line and add as institution
                cleaned_line = line.strip()
                if 5 < len(cleaned_line) < 200:
                    # Try to extract just the institution name
                    if cleaned_line not in institutions:
                        institutions.append(cleaned_line)
                break

    # Determine highest degree
    highest_degree = None
    highest_level = None
    level_order = [
        'doctorate', 'masters', 'bachelors', 'associate', 'diploma', 'certificate'
    ]

    for degree in degrees:
        degree_upper = degree.upper()
        for level in level_order:
            for degree_keyword in DEGREE_LEVELS[level]:
                if degree_keyword.upper() in degree_upper:
                    if (highest_level is None or
                            level_order.index(level) < level_order.index(highest_level)):
                        highest_level = level
                        highest_degree = degree
                    break

    # Build qualification text
    qualification_parts = []
    if highest_degree:
        qualification_parts.append(highest_degree)
    if fields:
        qualification_parts.append(f"in {fields[0]}")

    qualification_text = " ".join(qualification_parts) if qualification_parts else ""

    return {
        "degrees": degrees[:5],  # Limit to top 5
        "fields": fields[:5],  # Limit to top 5
        "institutions": institutions[:3],  # Limit to top 3
        "highest_degree": highest_degree,
        "highest_level": highest_level,
        "qualification_text": qualification_text
    }


def match_qualification(candidate_quals: Dict[str, Any],
                       required_qualification: str) -> Dict[str, Any]:
    """
    Match candidate qualifications against required qualification.

    Args:
        candidate_quals: Dictionary from extract_qualifications()
        required_qualification: Required qualification string from job

    Returns:
        Dictionary with match score and details
    """
    if not required_qualification or not candidate_quals:
        return {
            "match_score": 0.5,  # Neutral if no requirement
            "matched": False,
            "details": "No specific qualification requirement"
        }

    required_upper = required_qualification.upper()

    # Check for degree level match
    required_level = None
    level_order = [
        'doctorate', 'masters', 'bachelors', 'associate', 'diploma', 'certificate'
    ]

    for level in level_order:
        for keyword in DEGREE_LEVELS[level]:
            if keyword.upper() in required_upper:
                required_level = level
                break
        if required_level:
            break

    candidate_level = candidate_quals.get("highest_level")

    match_score = 0.5
    matched = False
    details = "Could not determine qualification match"

    # Calculate match score
    if required_level and candidate_level:
        required_idx = level_order.index(required_level)
        candidate_idx = level_order.index(candidate_level)

        if candidate_idx <= required_idx:
            # Candidate meets or exceeds requirement
            match_score = 1.0
            matched = True
            details = f"Qualification met: {candidate_quals.get('highest_degree', 'N/A')}"
        elif candidate_idx == required_idx + 1:
            # One level below
            match_score = 0.7
            matched = False
            details = (f"Slightly below requirement: Has {candidate_level}, "
                       f"needs {required_level}")
        else:
            # More than one level below
            match_score = 0.4
            matched = False
            details = f"Below requirement: Has {candidate_level}, needs {required_level}"
    else:
        # Check for field match if no level comparison possible
        field_match = False
        for field in candidate_quals.get("fields", []):
            if field.upper() in required_upper:
                field_match = True
                break

        if field_match:
            match_score = 0.8
            matched = True
            details = "Field of study matches requirement"

    return {
        "match_score": match_score,
        "matched": matched,
        "details": details,
        "candidate_qualification": candidate_quals.get("qualification_text", ""),
        "required_qualification": required_qualification
    }


def format_qualification_display(quals: Dict[str, Any]) -> str:
    """
    Format qualifications for display.

    Args:
        quals: Dictionary from extract_qualifications()

    Returns:
        Formatted string for display
    """
    parts = []

    if quals.get("degrees"):
        parts.append(f"Degrees: {', '.join(quals['degrees'])}")

    if quals.get("fields"):
        parts.append(f"Fields: {', '.join(quals['fields'])}")

    if quals.get("institutions"):
        parts.append(f"Institutions: {', '.join(quals['institutions'][:2])}")

    return " | ".join(parts) if parts else "No qualifications extracted"
