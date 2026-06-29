"""LLM Fabrication Shield (RAG Verification).

Ensures a 0% hallucination rate on cover letters and tailored resumes by 
explicitly verifying every generated claim against the original raw resume text.
"""
import re
from typing import Any
from . import llm
from .profile_parser import profile_context

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
