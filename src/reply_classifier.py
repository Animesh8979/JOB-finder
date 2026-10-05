"""Inbound Employer Reply Classifier & Auto-Tracker (reply-watch protocol).

Classifies incoming recruiter/company emails into canonical pipeline states:
- INTERVIEW_INVITE -> Advances status to 'Interview'
- ASSESSMENT_OA    -> Advances status to 'Assessment' / 'Interview'
- SCREENING_REQUEST -> Prompts candidate to schedule initial recruiter call
- SALARY_ELIGIBILITY_CHECK -> Highlights questions to respond to
- REJECTION        -> Updates status to 'Rejected'
- GENERIC_ACK      -> Remains 'Applied'

Can automatically update the database application record.
"""
from __future__ import annotations

import re
from typing import Any
from . import db, llm


# Deterministic keyword patterns for fast first-pass classification
_REJECTION_PATTERNS = [
    r"\b(unfortunately|not moving forward|decided to pursue other|after careful consideration|at this time|impressive.*however)\b",
    r"\b(will not be moving forward|not selected|high volume of applicants|wish you the best in your job search)\b"
]

_INTERVIEW_PATTERNS = [
    r"\b(would like to invite you|schedule a (call|chat|interview|conversation)|availability for an interview)\b",
    r"\b(calendly\.com|goodtime\.io|hubspot\.com\/meetings|schedule a 30-minute|technical interview)\b"
]

_ASSESSMENT_PATTERNS = [
    r"\b(codesignal|hackerrank|take-home|coding challenge|technical assessment|complete the following assessment)\b"
]


def classify_inbound_reply(email_text: str, prefs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Classify an inbound email message from a recruiter or company."""
    prefs = prefs or {}
    text_lower = email_text.lower()

    # Fast heuristic check
    for pat in _REJECTION_PATTERNS:
        if re.search(pat, text_lower):
            return {
                "category": "REJECTION",
                "recommended_status": "Rejected",
                "confidence": 0.95,
                "summary": "Application was not selected to move forward.",
                "action_required": False,
                "suggested_response": None
            }

    for pat in _ASSESSMENT_PATTERNS:
        if re.search(pat, text_lower):
            return {
                "category": "TECHNICAL_ASSESSMENT",
                "recommended_status": "Interview",
                "confidence": 0.90,
                "summary": "Online technical assessment / take-home coding challenge received.",
                "action_required": True,
                "suggested_response": "Acknowledge receipt and schedule dedicated focus time to complete the test."
            }

    for pat in _INTERVIEW_PATTERNS:
        if re.search(pat, text_lower):
            return {
                "category": "INTERVIEW_INVITE",
                "recommended_status": "Interview",
                "confidence": 0.92,
                "summary": "Invitation to schedule a phone screen or interview.",
                "action_required": True,
                "suggested_response": "Reply promptly with 3 distinct availability blocks or book via their scheduling link."
            }

    # If ambiguous, use LLM
    prompt = (
        "You are an AI Inbound Email Classifier (reply-watch).\n"
        "Classify the following recruiter or company email:\n\"\"\"\n"
        f"{email_text[:3000]}\n\"\"\"\n\n"
        "Categories:\n"
        "- INTERVIEW_INVITE (invited to interview/screen)\n"
        "- TECHNICAL_ASSESSMENT (take-home or coding test)\n"
        "- SALARY_CHECK (asking for comp expectations or work-auth)\n"
        "- REJECTION (not moving forward)\n"
        "- GENERIC_ACK (application received)\n\n"
        "Return JSON:\n"
        "{\n"
        '  "category": "...",\n'
        '  "recommended_status": "Interview" | "Rejected" | "Applied",\n'
        '  "summary": "1 sentence explanation",\n'
        '  "action_required": bool,\n'
        '  "suggested_response": "Brief draft response if needed, else null"\n'
        "}"
    )

    data = {}
    if llm.provider_ready():
        try:
            data = llm.generate_json(
                prompt,
                system="You are an expert recruitment assistant. Return valid JSON only.",
                model=prefs.get("writing_model"),
                max_tokens=500
            )
        except Exception:
            data = {}

    return {
        "category": data.get("category", "GENERIC_ACK"),
        "recommended_status": data.get("recommended_status", "Applied"),
        "confidence": 0.85,
        "summary": data.get("summary", "Inbound email processed."),
        "action_required": data.get("action_required", False),
        "suggested_response": data.get("suggested_response")
    }


def process_reply_and_update_application(job_id: int, email_text: str, prefs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Classify email and update application status in SQLite."""
    res = classify_inbound_reply(email_text, prefs)
    rec_status = res.get("recommended_status")
    
    if rec_status and rec_status in db.STATUSES:
        db.update_application(job_id, status=rec_status, notes=f"Automated reply classification: {res.get('summary')}")
        
    return res
