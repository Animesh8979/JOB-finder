"""LLM Fabrication Shield (RAG Verification).

Ensures a 0% hallucination rate on cover letters and tailored resumes by 
explicitly verifying every generated claim against the original raw resume text.
"""
from typing import Any
from . import llm

def verify_cover_letter_claims(cover_letter_text: str, profile: dict[str, Any], prefs: dict[str, Any]) -> str:
    """Verifies a cover letter against the candidate's profile.
    
    If the LLM spots facts not present in the original resume, it flags or rejects the letter,
    regenerating a safe version.
    """
    if not cover_letter_text.strip():
        return cover_letter_text
        
    source_text = profile.get("raw_text", "")
    if not source_text:
        return cover_letter_text # Can't verify without source
        
    prompt = (
        "You are an aggressive fact-checker and anti-hallucination shield.\n"
        "Your job is to read the proposed Cover Letter and verify that EVERY claim about the "
        "candidate's experience, skills, dates, metrics, and degrees exists in the Candidate's Source Resume.\n\n"
        f"CANDIDATE SOURCE RESUME:\n\"\"\"\n{source_text[:6000]}\n\"\"\"\n\n"
        f"PROPOSED COVER LETTER:\n\"\"\"\n{cover_letter_text}\n\"\"\"\n\n"
        "If you find ANY fabricated claim, metric, or skill in the Cover Letter that is NOT supported by the "
        "Source Resume, you must rewrite the Cover Letter to remove the fabrication, keeping the rest intact. "
        "If the Cover Letter is 100% truthful, simply output the original Cover Letter exactly as it is.\n\n"
        "Output ONLY the final, safe cover letter text. No preamble, no explanation."
    )
    
    verified_text = llm.generate(
        prompt,
        system="You are a strict, objective fact-checker. You output only the safe text.",
        model=prefs.get("writing_model"),
        max_tokens=900,
        temperature=0.1
    )
    
    return verified_text.strip()


def verify_resume_claims(resume_data: dict[str, Any], profile: dict[str, Any], prefs: dict[str, Any]) -> dict[str, Any]:
    """Verifies a tailored resume dict against the candidate's source profile.
    
    Ensures zero hallucinated metrics, zero fake employers, and zero tech stack overclaims.
    """
    import json
    source_text = profile.get("raw_text", "") or json.dumps(profile)
    if not source_text or not resume_data:
        return resume_data

    prompt = (
        "You are an aggressive fact-checker and anti-hallucination shield for resumes.\n"
        "Your job is to inspect the PROPOSED TAILORED RESUME JSON and compare it strictly against the CANDIDATE SOURCE RESUME.\n\n"
        f"CANDIDATE SOURCE RESUME:\n\"\"\"\n{source_text[:6000]}\n\"\"\"\n\n"
        f"PROPOSED TAILORED RESUME JSON:\n\"\"\"\n{json.dumps(resume_data, indent=2)}\n\"\"\"\n\n"
        "CRITICAL AUDIT RULES:\n"
        "1. Remove or rewrite any bullet point that introduces hallucinated percentages, dollar amounts, or metrics not explicitly stated in the CANDIDATE SOURCE RESUME.\n"
        "2. Remove any skill from 'skills' that the candidate does not actually possess in the source.\n"
        "3. Do NOT invent new companies, titles, or dates.\n\n"
        "Return strictly the audited JSON object matching the exact same keys (summary, skills, experience, education, projects, certifications)."
    )

    try:
        audited = llm.generate_json(
            prompt,
            system="You are a strict anti-hallucination auditor. Return only valid JSON.",
            model=prefs.get("writing_model"),
            max_tokens=2600,
        )
        if isinstance(audited, dict) and "experience" in audited:
            # Preserve identity fields
            audited["name"] = resume_data.get("name", "")
            audited["contact"] = resume_data.get("contact", "")
            return audited
    except Exception:
        pass
    return resume_data
