def compute_scores(semantic_score, resume_skills, resume_experience, job_data):
    must = set(job_data["must_have_skills"])
    good = set(job_data["good_to_have_skills"])

    matched_must = must.intersection(resume_skills)
    matched_good = good.intersection(resume_skills)

    skill_score = (
        len(matched_must) * 1.0 +
        len(matched_good) * 0.5
    ) / max(len(must), 1)

    experience_score = min(
        resume_experience / max(job_data["required_experience"], 1), 1.0
    )

    final_score = (
        0.5 * semantic_score +
        0.3 * skill_score +
        0.2 * experience_score
    )

    return {
        "semantic_score": round(semantic_score, 3),
        "skill_score": round(skill_score, 3),
        "experience_score": round(experience_score, 3),
        "final_score": round(final_score, 3),
        "matched_skills": list(matched_must | matched_good),
        "missing_skills": list(must - matched_must)
    }
