"""
Format Audit & Application Review Preparation Pipeline (AOS v5.0 Aligned)

Performs local structural checks (section headers, keyword presence, contact parsing, readable formatting)
and prepares structured payloads for user-reviewed application sessions.
"""

from __future__ import annotations
import json
from typing import Any
from .recruiter_score import score as hackerrank_score


def format_audit(profile: dict[str, Any], target_role: str = "Senior AI Engineer") -> dict[str, Any]:
    """
    Evaluates resume formatting and keyword structure across standard ATS archetypes:
    1. Structural & section header check
    2. Keyword density & presence check
    3. Contact and portfolio parsing check
    4. Scoring against open-source/project impact rubric
    """
    raw_text = profile.get("raw_text") or json.dumps(profile)

    # 1. HackerRank rubric score
    hr_report = hackerrank_score(
        raw_text,
        github_handle=profile.get("links", {}).get("github", ""),
        skills=profile.get("skills", [])
    )
    hr_score = hr_report.to_dict()["total"]

    # 2. Keyword check
    target_keywords = ["python", "ai", "llm", "machine learning", "api", "architecture", "system design"]
    text_lower = raw_text.lower()
    matched_keywords = [kw for kw in target_keywords if kw in text_lower]
    keyword_density = int((len(matched_keywords) / len(target_keywords)) * 100)
    keyword_passed = keyword_density >= 50

    # 3. Section header integrity check
    required_sections = ["experience", "skills", "education", "projects"]
    found_sections = [sec for sec in required_sections if sec in text_lower]
    section_score = int((len(found_sections) / len(required_sections)) * 100)
    section_passed = section_score >= 75

    # 4. Contact and link parsing check
    has_contact = bool(profile.get("email") or "email" in text_lower or "@" in text_lower)
    has_github = bool("github.com" in text_lower)
    contact_passed = has_contact and has_github

    parsers = {
        "HackerRank": {
            "score": f"{hr_score}/120",
            "passed": hr_score >= 60,
            "note": "Evaluates open-source engineering & quantified impact."
        },
        "Greenhouse": {
            "score": f"{keyword_density}% Keyword Match",
            "passed": keyword_passed,
            "note": f"Matched keywords: {', '.join(matched_keywords)}"
        },
        "Workday": {
            "score": f"{section_score}% Structural Integrity",
            "passed": section_passed,
            "note": f"Detected sections: {', '.join(found_sections)}"
        },
        "Lever": {
            "score": "PASS" if contact_passed else "REVIEW",
            "passed": contact_passed,
            "note": "Verifies clean contact info & GitHub portfolio link parsing."
        }
    }

    all_passed = all(p["passed"] for p in parsers.values())

    return {
        "verified": True,
        "audit_type": "format_audit",
        "overall_ats_compatibility": "PASS (FORMAT VERIFIED)" if all_passed else "REVIEW REQUIRED",
        "all_parsers_passed": all_passed,
        "parsers": parsers
    }


def simulate_enterprise_ats_parsers(profile: dict[str, Any], target_role: str = "Senior AI Engineer") -> dict[str, Any]:
    """Compatibility wrapper around format_audit."""
    return format_audit(profile, target_role)


def prepare_application_payload(profile: dict[str, Any], job_url: str = "https://remoteok.com/remote-jobs/ai-engineer") -> dict[str, Any]:
    """
    Prepares candidate profile data into a structured payload ready for review-first browser preparation.
    """
    ats_audit = format_audit(profile)

    payload = {
        "candidate_name": profile.get("name", "Candidate"),
        "candidate_email": profile.get("email", ""),
        "github_url": profile.get("links", {}).get("github", ""),
        "skills": profile.get("skills", []),
        "ats_compatibility": ats_audit["overall_ats_compatibility"],
        "target_job_url": job_url,
        "status": "STAGED_READY_FOR_USER_REVIEW"
    }

    return {
        "staged": True,
        "ats_audit": ats_audit,
        "application_payload": payload
    }


def stage_instant_auto_apply(profile: dict[str, Any], job_url: str = "https://remoteok.com/remote-jobs/ai-engineer") -> dict[str, Any]:
    """Compatibility wrapper around prepare_application_payload."""
    return prepare_application_payload(profile, job_url)

