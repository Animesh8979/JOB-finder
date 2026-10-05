"""Block G: Posting Legitimacy, Ghost-Job, Scam, and Work-Auth Pre-Filter Engine.

Deterministic, zero-LLM-cost heuristic filter inspired by career-ops Block G.
Evaluates job postings for scam signals, ghost-job/stale indicators, and explicit
visa/work-authorization hard blockers without distorting the 1-100 technical fit score.
"""
from __future__ import annotations

import re
from typing import Any
from datetime import datetime, timezone


# --- Scam & Fraud Patterns ---------------------------------------------------
_SCAM_PATTERNS = [
    (r"\b(telegram|whatsapp)\b.*(interview|contact|reach|message)", "Contact requested exclusively via insecure chat (Telegram/WhatsApp)", 40),
    (r"\b(wire transfer|crypto payment|buy equipment|reimburse.*check)\b", "Suspicious payment, equipment check, or wire transfer scheme", 50),
    (r"\b(no experience needed|earn \$[0-9]{3,}\/day.*simple task)\b", "Unrealistic compensation for zero-experience generic tasks", 30),
    (r"\b(processing fee|deposit required|pay for training)\b", "Upfront fee or paid training requested from candidate", 50),
    (r"\b(send (your )?ssn|social security number.*before interview)\b", "Premature request for sensitive PII/SSN before formal offer", 50),
]

# --- Ghost-Job / Low-Quality Indicators --------------------------------------
_GHOST_PATTERNS = [
    (r"\b(urgent urgent|immediate joiner only|immediate joining)\b", "High-churn or bait-and-switch staffing phrasing", 15),
    (r"\b(confidential client|undisclosed client|reputed client)\b", "Blind third-party agency repost without company transparency", 20),
    (r"\b(resume collecting|pipeline building|talent pool only)\b", "Passive talent pool aggregation with no active opening", 35),
]

# --- Work Authorization & Security Clearance Blockers -----------------------
_WORK_AUTH_PATTERNS = [
    (r"\b(no (c2c|corp to corp|sponsorship|visas?))\b", "Explicitly states no visa sponsorship or C2C permitted"),
    (r"\b(must be (a )?(u\.?s\.? citizen|permanent resident|green card holder))\b", "US Citizen or Green Card strictly required"),
    (r"\b(active (secret|top secret|ts\/sci) clearance required)\b", "Active US Security Clearance strictly required"),
    (r"\b(us citizens? only|only u\.?s\.? citizens?)\b", "Strict citizenship requirement"),
    (r"\b(w2 only.*no (c2c|visa))\b", "W2 only with no visa transfer support"),
]


def check_posting_legitimacy(
    job: dict[str, Any],
    candidate_prefs: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Evaluate job posting legitimacy, ghost-job probability, and work-auth blockers.

    Args:
        job: Dictionary representing the job posting (title, company, description, etc.).
        candidate_prefs: Candidate preferences including require_sponsorship, location, etc.

    Returns:
        dict containing:
            - legitimacy_score: int (0 to 100)
            - is_ghost_job: bool
            - is_scam: bool
            - work_auth_blocked: bool
            - risk_level: str ("LOW" | "MEDIUM" | "HIGH" | "BLOCKED")
            - signals: list[dict] with detailed rationale
            - passed_prefilter: bool
    """
    prefs = candidate_prefs or {}
    text = (job.get("description") or "").lower()
    title = (job.get("title") or "").lower()
    company = (job.get("company") or "").strip()
    full_text = f"{title}\n{company.lower()}\n{text}"

    signals: list[dict[str, Any]] = []
    penalty = 0

    # 1. Length & Substance check
    if len(text.strip()) < 180:
        penalty += 25
        signals.append({
            "category": "GHOST",
            "severity": "MEDIUM",
            "note": "Description is abnormally short (<180 characters), indicating placeholder or stub posting."
        })

    # 2. Scam & Fraud Detection
    is_scam = False
    for pat, desc, pts in _SCAM_PATTERNS:
        if re.search(pat, full_text, re.IGNORECASE):
            penalty += pts
            is_scam = True
            signals.append({
                "category": "SCAM",
                "severity": "HIGH",
                "note": desc
            })

    # 3. Ghost-Job Indicators
    is_ghost = False
    for pat, desc, pts in _GHOST_PATTERNS:
        if re.search(pat, full_text, re.IGNORECASE):
            penalty += pts
            if pts >= 20:
                is_ghost = True
            signals.append({
                "category": "GHOST",
                "severity": "LOW" if pts < 20 else "MEDIUM",
                "note": desc
            })

    # Stale Posting Check (if posted_at is provided)
    posted_at_raw = job.get("posted_at")
    if posted_at_raw:
        try:
            # Parse ISO or YYYY-MM-DD
            if isinstance(posted_at_raw, str) and len(posted_at_raw) >= 10:
                dt_posted = datetime.fromisoformat(posted_at_raw[:10]).replace(tzinfo=timezone.utc)
                age_days = (datetime.now(timezone.utc) - dt_posted).days
                if age_days > 60:
                    penalty += 25
                    is_ghost = True
                    signals.append({
                        "category": "GHOST",
                        "severity": "MEDIUM",
                        "note": f"Listing is {age_days} days old (>60 days), high probability of expired/ghost opening."
                    })
        except Exception:
            pass

    # 4. Work Authorization & Sponsorship Blocker Check
    work_auth_blocked = False
    require_sponsorship = prefs.get("require_sponsorship", False) or prefs.get("visa_sponsorship_needed", False)

    for pat, desc in _WORK_AUTH_PATTERNS:
        if re.search(pat, full_text, re.IGNORECASE):
            if require_sponsorship:
                work_auth_blocked = True
                signals.append({
                    "category": "WORK_AUTH",
                    "severity": "BLOCKER",
                    "note": f"Hard Blocker for candidate needing sponsorship: {desc}"
                })
            else:
                signals.append({
                    "category": "WORK_AUTH",
                    "severity": "INFO",
                    "note": f"Requirement noted: {desc}"
                })

    # 5. Missing Company Info Check
    if not company or company.lower() in ("unknown", "undisclosed", "n/a", "confidential"):
        penalty += 20
        signals.append({
            "category": "TRANSPARENCY",
            "severity": "LOW",
            "note": "Hiring company name is omitted or anonymous."
        })

    legitimacy_score = max(0, 100 - penalty)

    # Determine risk level
    if is_scam or legitimacy_score < 40:
        risk_level = "HIGH"
    elif work_auth_blocked:
        risk_level = "BLOCKED"
    elif is_ghost or legitimacy_score < 70:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    passed = (risk_level in ("LOW", "MEDIUM")) and not work_auth_blocked

    return {
        "legitimacy_score": legitimacy_score,
        "is_ghost_job": is_ghost,
        "is_scam": is_scam,
        "work_auth_blocked": work_auth_blocked,
        "risk_level": risk_level,
        "signals": signals,
        "passed_prefilter": passed
    }
