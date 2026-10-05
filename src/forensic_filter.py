"""Forensic Hiring Signal Detector & Ghost Job Filter.

Identifies phantom requisitions, resume harvesting traps, and compliance postings.
Combines:
1. Sub-millisecond rule-based pre-filtering (re-posting velocity, blacklist, buzzword density).
2. LLM-powered deep forensic inspection via src.llm for ambiguous postings.
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ForensicAuditResult:
    job_id: str
    company: str
    title: str
    is_ghost_job: bool
    real_hire_probability: float  # [0.0, 1.0]
    risk_factors: List[str]
    audit_tier: str  # 'VERIFIED_ACTIVE', 'SUSPICIOUS', 'CONFIRMED_GHOST'


class ForensicFilter:
    """Evaluates real hiring intent before compute or application slots are spent."""

    def __init__(self):
        self.known_ghost_companies = {
            "revature", "cognizant", "infosys", "wipro"
        }

    def audit_job(self, job: Dict[str, Any], use_llm: bool = True) -> ForensicAuditResult:
        job_id = str(job.get("id") or job.get("job_id") or "unknown")
        company = str(job.get("company") or "").strip()
        title = str(job.get("title") or "").strip()
        desc = str(job.get("description") or "").lower()

        risk_factors: List[str] = []
        penalty = 0.0

        # 1. Company blacklist / evergreen check
        if company.lower() in self.known_ghost_companies:
            risk_factors.append("Company flagged for perpetual talent harvesting / evergreen bench pooling")
            penalty += 0.45

        # 2. Days active / age check
        posted_at = job.get("posted_at") or job.get("date_posted")
        days_active = 0
        if isinstance(posted_at, (int, float)):
            days_active = int((time.time() - posted_at) / 86400)
        elif isinstance(job.get("days_active"), (int, float)):
            days_active = int(job["days_active"])

        if days_active > 90:
            risk_factors.append(f"Requisition active for {days_active} days (likely stale evergreen posting)")
            penalty += 0.35
        elif days_active > 45:
            risk_factors.append(f"Requisition active for {days_active} days without fulfillment")
            penalty += 0.15

        # 3. Reposting signal
        repost_count = int(job.get("repost_count") or 0)
        if repost_count >= 3:
            risk_factors.append(f"Job reposted {repost_count} times on job boards")
            penalty += 0.30

        # 4. Text Specificity vs Generic Boilerplate Ratio
        concrete_tokens = set(re.findall(r"\b(kubernetes|docker|python|rust|golang|postgres|fastapi|aws|gcp|kafka|clickhouse|terraform)\b", desc))
        vague_tokens = set(re.findall(r"\b(synergy|rockstar|ninja|fast-paced|self-starter|dynamic|team-player|wear-many-hats)\b", desc))

        if len(concrete_tokens) == 0 and len(vague_tokens) >= 2:
            risk_factors.append("High buzzword density with zero verifiable technical stack requirements")
            penalty += 0.25

        # 5. Layoff warning flag
        if job.get("has_recent_layoffs") is True or "layoff" in desc:
            risk_factors.append("Company recorded recent layoffs within past 90 days")
            penalty += 0.20

        # Heuristic baseline probability
        real_hire_prob = max(0.02, min(0.98, 1.0 - penalty))

        # Optional LLM deep forensic pass if ambiguous and use_llm requested
        if use_llm and (0.35 <= real_hire_prob <= 0.70) and len(desc) > 150:
            try:
                from . import llm
                prompt = (
                    f"Perform a forensic audit on this job requisition to detect if it is a phantom/ghost posting, "
                    f"evergreen pipeline harvester, or genuine active opening.\n\n"
                    f"Company: {company}\nRole: {title}\nDays Active: {days_active}\n"
                    f"Description Excerpt:\n{desc[:1200]}\n\n"
                    f"Return valid JSON: {{\"is_ghost_job\": bool, \"real_hire_probability\": float (0.0 to 1.0), \"reasons\": [str]}}"
                )
                res = llm.generate_json(
                    prompt,
                    system="You are an expert technical talent intelligence auditor. Return ONLY a valid JSON object.",
                    max_tokens=250,
                    temperature=0.1
                )
                if isinstance(res, dict) and "real_hire_probability" in res:
                    real_hire_prob = float(res["real_hire_probability"])
                    if res.get("reasons"):
                        risk_factors.extend([f"AI Forensic: {r}" for r in res["reasons"][:3]])
            except Exception as e:
                logger.debug("ForensicFilter LLM pass skipped: %s", e)

        is_ghost = real_hire_prob < 0.40
        if real_hire_prob >= 0.75:
            tier = "VERIFIED_ACTIVE"
        elif real_hire_prob >= 0.40:
            tier = "SUSPICIOUS"
        else:
            tier = "CONFIRMED_GHOST"

        return ForensicAuditResult(
            job_id=job_id,
            company=company,
            title=title,
            is_ghost_job=is_ghost,
            real_hire_probability=round(real_hire_prob, 2),
            risk_factors=risk_factors,
            audit_tier=tier
        )

    def audit_posting(
        self,
        title: str,
        company: str,
        description: str,
        days_active: int = 0,
        repost_count: int = 0,
        use_llm: bool = True
    ) -> Any:
        """High-level audit helper used by API and tests."""
        job_dict = {
            "title": title,
            "company": company,
            "description": description,
            "days_active": days_active,
            "repost_count": repost_count
        }
        res = self.audit_job(job_dict, use_llm=use_llm)

        class _ForensicResponse:
            def __init__(self, is_ghost_job, hiring_intent_score, signals):
                self.is_ghost_job = is_ghost_job
                self.hiring_intent_score = hiring_intent_score
                self.signals = signals

        signals = [{"signal_type": "RISK_FACTOR", "description": rf} for rf in res.risk_factors]
        return _ForensicResponse(
            is_ghost_job=res.is_ghost_job,
            hiring_intent_score=res.real_hire_probability,
            signals=signals
        )
