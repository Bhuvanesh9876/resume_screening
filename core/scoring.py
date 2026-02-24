"""
Scoring Module

This module calculates various scores (semantic, skill, experience) for candidate
resumes against job descriptions. It aggregates these into a final score
and provides a confidence metric.
"""

from typing import List, Dict, Set, Optional, Any
import numpy as np
from core.config import SEMANTIC_WEIGHT, SKILL_WEIGHT, EXPERIENCE_WEIGHT

def _normalize_set(items: Optional[List[str]]) -> Set[str]:
    """Normalize a list of strings into a set of lowercase strings."""
    if items is None:
        return set()
    return {s.strip().lower() for s in items if s and s.strip()}

def _find_original(matched_lower: Set[str], original_list: List[str]) -> List[str]:
    """Recover original case formatting for matched lowercase strings."""
    if not matched_lower or not original_list:
        return []
    return [s for s in original_list if s and s.strip().lower() in matched_lower]

def _clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp a value between a minimum and maximum."""
    return max(min_val, min(max_val, float(value)))

def _compute_confidence(resume_text_len: int, skills_found: int,
                        has_experience: bool) -> float:
    """
    Compute a confidence score for the parsing quality based on
    text length, skills found, and experience detection.
    """
    confidence = 0.0

    if resume_text_len >= 1000:
        confidence += 0.4
    elif resume_text_len >= 500:
        confidence += 0.3
    elif resume_text_len >= 200:
        confidence += 0.2
    else:
        confidence += 0.1

    if skills_found >= 5:
        confidence += 0.35
    elif skills_found >= 3:
        confidence += 0.25
    elif skills_found >= 1:
        confidence += 0.15
    else:
        confidence += 0.05

    if has_experience:
        confidence += 0.25
    else:
        confidence += 0.1

    return _clamp(confidence)

def compute_semantic_score(resume_embedding: Any, job_embedding: Any) -> float:
    """
    Calculate cosine similarity between resume and job embeddings.
    """
    if resume_embedding is None or job_embedding is None:
        return 0.0

    try:
        resume_vec = np.array(resume_embedding, dtype=np.float32)
        job_vec = np.array(job_embedding, dtype=np.float32)

        if resume_vec.size == 0 or job_vec.size == 0:
            return 0.0

        if resume_vec.shape != job_vec.shape:
            return 0.0

        resume_norm = np.linalg.norm(resume_vec)
        job_norm = np.linalg.norm(job_vec)

        if resume_norm == 0 or job_norm == 0:
            return 0.0

        resume_vec = resume_vec / resume_norm
        job_vec = job_vec / job_norm

        similarity = float(np.dot(resume_vec, job_vec))

        return _clamp(similarity, 0.0, 1.0)

    except (ValueError, TypeError):
        return 0.0

def compute_skill_score(resume_skills: List[str], required_skills: List[str]) -> Dict[str, Any]:
    """
    Compute a simple skill match score (Jaccard-like index).
    Note: 'compute_scores' uses a weighted approach; this is a simpler utility.
    """
    resume_lower = _normalize_set(resume_skills)
    required_lower = _normalize_set(required_skills)

    if not required_lower:
        return {
            "skill_score": 1.0 if resume_lower else 0.5,
            "matched_skills": list(resume_lower),
            "missing_skills": []
        }

    matched_lower = required_lower & resume_lower
    missing_lower = required_lower - matched_lower

    skill_score = len(matched_lower) / len(required_lower)

    return {
        "skill_score": _clamp(skill_score),
        "matched_skills": sorted(list(matched_lower)),
        "missing_skills": sorted(list(missing_lower))
    }

def compute_experience_score(candidate_experience: float,
                             required_experience: float) -> float:
    """
    Calculate score based on years of experience vs required.
    Score is 1.0 if candidate meets requirement, otherwise a ratio.
    """
    candidate_exp = max(0.0, float(candidate_experience) if candidate_experience else 0.0)
    required_exp = max(0.0, float(required_experience) if required_experience else 0.0)

    # If no experience required, give full points if candidate has any checks out, else 0.5
    if required_exp <= 0:
        return 1.0 if candidate_exp > 0 else 0.5

    # Simple ratio, capped at 1.0 by _clamp later
    score = candidate_exp / required_exp
    return _clamp(score)

def compute_scores(semantic_score: float, resume_skills: List[str],
                   resume_experience: float, job_data: Dict[str, Any],
                   resume_text_len: int = 0) -> Dict[str, Any]:
    """
    Aggregates all scores into a final weighted score.
    Considers semantic similarity, weighted skill matching, and experience.

    Args:
        semantic_score: Pre-computed semantic similarity.
        resume_skills: List of skills found in the resume.
        resume_experience: Years of experience extracted from resume.
        job_data: Dictionary containing job requirements (must/good skills, experience).
        resume_text_len: Length of resume text for confidence calculation.

    Returns:
        Dictionary containing breakdown of scores and final result.
    """
    semantic_score = _clamp(float(semantic_score) if semantic_score is not None else 0.0)

    must_original = list(job_data.get("must_have_skills", []) or [])
    good_original = list(job_data.get("good_to_have_skills", []) or [])
    req_exp = float(job_data.get("required_experience", 0) or 0)

    must_lower = _normalize_set(must_original)
    good_lower = _normalize_set(good_original)
    resume_lower = _normalize_set(resume_skills)

    matched_must_lower = must_lower & resume_lower
    matched_good_lower = good_lower & resume_lower
    missing_must_lower = must_lower - matched_must_lower

    matched_skills = _find_original(matched_must_lower | matched_good_lower,
                                     must_original + good_original)
    missing_skills = _find_original(missing_must_lower, must_original)

    # Weighted Skill Scoring: Must Have = 2x, Good to Have = 1x
    total_weight = len(must_lower) * 2.0 + len(good_lower) * 1.0
    if total_weight > 0:
        skill_score = (
            len(matched_must_lower) * 2.0 + len(matched_good_lower) * 1.0
        ) / total_weight
    else:
        skill_score = 0.5

    skill_score = _clamp(skill_score)

    experience_score = compute_experience_score(resume_experience, req_exp)

    # Penalty for missing essential skills
    if must_lower:
        missing_ratio = len(missing_must_lower) / len(must_lower)
        penalty = 0.25 * missing_ratio
    else:
        penalty = 0.0

    base_score = (
        SEMANTIC_WEIGHT * semantic_score +
        SKILL_WEIGHT * skill_score +
        EXPERIENCE_WEIGHT * experience_score
    )

    final_score = base_score - penalty

    final_score = _clamp(final_score)

    confidence = _compute_confidence(
        resume_text_len=resume_text_len,
        skills_found=len(resume_skills) if resume_skills else 0,
        has_experience=resume_experience is not None and resume_experience >= 0
    )

    return {
        "semantic_score": round(semantic_score, 3),
        "skill_score": round(skill_score, 3),
        "experience_score": round(experience_score, 3),
        "final_score": round(final_score, 3),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "confidence": round(confidence, 2),
        "score_breakdown": {
            "semantic_contribution": round(SEMANTIC_WEIGHT * semantic_score, 3),
            "skill_contribution": round(SKILL_WEIGHT * skill_score, 3),
            "experience_contribution": round(EXPERIENCE_WEIGHT * experience_score, 3),
            "penalty_applied": round(penalty, 3)
        }
    }
