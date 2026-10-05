"""Offer Stage & Contract Clause Analyzer (offer-prep protocol).

Analyzes job offer letters and employment contracts for:
1. Intellectual Property (IP) assignment overreach (e.g. claiming personal side projects).
2. Non-compete and non-solicitation restrictions.
3. Clawback provisions (signing bonus or relocation repayment windows).
4. Salary gap vs desired/market rate with tailored negotiation counter-scripts.
5. Prioritized question list for legal counsel or hiring managers.
"""
from __future__ import annotations

import re
from typing import Any
from . import llm


# Deterministic high-risk clause keywords
_CLAUSE_PATTERNS = [
    ("ip_assignment", r"\b(all (inventions|intellectual property|ideas|copyrights).*whether or not during working hours)\b", "Broad IP Assignment Overreach: may claim personal side-projects created outside work hours."),
    ("non_compete", r"\b(non-compete|shall not engage in|competitive business for a period of [0-9]+ (months|years))\b", "Non-Compete Restriction: limits future employment in the same industry post-departure."),
    ("clawback", r"\b(repay|clawback|pro-rated repayment|if employee leaves within [0-9]+ (months|years))\b", "Signing/Relocation Clawback: requires repayment if resigning within 12-24 months."),
    ("moonlighting", r"\b(exclusive services|sole employment|shall not engage in any other business or commercial activity)\b", "Moonlighting Ban: prohibits open-source contributions, advisory roles, or side businesses."),
    ("at_will_arbitration", r"\b(binding arbitration|waive right to jury trial|class action waiver)\b", "Mandatory Arbitration: disputes resolved through private arbitration rather than public courts.")
]


def audit_offer_contract(contract_text: str, prefs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Audit offer letter text for red flag clauses and generate lawyer questions."""
    prefs = prefs or {}
    text_lower = contract_text.lower()
    
    flagged_clauses = []
    for category, pat, risk_desc in _CLAUSE_PATTERNS:
        match = re.search(pat, text_lower, re.IGNORECASE)
        if match:
            flagged_clauses.append({
                "category": category,
                "risk_level": "HIGH" if category in ("ip_assignment", "non_compete") else "MEDIUM",
                "finding": risk_desc,
                "matched_snippet": match.group(0)
            })

    prompt = (
        "You are an Elite Tech Employment Lawyer & Executive Compensation Advisor.\n"
        "Audit this employment offer/contract text:\n\"\"\"\n"
        f"{contract_text[:4000]}\n\"\"\"\n\n"
        "Analyze:\n"
        "1. Identified risks and overreach\n"
        "2. Top 3 questions to ask employment counsel or the recruiter\n"
        "3. Recommended amendments to protect the candidate's personal side projects\n\n"
        "Return strictly valid JSON: {\n"
        '  "executive_summary": "1-2 sentence overview",\n'
        '  "lawyer_questions": ["Question 1", "Question 2", "Question 3"],\n'
        '  "suggested_amendments": [{"clause": "...", "amendment": "..."}]\n'
        "}"
    )

    data = {}
    if llm.provider_ready():
        try:
            data = llm.generate_json(
                prompt,
                system="You are an expert contract advisor. Return valid JSON only.",
                model=prefs.get("writing_model"),
                max_tokens=900
            )
        except Exception:
            data = {}

    return {
        "flagged_clauses": flagged_clauses,
        "lawyer_questions": data.get("lawyer_questions", [
            "Does the IP assignment clause explicitly exclude pre-existing personal projects listed on an Exhibit A?",
            "Is the non-compete clause legally enforceable in the candidate's state/country of residence?",
            "What is the exact vesting and clawback timeline on equity and sign-on bonuses?"
        ]),
        "suggested_amendments": data.get("suggested_amendments", []),
        "summary": data.get("executive_summary", "Contract reviewed for IP overreach and clawbacks.")
    }


def analyze_salary_gap(
    offered_base: int,
    desired_base: int,
    market_median: int,
    currency: str = "USD",
    prefs: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Calculate salary gap and generate actionable negotiation counter-scripts."""
    prefs = prefs or {}
    gap = desired_base - offered_base
    gap_percent = round((gap / offered_base) * 100, 1) if offered_base > 0 else 0.0

    prompt = (
        f"Generate a professional, high-leverage compensation negotiation script.\n"
        f"Offered Base: {offered_base:,} {currency}\n"
        f"Desired Base: {desired_base:,} {currency}\n"
        f"Market Median: {market_median:,} {currency}\n"
        f"Gap: {gap:,} {currency} ({gap_percent}%)\n\n"
        "Provide:\n"
        "1. Email counter-offer script (polite, confident, grounded in market value)\n"
        "2. Phone negotiation talking points (how to handle pushback like 'this is our band limit')\n"
        "3. Alternative levers if base is fixed (signing bonus, extra equity, accelerated review, remote stipend)\n\n"
        "Return JSON: {\"counter_email\": \"...\", \"phone_talking_points\": [\"...\"], \"alternative_levers\": [\"...\"]}"
    )

    data = {}
    if llm.provider_ready():
        try:
            data = llm.generate_json(
                prompt,
                system="You are a seasoned executive negotiation coach.",
                model=prefs.get("writing_model"),
                max_tokens=800
            )
        except Exception:
            data = {}

    return {
        "offered_base": offered_base,
        "desired_base": desired_base,
        "market_median": market_median,
        "gap": gap,
        "gap_percent": gap_percent,
        "currency": currency,
        "counter_email": data.get("counter_email", (
            f"Thank you for extending this offer. I am genuinely excited about the team's vision. "
            f"Given the scope of the role and current market data for this level ({market_median:,} {currency}), "
            f"I would be thrilled to sign immediately at a base salary of {desired_base:,} {currency}."
        )),
        "phone_talking_points": data.get("phone_talking_points", [
            "Reiterate strong excitement about the team and technical roadmap.",
            f"Anchor on market benchmarks of {desired_base:,} {currency} based on candidate proven impact.",
            "If base is capped, ask for an increased sign-on bonus or accelerated 6-month equity grant review."
        ]),
        "alternative_levers": data.get("alternative_levers", [
            "Higher initial Signing Bonus to bridge year 1 compensation",
            "Additional RSU / Equity Grant",
            "Guaranteed 6-month performance review cycle",
            "Annual learning and remote setup budget"
        ])
    }
