import streamlit as st
from groq import Groq
from core.config import GROQ_API_KEY, LLM_MODEL

@st.cache_data(show_spinner="Generating Executive Audit...", ttl=3600)
def generate_llama_rationale(job_title: str, scores: dict, projects: list, experience: float) -> str:
    """Uses LLM to generate an 'Executive Audit' for senior recruiters."""
    api_key = GROQ_API_KEY or st.secrets.get("GROQ_API_KEY")
    if not api_key:
        return ""

    try:
        client = Groq(api_key=api_key)
        
        matched_skills = scores.get('matched_skills', [])
        missing_skills = scores.get('missing_skills', [])
        
        prompt = rf"""
        System: Senior Recruitment Auditor.
        Tone: Analytical, professional, evidence-based. No emojis.
        
        Context:
        - Job Title: {job_title}
        - Score: {scores.get('final_score', 0):.2%}
        - Experience: {experience} years
        - Matches: {', '.join(matched_skills[:5])}
        - Gaps: {', '.join(missing_skills[:3])}
        
        Task: Provide a highly concise, punchy 2-3 sentence explanation of why this candidate received this specific score.
        Highlight their strongest relevant match and point out the biggest gap preventing a perfect score.
        
        Rules:
        - Keep it under 50 words.
        - Be direct and objective.
        - No fluff or generic praise.
        """
        
        completion = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a terminal-level recruitment executive. Provide sharp, analytical audit reports."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.15,
            max_tokens=300
        )
        return completion.choices[0].message.content.strip()
    except Exception:
        return "*Audit analysis temporarily unavailable.*"

def generate_text_based_xai(job_data: dict, candidate: dict) -> str:
    """
    Generates a premium, high-density professional audit scorecard.
    """
    scores = candidate.get("scores", {})
    final_score = scores.get("final_score", 0)
    matched = scores.get("matched_skills", [])
    missing = scores.get("missing_skills", [])
    semantic_score = scores.get("semantic_score", 0)
    exp_score = scores.get("experience_score", 0)
    skill_score = scores.get("skill_score", 0)
    
    must_have = set(s.lower() for s in (job_data.get("must_have_skills", []) or []))
    matched_must = [s for s in matched if s.lower() in must_have]
    
    report = []
    
    # 1. Auditor Findings (Llama-3 concise rationale)
    audit_findings = generate_llama_rationale(
        job_title=job_data.get('job_title', 'The Role'),
        scores=scores,
        projects=candidate.get('projects', []),
        experience=candidate.get('experience', 0)
    )
    
    if audit_findings:
        report.append(f"**Rationale:** {audit_findings}\n")

    # 2. Key Matching and Missing Items
    if matched:
        report.append(f"✅ **Matched Requirements:** {', '.join(matched)}")
        
    if missing:
        report.append(f"❌ **Missing Requirements:** {', '.join(missing)}")
    elif not missing and matched:
        report.append(f"⭐️ **Missing Requirements:** None! Candidate possesses all required skills.")

    return "\n".join(report)
