from core.prompts import XAI_PROMPT_TEMPLATE

def generate_xai_explanation(job_data, candidate):
    return f"""
This resume was shortlisted because:

• Matches key required skills: {', '.join(candidate['scores']['matched_skills'])}
• Candidate experience: {candidate['experience']} years (Required: {job_data['required_experience']})
• Strong overall relevance to the job description

Missing skills (if any):
• {', '.join(candidate['scores']['missing_skills']) or 'None'}

Final Score: {candidate['scores']['final_score']}
"""
