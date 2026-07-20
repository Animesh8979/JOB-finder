"""Generate a tailored resume and a cover letter for a specific job.

Hard rule enforced in every prompt: emphasize and re-word the candidate's REAL
experience, but never invent employers, titles, dates, degrees, tools, or metrics.
"""
from __future__ import annotations

from typing import Any

from . import llm
from .profile_parser import profile_context
from .fabrication_shield import verify_cover_letter_claims, verify_resume_claims

NO_FABRICATION = (
    "CRITICAL RULES:\n"
    "- Use ONLY facts present in the candidate profile / original resume text.\n"
    "- You MAY reorder, reword, summarize, and choose what to include or emphasize.\n"
    "- You MAY NOT invent employers, job titles, dates, degrees, certifications, tools,\n"
    "  metrics, or achievements that are not in the source. No exaggeration.\n"
    "- Keep everything truthful and ATS-friendly (plain text, standard sections, no tables)."
)


def _name_and_contact(profile: dict[str, Any], prefs: dict[str, Any]) -> tuple[str, str]:
    ident = prefs.get("identity", {}) or {}
    links = profile.get("links", {}) or {}
    name = ident.get("full_name") or profile.get("name") or ""
    bits = [
        ident.get("email") or profile.get("email", ""),
        ident.get("phone") or profile.get("phone", ""),
        ident.get("location") or profile.get("location", ""),
        ident.get("linkedin") or links.get("linkedin", ""),
    ]
    return name, "  ·  ".join(b for b in bits if b)


def tailor_resume(job: dict[str, Any], profile: dict[str, Any], prefs: dict[str, Any], angle: str = "") -> dict[str, Any]:
    """Return a tailored resume as a structured dict (rendered to DOCX/PDF elsewhere)."""
    name, contact = _name_and_contact(profile, prefs)
    
    angle_instruction = ""
    if angle and angle != "Balanced (Default)":
        angle_instruction = f"\n\nFOCUS/ANGLE: Strongly emphasize '{angle}' throughout the summary and bullet points."

    prompt = (
        "Create a resume TAILORED to the following job.\n\n"
        f"JOB TITLE: {job.get('title','')}\nCOMPANY: {job.get('company','')}\n"
        f"JOB DESCRIPTION:\n\"\"\"\n{(job.get('description') or '')[:3500]}\n\"\"\"\n\n"
        f"{NO_FABRICATION}{angle_instruction}\n\n"
        "Return JSON with these keys:\n"
        "- summary (str): 2-3 sentences tuned to this role.\n"
        "- skills (list[str]): most relevant first; only skills the candidate actually has.\n"
        "- experience (list of objects): {title, company, location, dates, "
        "bullets (list[str], rewritten to emphasize relevance; keep numbers only if they "
        "appear in the source)}.\n"
        "- education (list[str]): each a one-line entry.\n"
        "- projects (list of objects): {name, line}.\n"
        "- certifications (list[str])."
    )
    data = llm.generate_json(
        prompt,
        system="You are an expert resume writer and career coach.",
        cached_context=profile_context(profile),
        model=prefs.get("writing_model"),
        max_tokens=2600,
    )
    if not isinstance(data, dict):
        data = {}
    data["name"] = name
    data["contact"] = contact
    # Guarantee shape for the renderer.
    for key in ("skills", "experience", "education", "projects", "certifications"):
        data.setdefault(key, [])
    data.setdefault("summary", "")
    data = verify_resume_claims(data, profile, prefs)
    return data


def cover_letter(
    job: dict[str, Any],
    profile: dict[str, Any],
    prefs: dict[str, Any],
    tone: str = "Professional",
    extra_notes: str = "",
) -> str:
    """Return a tailored cover letter as plain text (salutation → sign-off)."""
    name, _ = _name_and_contact(profile, prefs)
    notes = f"Extra notes to weave in naturally: {extra_notes}\n" if extra_notes.strip() else ""
    prompt = (
        f"Write a {tone.lower()} cover letter for this job.\n\n"
        f"JOB TITLE: {job.get('title','')}\nCOMPANY: {job.get('company','')}\n"
        f"JOB DESCRIPTION:\n\"\"\"\n{(job.get('description') or '')[:3000]}\n\"\"\"\n\n"
        f"Candidate name: {name}\n{notes}\n"
        f"{NO_FABRICATION}\n\n"
        "Guidelines: 250-350 words in 3-4 short paragraphs. Open with a specific hook (not "
        "'I am writing to apply'). Show genuine fit using the candidate's REAL experience. "
        "Say why THIS company/role. End with a polite call to action. Use 'Dear Hiring Manager' "
        "if no name is known. Do NOT add dates or postal addresses — start at the salutation and "
        "end by signing off with the candidate's name."
    )
    text = llm.generate(
        prompt,
        system="You are an expert cover-letter writer.",
        cached_context=profile_context(profile),
        model=prefs.get("writing_model"),
        max_tokens=900,
        temperature=0.6,
    )
    text = text.strip()
    return verify_cover_letter_claims(text, profile, prefs)


def suggest_bullet_improvements(job: dict[str, Any], profile: dict[str, Any], prefs: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate side-by-side bullet point improvements for the resume."""
    if not profile or not job:
        return []
        
    experience = profile.get("experience", [])
    if not experience:
        return []
        
    original_bullets = []
    for exp in experience:
        for b in exp.get("bullets", []) or []:
            if b and b.strip():
                original_bullets.append(b.strip())
                
    if not original_bullets:
        return []
        
    prompt = (
        "You are an expert resume optimizer.\n"
        "Your task is to review the candidate's original bullet points and suggest improvements to align them with the job description below.\n\n"
        "RULES:\n"
        "- Emphasize relevance by matching technologies, methodologies, and requirements in the job description.\n"
        "- Start each suggested bullet with a strong action verb (e.g. Led, Designed, Built).\n"
        f"- {NO_FABRICATION}\n\n"
        f"JOB TITLE: {job.get('title','')}\n"
        f"JOB DESCRIPTION:\n\"\"\"\n{(job.get('description') or '')[:2500]}\n\"\"\"\n\n"
        "ORIGINAL BULLET POINTS:\n" + 
        "\n".join(f"- {b}" for b in original_bullets) + "\n\n"
        "Return a JSON object containing a 'suggestions' list of objects. Each object must have:\n"
        "- 'original': the exact original bullet point.\n"
        "- 'suggested': the optimized version of that bullet point.\n"
        "- 'explanation': why the rewrite was made (e.g. which keywords were added or verb changed)."
    )
    
    try:
        data = llm.generate_json(
            prompt,
            system="You are an expert resume writer. Be truthful, clear, and action-oriented.",
            cached_context=profile_context(profile),
            model=prefs.get("writing_model"),
            max_tokens=2000
        )
        if isinstance(data, dict) and "suggestions" in data:
            return data["suggestions"]
    except Exception as e:
        print(f"Error generating bullet improvements: {e}")
        
    return []


def company_specific_cover_letter(
    job: dict[str, Any],
    profile: dict[str, Any],
    prefs: dict[str, Any],
    tone: str = "Professional",
    extra_notes: str = "",
    company_intel: dict[str, Any] | None = None
) -> str:
    """Generate a cover letter utilizing company intelligence details to create custom hooks."""
    name, _ = _name_and_contact(profile, prefs)
    notes = f"Extra notes to weave in naturally: {extra_notes}\n" if extra_notes.strip() else ""
    
    intel_str = ""
    if company_intel and company_intel.get("mission"):
        intel_str = (
            "COMPANY RESEARCH SUMMARY:\n"
            f"Mission: {company_intel.get('mission')}\n"
            f"Values: {', '.join(company_intel.get('values', []))}\n"
            f"Milestones: {', '.join(company_intel.get('milestones', []))}\n"
            f"Culture: {company_intel.get('culture_summary')}\n\n"
            "INSTRUCTION: Open the cover letter with a personalized hook showing your alignment with their mission, values, or recent milestones. Avoid generic lines like 'I am writing to apply'.\n\n"
        )
    
    prompt = (
        f"Write a {tone.lower()} cover letter for this job.\n\n"
        f"JOB TITLE: {job.get('title','')}\nCOMPANY: {job.get('company','')}\n"
        f"JOB DESCRIPTION:\n\"\"\"\n{(job.get('description') or '')[:3000]}\n\"\"\"\n\n"
        f"{intel_str}"
        f"Candidate name: {name}\n{notes}\n"
        f"{NO_FABRICATION}\n\n"
        "Guidelines: 250-350 words in 3-4 short paragraphs. Open with a specific company hook from the research above. "
        "Show genuine fit using the candidate's REAL experience. Say why THIS company/role. "
        "End with a polite call to action. Use 'Dear Hiring Manager' if no name is known. "
        "Do NOT add dates or postal addresses — start at the salutation and end by signing off with the candidate's name."
    )
    
    text = llm.generate(
        prompt,
        system="You are an expert cover-letter writer.",
        cached_context=profile_context(profile),
        model=prefs.get("writing_model"),
        max_tokens=900,
        temperature=0.6,
    )
    text = text.strip()
    return verify_cover_letter_claims(text, profile, prefs)


