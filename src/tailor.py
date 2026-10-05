"""Generate a tailored resume and a cover letter for a specific job.

Hard rule enforced in every prompt: emphasize and re-word the candidate's REAL
experience, but never invent employers, titles, dates, degrees, tools, or metrics.
"""
from __future__ import annotations

from typing import Any

from . import llm
from .profile_parser import profile_context
from .fabrication_shield import verify_cover_letter_claims, verify_resume_claims
from .anti_slop import audit_and_sanitize, sanitize_bullet

NO_FABRICATION = (
    "CRITICAL RULES:\n"
    "- Use ONLY facts present in the candidate profile / original resume text.\n"
    "- You MAY reorder, reword, summarize, and choose what to include or emphasize.\n"
    "- You MAY NOT invent employers, job titles, dates, degrees, certifications, tools,\n"
    "  metrics, or achievements that are not in the source. No exaggeration.\n"
    "- Keep everything truthful and ATS-friendly (plain text, standard sections, no tables).\n"
    "- HUMAN WRITING STYLE: Never use em-dashes (—), never use cliché buzzwords like delve/tapestry/spearheaded/fostered, vary sentence lengths drastically, write with concrete engineering verbs and numbers only.\n"
    "- ZERO AI CLICHÉS: Never use words like 'delve', 'testament', 'tapestry', 'spearheaded', 'spearhead', 'leverage', "
    "'holistic', 'fostered', 'foster', 'beacon', 'pivotal', 'robust', 'seamless', 'cutting-edge', 'thrilled to apply', "
    "'I hope this letter finds you well', 'Furthermore', 'Moreover', 'game-changer', 'revolutionize', 'transformative'.\n"
    "- NATURAL BUILDER VOICE: Use active, direct language with varied sentence rhythms."
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
    try:
        data = llm.generate_json(
            prompt,
            system=(
                "You are an expert resume writer and career coach. "
                "Never use em-dashes (—), never use cliché buzzwords like delve/tapestry/spearheaded/fostered, "
                "vary sentence lengths drastically, write with concrete engineering verbs and numbers only."
            ),
            cached_context=profile_context(profile),
            model=prefs.get("writing_model"),
            max_tokens=3000,
        )
    except Exception:
        data = {
            "summary": profile.get("summary", ""),
            "skills": profile.get("skills", []),
            "experience": profile.get("experience", []),
            "education": profile.get("education", []),
            "projects": profile.get("projects", []),
            "certifications": profile.get("certifications", []),
        }
    if not isinstance(data, dict):
        data = {}
    data["name"] = name
    data["contact"] = contact
    # Guarantee shape for the renderer.
    for key in ("skills", "experience", "education", "projects", "certifications"):
        data.setdefault(key, [])
    data.setdefault("summary", "")
    data = verify_resume_claims(data, profile, prefs)
    if "headline" in data and isinstance(data["headline"], str):
        data["headline"] = audit_and_sanitize(data["headline"]).cleaned_text
    if "summary" in data and isinstance(data["summary"], str):
        data["summary"] = audit_and_sanitize(data["summary"]).cleaned_text
    if "skills" in data and isinstance(data["skills"], list):
        data["skills"] = [audit_and_sanitize(str(s)).cleaned_text for s in data["skills"] if s]
    for exp in data.get("experience", []):
        if isinstance(exp, dict):
            if "title" in exp and isinstance(exp["title"], str):
                exp["title"] = audit_and_sanitize(exp["title"]).cleaned_text
            if "company" in exp and isinstance(exp["company"], str):
                exp["company"] = audit_and_sanitize(exp["company"]).cleaned_text
            if "bullets" in exp and isinstance(exp["bullets"], list):
                exp["bullets"] = [sanitize_bullet(b) for b in exp["bullets"] if b]
    for proj in data.get("projects", []):
        if isinstance(proj, dict):
            if "name" in proj and isinstance(proj["name"], str):
                proj["name"] = audit_and_sanitize(proj["name"]).cleaned_text
            if "line" in proj and isinstance(proj["line"], str):
                proj["line"] = sanitize_bullet(proj["line"])
            if "description" in proj and isinstance(proj["description"], str):
                proj["description"] = audit_and_sanitize(proj["description"]).cleaned_text
            if "bullets" in proj and isinstance(proj["bullets"], list):
                proj["bullets"] = [sanitize_bullet(b) for b in proj["bullets"] if b]
    for i, edu in enumerate(data.get("education", [])):
        if isinstance(edu, str):
            data["education"][i] = audit_and_sanitize(edu).cleaned_text
        elif isinstance(edu, dict):
            for k in ("degree", "field", "institution", "school"):
                if k in edu and isinstance(edu[k], str):
                    edu[k] = audit_and_sanitize(edu[k]).cleaned_text
    if "certifications" in data and isinstance(data["certifications"], list):
        data["certifications"] = [audit_and_sanitize(str(c)).cleaned_text for c in data["certifications"] if c]
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
        "if no name is known. Do NOT add dates or postal addresses - start at the salutation and "
        "end by signing off with the candidate's name."
    )
    try:
        text = llm.generate(
            prompt,
            system=(
                "You are an expert cover-letter writer. Write authentically like a real engineer. "
                "Never use em-dashes (—), never use cliché buzzwords like delve/tapestry/spearheaded/fostered, "
                "vary sentence lengths drastically, write with concrete engineering verbs and numbers only."
            ),
            cached_context=profile_context(profile),
            model=prefs.get("writing_model"),
            max_tokens=900,
            temperature=0.6,
        )
    except Exception:
        text = (
            f"Dear Hiring Manager,\n\n"
            f"I am applying for the {job.get('title','role')} position at {job.get('company','your company')}. "
            f"With a strong background in {profile.get('headline','Business Analytics and AI Automation')} and hands-on experience "
            f"building end-to-end Python data science pipelines, KPI dashboards, and multi-agent AI systems, I am excited about "
            f"the opportunity to contribute to your data initiatives.\n\n"
            f"At Elevate Labs, I engineered regression and classification models in Python that delivered reliable, actionable "
            f"business insights, earning the Best Performer Award. I also built full-stack automation workflows including "
            f"an intelligent job matching engine and automated data analytics dashboards.\n\n"
            f"I look forward to discussing how my skills in Python, SQL, and AI workflow automation can create immediate value for your team.\n\n"
            f"Sincerely,\n{name}"
        )
    text = text.strip()
    verified = verify_cover_letter_claims(text, profile, prefs)
    return audit_and_sanitize(verified).cleaned_text


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
            system=(
                "You are an expert resume writer. Be truthful, clear, and action-oriented. "
                "Never use em-dashes (—), never use cliché buzzwords like delve/tapestry/spearheaded/fostered, "
                "vary sentence lengths drastically, write with concrete engineering verbs and numbers only."
            ),
            cached_context=profile_context(profile),
            model=prefs.get("writing_model"),
            max_tokens=2000
        )
        if isinstance(data, dict) and "suggestions" in data:
            for s in data["suggestions"]:
                if isinstance(s, dict):
                    if "suggested" in s and s["suggested"]:
                        s["suggested"] = sanitize_bullet(s["suggested"])
                    if "explanation" in s and s["explanation"]:
                        s["explanation"] = audit_and_sanitize(str(s["explanation"])).cleaned_text
            return data["suggestions"]
    except Exception as e:
        print(f"Error generating bullet improvements: {e}")
        
    return []


# --- 4-Angle Cover Letter Strategic Generator (CareerOps Protocol) -----------

COVER_LETTER_ANGLES = {
    "vision": {
        "name": "The Vision Angle",
        "description": "Align candidate philosophy with company mission and long-term trajectory.",
        "instruction": "Open with deep admiration and alignment with the company's core mission, product vision, and market impact. Frame candidate background as a natural catalyst for their next stage of growth."
    },
    "problem_solver": {
        "name": "The Problem-Solver Angle",
        "description": "Directly address and deconstruct the hardest technical challenge mentioned in the JD.",
        "instruction": "Analyze the hardest technical problem or bottleneck described in the job requirements (scaling, distributed systems, latency, reliability) and explain the exact architectural methodology you have used to solve similar problems."
    },
    "methodology": {
        "name": "The Methodology Angle",
        "description": "Focus on engineering craft, testing discipline, observability, and shipping velocity.",
        "instruction": "Emphasize your engineering practices: high code quality, automated CI/CD, deterministic testing, zero-downtime deployments, and collaborative mentorship that raises team-wide standards."
    },
    "direct_executive": {
        "name": "The Direct / Executive Angle",
        "description": "High-impact, concise, metric-dense narrative with zero corporate fluff.",
        "instruction": "Cut straight to the point. No fluff. Highlight 3 decisive, verifiable accomplishments with production metrics and invite a technical conversation."
    }
}


def generate_strategic_cover_letter(
    job: dict[str, Any],
    profile: dict[str, Any],
    prefs: dict[str, Any],
    angle_key: str = "vision",
    tone: str = "Professional",
    extra_notes: str = "",
    company_intel: dict[str, Any] | None = None
) -> str:
    """Generate a high-converting cover letter using one of the 4 strategic CareerOps angles."""
    name, _ = _name_and_contact(profile, prefs)
    notes = f"Extra candidate context: {extra_notes}\n" if extra_notes.strip() else ""
    
    angle_info = COVER_LETTER_ANGLES.get(angle_key.lower(), COVER_LETTER_ANGLES["vision"])
    
    intel_str = ""
    if company_intel and company_intel.get("overview"):
        intel_str = f"COMPANY OVERVIEW: {company_intel.get('overview')}\nCULTURE: {company_intel.get('culture_signals', '')}\n\n"

    prompt = (
        f"Write a high-converting {tone.lower()} cover letter using '{angle_info['name']}'.\n\n"
        f"STRATEGIC ANGLE INSTRUCTION:\n{angle_info['instruction']}\n\n"
        f"JOB TITLE: {job.get('title','')}\nCOMPANY: {job.get('company','')}\n"
        f"JOB DESCRIPTION:\n\"\"\"\n{(job.get('description') or '')[:3000]}\n\"\"\"\n\n"
        f"{intel_str}"
        f"Candidate name: {name}\n{notes}\n"
        f"{NO_FABRICATION}\n\n"
        "Guidelines:\n"
        "- 250-320 words in 3-4 structured paragraphs.\n"
        "- Salutation: 'Dear Hiring Manager,' (or name if known).\n"
        "- Strict truthfulness: use only verified achievements from candidate profile.\n"
        "- Sign-off: 'Sincerely,\n" + name + "'"
    )

    text = llm.generate(
        prompt,
        system=(
            "You are an elite career strategist and executive copywriter. "
            "Never use em-dashes (—), never use cliché buzzwords like delve/tapestry/spearheaded/fostered, "
            "vary sentence lengths drastically, write with concrete engineering verbs and numbers only."
        ),
        cached_context=profile_context(profile),
        model=prefs.get("writing_model"),
        max_tokens=900,
        temperature=0.5,
    )
    verified = verify_cover_letter_claims(text.strip(), profile, prefs)
    return audit_and_sanitize(verified).cleaned_text


def company_specific_cover_letter(
    job: dict[str, Any],
    profile: dict[str, Any],
    prefs: dict[str, Any],
    tone: str = "Professional",
    extra_notes: str = "",
    company_intel: dict[str, Any] | None = None,
    angle: str = "vision"
) -> str:
    """Generate a cover letter utilizing company intelligence details to create custom hooks."""
    return generate_strategic_cover_letter(
        job, profile, prefs, angle_key=angle, tone=tone, extra_notes=extra_notes, company_intel=company_intel
    )



