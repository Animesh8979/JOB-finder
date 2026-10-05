"""Persona-Targeted Outreach Engine (contacto protocol).

Generates ≤300-character LinkedIn connection requests tuned to 3 distinct personas:
1. Hiring Manager: Focus on delivery velocity, technical problem solving, and architecture.
2. Recruiter / Talent Partner: Focus on exact keywords, seniority level, and immediate availability.
3. Future Engineering Peer: Focus on shared craft, open-source work, and tech stack synergy.

Also generates formal email application drafts with attachment checklists and contact blocks.
"""
from __future__ import annotations

from typing import Any
from . import llm
from .profile_parser import profile_context
from .anti_slop import audit_and_sanitize


def generate_persona_outreach(
    job: dict[str, Any],
    profile: dict[str, Any],
    prefs: dict[str, Any],
    contact_name: str = "Hiring Team"
) -> dict[str, Any]:
    """Generate 3 persona-specific LinkedIn connection notes and 1 formal application email."""
    name = (prefs.get("identity", {}) or {}).get("full_name") or profile.get("name") or "Candidate"
    skills = ", ".join(profile.get("skills", [])[:6])
    
    prompt = (
        "You are an Elite Career Networking Coach (contacto protocol).\n"
        "Draft targeted outreach messages for the following job opportunity.\n\n"
        f"JOB TITLE: {job.get('title', '')}\n"
        f"COMPANY: {job.get('company', '')}\n"
        f"JOB DESCRIPTION:\n\"\"\"\n{(job.get('description') or '')[:2500]}\n\"\"\"\n\n"
        f"CANDIDATE NAME: {name}\n"
        f"CORE SKILLS: {skills}\n"
        f"TARGET CONTACT NAME: {contact_name}\n\n"
        "RULES:\n"
        "1. Never use em-dashes (—) or double hyphens (--). Use commas or hyphens (-).\n"
        "2. Never use cliché buzzwords like delve/tapestry/spearheaded/fostered/leverage/robust/seamless.\n"
        "3. Vary sentence rhythms drastically. Write with concrete engineering verbs and authentic human tone.\n"
        "4. LinkedIn notes MUST BE ≤300 characters each (hard LinkedIn character limit).\n"
        "5. Hiring Manager Note: Focus on scaling, engineering velocity, and technical problem solving.\n"
        "6. Recruiter Note: Focus on exact stack fit, level alignment, and availability.\n"
        "7. Peer Note: Focus on shared tech stack, open-source projects, and engineering craft.\n"
        "8. Email Application Draft: Structured formal email with subject line, 3 concise proof points, and attachment checklist.\n\n"
        "Return strictly valid JSON with these exact keys:\n"
        "{\n"
        '  "linkedin_hiring_manager": "≤300 chars message",\n'
        '  "linkedin_recruiter": "≤300 chars message",\n'
        '  "linkedin_peer": "≤300 chars message",\n'
        '  "email_application": {\n'
        '    "subject": "Application: [Title] - [Candidate Name]",\n'
        '    "body": "Formal application email body",\n'
        '    "attachment_checklist": ["Tailored Resume (PDF)", "Cover Letter (PDF)", "Code Portfolio / GitHub Link"]\n'
        '  }\n'
        "}"
    )

    data = {}
    if llm.provider_ready():
        try:
            data = llm.generate_json(
                prompt,
                system=(
                    "You are an expert executive networking coach. "
                    "Never use em-dashes (—), never use cliché buzzwords like delve/tapestry/spearheaded/fostered, "
                    "vary sentence lengths drastically, write with concrete engineering verbs and numbers only. "
                    "Return valid JSON only."
                ),
                cached_context=profile_context(profile),
                model=prefs.get("writing_model"),
                max_tokens=900
            )
        except Exception:
            data = {}

    if not isinstance(data, dict):
        data = {}

    # Enforce ≤300 chars limit and anti-slop sanitization defensively
    def _cap300(text: Any, fallback: str) -> str:
        raw = str(text).strip() if (text and str(text).strip()) else fallback
        clean = audit_and_sanitize(raw).cleaned_text
        return clean[:297] + "..." if len(clean) > 300 else clean

    hm_fb = f"Hi {contact_name}, saw your work at {job.get('company','')}. With deep experience in {skills[:60]}, I'd love to connect and share how I can accelerate the {job.get('title','')} roadmap."
    rec_fb = f"Hi {contact_name}, I recently applied for {job.get('title','')} at {job.get('company','')}. My background aligns directly with your stack ({skills[:50]}). Would love to connect!"
    peer_fb = f"Hey {contact_name}, love what the team at {job.get('company','')} is building. Fellow engineer working with {skills[:50]}, would enjoy connecting and following your work!"

    raw_email = data.get("email_application") if isinstance(data.get("email_application"), dict) else {
        "subject": f"Application: {job.get('title', 'Engineering Role')} - {name}",
        "body": f"Dear {contact_name},\n\nI am applying for the {job.get('title', '')} position at {job.get('company', '')}. My experience in {skills} directly mirrors your technical needs.\n\nAttached are my tailored resume and portfolio.\n\nBest regards,\n{name}",
        "attachment_checklist": [
            "Tailored ATS Resume (PDF)",
            "Cover Letter (PDF)",
            "GitHub Evidence & Portfolio Link"
        ]
    }

    clean_email = {
        "subject": audit_and_sanitize(str(raw_email.get("subject", ""))).cleaned_text,
        "body": audit_and_sanitize(str(raw_email.get("body", ""))).cleaned_text,
        "attachment_checklist": [
            audit_and_sanitize(str(item)).cleaned_text
            for item in raw_email.get("attachment_checklist", [])
            if item
        ]
    }

    return {
        "job_id": job.get("id"),
        "company": job.get("company"),
        "title": job.get("title"),
        "linkedin_hiring_manager": _cap300(data.get("linkedin_hiring_manager"), hm_fb),
        "linkedin_recruiter": _cap300(data.get("linkedin_recruiter"), rec_fb),
        "linkedin_peer": _cap300(data.get("linkedin_peer"), peer_fb),
        "email_application": clean_email
    }
