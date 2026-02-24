import hashlib
from typing import Dict, List, Tuple
import streamlit as st
from groq import Groq
from core.config import GROQ_API_KEY, LLM_MODEL

def generate_llama_rationale(job_data: dict, candidate: dict, base_report: str) -> str:
    """Uses Llama-3 to generate a sophisticated rationale for the candidate ranking."""
    api_key = GROQ_API_KEY or st.secrets.get("GROQ_API_KEY")
    if not api_key:
        return ""

    try:
        client = Groq(api_key=api_key)
        
        # Enhanced Prompt for better reasoning
        prompt = f"""
        Role: Expert Recruitment & Talent Acquisition Analyst.
        Action: Analyze candidate-to-job alignment.
        
        Job Title: {job_data.get('job_title', 'The Role')}
        Required Skills: {', '.join(job_data.get('must_have_skills', []))}
        
        Candidate Information:
        - Overall Match: {candidate.get('scores', {}).get('final_score', 0):.0%}
        - Key Matches: {', '.join(candidate.get('scores', {}).get('matched_skills', []))}
        - Key Gaps: {', '.join(candidate.get('scores', {}).get('missing_skills', []))}
        - Semantic Fit Score: {candidate.get('scores', {}).get('semantic_score', 0):.2f}
        
        Rule-Based Analysis:
        {base_report}
        
        Task: 
        Provide a sharp, professional 3-4 sentence rationale explaining WHY this candidate was scored this way. 
        Don't just repeat keywords; focus on the 'holistic' or 'semantic' fit. 
        If there's a strong semantic score but missing keywords, explain that the candidate shows potential domain alignment.
        Maintain a constructive, objective HR tone.
        """
        
        completion = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a senior recruitment consultant specializing in technical talent assessment."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4, # Lower temperature for consistency
            max_tokens=300
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        # Check for specific authentication or rate limit errors if needed
        return f"*(Llama reasoning currently unavailable: {str(e)})*"

def generate_text_based_xai(job_data: dict, candidate: dict) -> str:
    """
    Generates a professional markdown-formatted narrative report with extreme variety
    using a multi-part sentence assembly logic, enhanced by Llama-3 reasoning.
    """
    scores = candidate.get("scores", {})
    final_score = scores.get("final_score", 0)
    matched = scores.get("matched_skills", [])
    missing = scores.get("missing_skills", [])
    semantic_score = scores.get("semantic_score", 0)
    exp_score = scores.get("experience_score", 0)
    
    must_have = set(s.lower() for s in (job_data.get("must_have_skills", []) or []))
    good_to_have = set(s.lower() for s in (job_data.get("good_to_have_skills", []) or []))
    
    matched_must = [s for s in matched if s.lower() in must_have]
    matched_good = [s for s in matched if s.lower() in good_to_have]
    
    job_title = job_data.get("job_title", "the role")
    candidate_name = candidate.get("resume_name", "Candidate").replace(".pdf", "").replace("_", " ").title()
    
    # Stable seed for variety based on candidate name
    h = hashlib.md5(candidate_name.encode()).hexdigest()
    seed = int(h, 16)
    
    def get_variant(parts: List[str], offset: int) -> str:
        return parts[(seed + offset) % len(parts)]
    
    report = []
    
    # --- 1. Executive Summary ---
    report.append(f"### 📋 Executive Summary for {candidate_name}")
    
    # Part A: Heading/Tone
    if final_score >= 0.85:
        p1 = ["**Strongly Recommended**", "**Excellent Fit**", "**Top-Tier Candidate**", "**Exceptional Match**", "**Highly Qualified**"]
    elif final_score >= 0.65:
        p1 = ["**Recommended**", "**Solid Match**", "**Qualified Candidate**", "**Strong Contender**", "**Balanced Fit**"]
    else:
        p1 = ["**Review with Caution**", "**Partial Match**", "**Emerging Fit**", "**Limited Alignment**", "**Requires Scrutiny**"]
        
    # Part B: Core Logic
    if final_score >= 0.85:
        p2 = [f"surpasses the {job_title} benchmark with ease,", f"demonstrates a near-perfect alignment with the {job_title} profile,", f"is an outstanding prospect for this {job_title} opening,", f"exhibits a high level of mastery requested for the {job_title},", f"presents a compelling case for immediate interview for the {job_title},"]
    elif final_score >= 0.65:
        p2 = [f"is a dependable match for the {job_title} position,", f"covers the core requirements of the {job_title} effectively,", f"aligns well with the majority of {job_title} expectations,", f"shows professional competence for the {job_title} scope,", f"is a well-rounded candidate for the {job_title} requirements,"]
    else:
        p2 = [f"shows some relevant background for the {job_title} but has gaps,", f"has a profile that only partially maps to the {job_title} needs,", f"meets a subset of the {job_title} criteria but misses key areas,", f"displays foundational skills but lacks depth in the {job_title} stack,", f"would require significant ramp-up time for the {job_title} role,"]

    # Part C: Skill/Metric Highlight
    must_count = len(matched_must)
    total_must = len(must_have)
    must_str = f"{must_count}/{total_must} must-have skills" if total_must > 0 else "core skills"
    
    p3 = [f"specifically matching {must_str},", f"backed by a verified {must_str} alignment,", f"with a clear track record in {must_str},", f"demonstrating proficiency in {must_str},", f"evidenced by the presence of {must_str} in the profile,"]
    
    # Part D: Closing Context
    p4 = ["and high semantic profile relevance.", "combined with a strong professional narrative.", "supported by relevant industry experience.", "and a highly relevant technical pedigree.", "with a solid thematic match to the job description."]

    summary = f"{get_variant(p1, 0)} ({final_score:.0%}). {candidate_name} {get_variant(p2, 1)} {get_variant(p3, 2)} {get_variant(p4, 3)}"
    report.append(summary)
    
    # --- 2. Llama-Powered Rationale ---
    llama_rationale = generate_llama_rationale(job_data, candidate, summary)
    if llama_rationale:
        report.append("")
        report.append("### 🧠 Llama-3 Intelligent Rationale")
        report.append(llama_rationale)
    
    report.append("")
    
    # --- 3. Key Strengths ---
    report.append("### 💪 Key Strengths")
    
    # Strength A: Semantic/Profile
    sem_p = ["- **High Profile Relevance**: Career history closely matches the job domain.", "- **Domain Expertise**: Previous roles show a deep thematic overlap with this role.", "- **Industry Alignment**: Profile narrative is perfectly synced with the job's context."]
    if semantic_score > 0.75:
        report.append(get_variant(sem_p, 4))
        
    # Strength B: Skills
    skill_p = [f"- **Strong Skill Layer**: Matched {len(matched)} diverse technologies including **{', '.join(matched[:2])}**.", f"- **Technical Robustness**: Possesses **{len(matched)}** keys skills, specifically excelling in **{', '.join(matched[:2])}**.", f"- **Core Proficiency**: Shows verifiable experience in **{', '.join(matched[:2])}** and {len(matched)-2} others."]
    if len(matched) > 3:
        report.append(get_variant(skill_p, 5))
        
    # Strength C: Experience
    years = candidate.get("experience", 0)
    exp_p = [f"- **Industry Tenure**: {years} years of pure professional/internship experience.", f"- **Professional Maturity**: A consistent {years}-year track record in relevant domains.", f"- **Verified Experience**: {years} years of work history that aligns with the required seniority."]
    if exp_score > 0.7:
        report.append(get_variant(exp_p, 6))

    if len(report) <= 4: # Only Header + ExSum + Weakness Header
        report.append("- **General Background**: Meets broader industry standards for professional readiness.")
    report.append("")

    # --- 4. Gaps & Review ---
    if missing:
        report.append("### ⚠️ Areas for Review")
        gap_intro = ["Critically missing the following essential skills:", "Verification required for the absence of:", "Gaps found in these primary requirements:"]
        report.append(f"{get_variant(gap_intro, 7)} **{', '.join(missing[:4])}**.")
        report.append("")

    # --- 5. Interview Strategy ---
    report.append("### 💬 Interview Strategy")
    report.append("Suggested questions to validate candidate fit:")
    
    # Q1: Hard Skill (Matched)
    if matched:
        q1_p = [f"1. *Expertise Check*: 'Can you describe a complex project where **{matched[0]}** was the primary tool?'", f"1. *Technical Depth*: 'What are the biggest challenges you faced when scaling applications using **{matched[0]}**?'", f"1. *Best Practices*: 'How do you ensure code quality and maintainability when working with **{matched[0]}**?'"]
        report.append(get_variant(q1_p, 8))
        
    # Q2: Gap Fill (Missing)
    if missing:
        q2_p = [f"2. *Adaptability*: 'We use **{missing[0]}** extensively. How would you bridge your current knowledge to master this?'", f"2. *Tool Mapping*: 'Is there an alternative or similar tool to **{missing[0]}** that you have mastered?'", f"2. *Learning Agility*: 'How quickly can you ramp up on **{missing[0]}** given your background in related stacks?'"]
        report.append(get_variant(q2_p, 9))
    
    # Q3: Role ACHIEVEMENT
    q3_p = [f"3. *Role Focus*: 'Describe your most significant professional achievement relevant to a {job_title} role.'", f"3. *Impact Assessment*: 'How do you measure success in a position like {job_title}?'", f"3. *Collaboration*: 'Walk us through a time you led a {job_title}-focused initiative under tight deadlines.'"]
    report.append(get_variant(q3_p, 10))
    
    return "\n".join(report)
