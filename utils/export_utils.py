"""
Export utilities for resume screening results
Allows exporting to CSV, PDF reports, and JSON formats
"""

import pandas as pd
import json
from datetime import datetime
import io
from typing import List, Dict


def export_to_csv(shortlisted_candidates: List[Dict], job_data: Dict) -> str:
    """
    Export shortlisted candidates to CSV format
    
    Returns:
        CSV content as string
    """
    data = []
    for idx, candidate in enumerate(shortlisted_candidates, 1):
        scores = candidate.get("scores", {})
        row = {
            "Rank": idx,
            "Candidate_Name": candidate.get("resume_name", f"Candidate_{idx}"),
            "Email": candidate.get("email", ""),
            # Force Excel to treat phone as string to avoid scientific notation (e.g. 9.12E+10)
            "Phone_Contact": f'="{candidate.get("phone")}"' if candidate.get("phone") else "",
            "Final_Score": scores.get("final_score", 0),
            "Semantic_Score": scores.get("semantic_score", 0),
            "Skill_Score": scores.get("skill_score", 0),
            "Experience_Score": scores.get("experience_score", 0),
            "Experience_Years": candidate.get("experience", 0),
            "Matched_Skills": ", ".join(scores.get("matched_skills", [])),
            "Missing_Skills": ", ".join(scores.get("missing_skills", [])),
            "Matched_Skills_Count": len(scores.get("matched_skills", [])),
            "Missing_Skills_Count": len(scores.get("missing_skills", [])),
            "Confidence": scores.get("confidence", 0),
            "Job_Title": job_data.get("job_title", ""),
            "Screening_Date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        data.append(row)
    
    if not data:
        # Return empty dataframe with correct columns
        columns = ["Rank", "Candidate_Name", "Email", "Phone_Contact", "Final_Score", "Semantic_Score", 
                   "Skill_Score", "Experience_Score", "Experience_Years", "Matched_Skills", "Missing_Skills", 
                   "Matched_Skills_Count", "Missing_Skills_Count", "Confidence", "Job_Title", "Screening_Date"]
        df = pd.DataFrame(columns=columns)
    else:
        df = pd.DataFrame(data)
    
    return df.to_csv(index=False)


def export_to_json(shortlisted_candidates: List[Dict], job_data: Dict, include_resume_text: bool = False) -> str:
    """
    Export screening results to JSON format
    
    Args:
        shortlisted_candidates: List of candidate dictionaries
        job_data: Job requirements dictionary
        include_resume_text: Whether to include full resume text
        
    Returns:
        JSON string
    """
    export_data = {
        "metadata": {
            "job_title": job_data.get("job_title", ""),
            "required_experience": job_data.get("required_experience", 0),
            "must_have_skills": job_data.get("must_have_skills", []),
            "good_to_have_skills": job_data.get("good_to_have_skills", []),
            "screening_date": datetime.now().isoformat(),
            "total_shortlisted": len(shortlisted_candidates)
        },
        "candidates": []
    }
    
    for idx, candidate in enumerate(shortlisted_candidates, 1):
        candidate_data = {
            "rank": idx,
            "resume_name": candidate.get("resume_name", ""),
            "experience": candidate.get("experience", 0),
            "skills": candidate.get("skills", []),
            "scores": candidate.get("scores", {})
        }
        
        if include_resume_text:
            candidate_data["resume_text"] = candidate.get("resume_text", "")
        
        export_data["candidates"].append(candidate_data)
    
    return json.dumps(export_data, indent=2)


def generate_summary_report(shortlisted_candidates: List[Dict], job_data: Dict) -> str:
    """
    Generate a text summary report
    
    Returns:
        Formatted text report
    """
    report = []
    report.append("=" * 80)
    report.append("RESUME SCREENING REPORT")
    report.append("=" * 80)
    report.append("")
    report.append(f"Job Title: {job_data.get('job_title', 'N/A')}")
    report.append(f"Required Experience: {job_data.get('required_experience', 0)} years")
    report.append(f"Screening Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Total Shortlisted: {len(shortlisted_candidates)}")
    report.append("")
    
    report.append("REQUIRED SKILLS:")
    report.append(f"  Required Skills: {', '.join(job_data.get('must_have_skills', []))}")
    report.append(f"  Preferred Qualifications: {', '.join(job_data.get('good_to_have_skills', []))}")
    report.append("")
    report.append("=" * 80)
    report.append("")
    
    for idx, candidate in enumerate(shortlisted_candidates, 1):
        scores = candidate.get("scores", {})
        report.append(f"RANK #{idx}: {candidate.get('resume_name', 'Unknown')}")
        report.append("-" * 80)
        report.append(f"  Overall Match Score: {scores.get('final_score', 0):.1%}")
        report.append(f"  Profile Alignment:   {scores.get('semantic_score', 0):.1%}")
        report.append(f"  Skills Match:        {scores.get('skill_score', 0):.1%}")
        report.append(f"  Experience Match:    {scores.get('experience_score', 0):.1%}")
        report.append(f"  Years of Experience: {candidate.get('experience', 0)}")
        report.append(f"  Data Confidence:     {scores.get('confidence', 0):.1%}")
        report.append("")
        
        matched = scores.get("matched_skills", [])
        if matched:
            report.append(f"  ✅ Matched Skills ({len(matched)}): {', '.join(matched)}")
        
        missing = scores.get("missing_skills", [])
        if missing:
            report.append(f"  ❌ Missing Skills ({len(missing)}): {', '.join(missing)}")
        
        report.append("")
        
        # Recommendation
        final_score = scores.get('final_score', 0)
        if final_score >= 0.85:
            recommendation = "🏆 PRIORITY - Schedule interview immediately"
        elif final_score >= 0.75:
            recommendation = "⭐ STRONG - Recommend interview"
        elif final_score >= 0.65:
            recommendation = "✓ GOOD - Consider for interview"
        else:
            recommendation = "◐ MODERATE - Review carefully"
        
        report.append(f"  Recommendation: {recommendation}")
        report.append("")
        report.append("")
    
    report.append("=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)
    
    return "\n".join(report)


def export_for_email(shortlisted_candidates: List[Dict], job_data: Dict) -> str:
    """
    Generate email-friendly HTML summary
    
    Returns:
        HTML string suitable for email
    """
    html = []
    html.append("<html><body style='font-family: Arial, sans-serif;'>")
    html.append(f"<h2>Resume Screening Results: {job_data.get('job_title', 'Position')}</h2>")
    html.append(f"<p><strong>Screening Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>")
    html.append(f"<p><strong>Total Shortlisted:</strong> {len(shortlisted_candidates)}</p>")
    html.append("<hr>")
    
    for idx, candidate in enumerate(shortlisted_candidates, 1):
        scores = candidate.get("scores", {})
        final_score = scores.get('final_score', 0)
        
        if final_score >= 0.85:
            color = "#22c55e"
            icon = "🏆"
        elif final_score >= 0.75:
            color = "#3b82f6"
            icon = "⭐"
        elif final_score >= 0.65:
            color = "#60a5fa"
            icon = "✓"
        else:
            color = "#fbbf24"
            icon = "◐"
        
        html.append(f"<div style='border-left: 4px solid {color}; padding-left: 16px; margin-bottom: 24px;'>")
        html.append(f"<h3 style='color: {color};'>{icon} #{idx}: {candidate.get('resume_name', 'Unknown')}</h3>")
        html.append(f"<p><strong>Match Score:</strong> {final_score:.0%}</p>")
        html.append(f"<p><strong>Experience:</strong> {candidate.get('experience', 0)} years</p>")
        
        matched = scores.get("matched_skills", [])
        if matched:
            html.append(f"<p><strong>Matched Skills:</strong> {', '.join(matched[:10])}</p>")
        
        missing = scores.get("missing_skills", [])
        if missing:
            html.append(f"<p style='color: #f97316;'><strong>Skill Gaps:</strong> {', '.join(missing[:5])}</p>")
        
        html.append("</div>")
    
    html.append("<hr>")
    html.append("<p><em>Generated by AI Resume Screening System</em></p>")
    html.append("</body></html>")
    
    return "\n".join(html)


def create_comparison_dataframe(shortlisted_candidates: List[Dict]) -> pd.DataFrame:
    """
    Create a pandas DataFrame for easy comparison and export
    
    Returns:
        DataFrame with candidate comparison
    """
    data = []
    for idx, candidate in enumerate(shortlisted_candidates, 1):
        scores = candidate.get("scores", {})
        data.append({
            "Rank": idx,
            "Name": candidate.get("resume_name", f"Candidate {idx}"),
            "Overall_Score": scores.get("final_score", 0),
            "Profile_Match": scores.get("semantic_score", 0),
            "Skills_Match": scores.get("skill_score", 0),
            "Experience_Match": scores.get("experience_score", 0),
            "Years_Experience": candidate.get("experience", 0),
            "Skills_Matched": len(scores.get("matched_skills", [])),
            "Skills_Missing": len(scores.get("missing_skills", [])),
            "Confidence": scores.get("confidence", 0)
        })
    
    return pd.DataFrame(data)
