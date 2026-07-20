"""Rule-based resume scorer inspired by HackerRank's interviewstreet/hiring-agent.

This is a STRUCTURAL PEER, not a port. Per project AOS discipline:
- Does not copy the HackerRank evaluators' Jinja prompts verbatim.
- Uses the SAME high-level rubric categories as the upstream taxonomy
  (open_source, self_projects, production, technical_skills), but the
  score composer is custom rule-based code against the resume's `raw_text`
  that the existing `profile_parser.py` already saves to `data/profiles/`.

No LLM is invoked at score time. The output is explainable per rule so a
candidate can see exactly which patterns cost or earned points.

Public API:
    score(text, *, github_handle=None, has_github_link=False, ...)
        -> ScoreReport dataclass-like dict

    rationale is a list of dicts: {"category","rule","delta","note"}.
    totals clamp to [MIN_FINAL_SCORE, MAX_FINAL_SCORE].
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Optional, Any
from datetime import datetime, timezone

# Same category taxonomy the upstream README documents
CATEGORIES = ("open_source", "self_projects", "production", "technical_skills")

MAX_FINAL_SCORE = 120
MIN_FINAL_SCORE = -20
MAX_BONUS_POINTS = 20
MAX_DEDUCTION_POINTS = 20


@dataclass
class ScoreReport:
    total: int
    by_category: dict[str, int] = field(default_factory=dict)
    bonus: int = 0
    deduction: int = 0
    rationale: list[dict] = field(default_factory=list)
    inspirations: list[str] = field(default_factory=list)
    inspirer: str = (
        "Inspired by HackerRank's open-source hiring-agent scoring taxonomy "
        "(github.com/interviewstreet/hiring-agent). Re-implemented locally "
        "as rule-based scoring — no LLM cost, no source-port attribution."
    )

    def to_dict(self) -> dict:
        d = asdict(self)
        d["inspirer"] = self.inspirer
        return d


_NUMERIC_BULLET_RE = re.compile(
    r"(?m)^\s*[-*+•]\s+.*\b("
    r"\d+\s*%|\d+\s*x|\d+\s*\+|\$[\d,.]+|\d{2,}\s*(users|customers|requests|sessions|maus|dau|qps|rps)|"
    r"reduced\s+by\s+\d+|increased\s+by\s+\d+|saved\s+\$?\d+"
    r")\b",
    re.IGNORECASE,
)
_SECTION_RE = re.compile(
    r"(?im)^\s*(skills?|technical\s+skills?|experience|work\s+experience|"
    r"projects?|education|certifications|awards|publications|summary|"
    r"open\s*source|github)\b"
)
_ACTION_VERB_RE = re.compile(
    r"\b("
    r"built|designed|led|shipped|launched|migrated|automated|optimized|"
    r"reduced|increased|owned|architected|deployed|mentored|refactored|"
    r"implemented|developed|engineered|delivered"
    r")\b",
    re.IGNORECASE,
)
_GITHUB_HANDLE_RE = re.compile(r"(?<!\w)github\.com/([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))", re.IGNORECASE)


def _clip(text: str, *, n: int = 4000) -> str:
    """Avoid pathological resumes overflowing the regex budget."""
    if not text:
        return ""
    return text[:n]


def _section_present(text: str, name: str) -> bool:
    rx = re.compile(rf"(?im)^\s*{re.escape(name)}\s*[:\-]?\s*$")
    return bool(rx.search(text))


def _count_action_verbs(text: str) -> int:
    return len(set(m.group(0).lower() for m in _ACTION_VERB_RE.finditer(text)))


def _count_numeric_bullets(text: str) -> int:
    return len(_NUMERIC_BULLET_RE.findall(text))


def _detect_github_handle(text: str) -> Optional[str]:
    m = _GITHUB_HANDLE_RE.search(text)
    return m.group(1).lower() if m else None


def score(
    raw_text: str,
    *,
    github_handle: Optional[str] = None,
    skills: Optional[list[str]] = None,
) -> ScoreReport:
    """Compute a rule-based score with explainable per-rule rationale.

    Args:
        raw_text: Full text of the parsed resume (already saved by
            `profile_parser.py` into `data/profiles/*.json`).
        github_handle: A GitHub handle, supplied either from the parsed
            profile's `links` field or as user input. If None, we try to
            sniff one from raw_text.
        skills: Extracted skills list — optional, used as a bonus signal.

    Returns:
        ScoreReport with category totals, bonus, deduction, and rationale.
    """
    text = _clip(raw_text or "")
    rationale: list[dict] = []
    by_category = {c: 0 for c in CATEGORIES}
    bonus = 0
    deduction = 0
    inspirations: list[str] = []

    handle = (github_handle or _detect_github_handle(text))
    has_github = bool(handle)

    # ---------------- open_source --------------------
    # Upstream weights GitHub signal + presence of "Open Source" section.
    if has_github:
        by_category["open_source"] += 10
        rationale.append({
            "category": "open_source",
            "rule": "github_handle_present",
            "delta": +10,
            "note": f"GitHub handle detected: @{handle}",
        })
    if _section_present(text, "open source") or _section_present(text, "open-source"):
        by_category["open_source"] += 5
        rationale.append({
            "category": "open_source",
            "rule": "open_source_section_present",
            "delta": +5,
            "note": "Dedicated 'Open Source' / 'Contributions' section found",
        })
    if not has_github and not _section_present(text, "open source"):
        deduction += 3
        rationale.append({
            "category": "open_source",
            "rule": "no_github_signal",
            "delta": -3,
            "note": "No GitHub handle and no open-source section — recruiters struggle to verify depth",
        })

    # ---------------- self_projects --------------------
    # Upstream rewards concrete projects with measurable outcomes.
    if _section_present(text, "projects") or _section_present(text, "project"):
        by_category["self_projects"] += 8
        rationale.append({
            "category": "self_projects",
            "rule": "projects_section_present",
            "delta": +8,
            "note": "Projects section present",
        })
    bullets_with_numbers = _count_numeric_bullets(text)
    if bullets_with_numbers >= 5:
        by_category["self_projects"] += 10
        rationale.append({
            "category": "self_projects",
            "rule": "quantified_outcomes_dense",
            "delta": +10,
            "note": f"{bullets_with_numbers} bullets contain quantified outcomes (%, x, $, MAU/DAU/QPS)",
        })
    elif bullets_with_numbers >= 2:
        by_category["self_projects"] += 5
        rationale.append({
            "category": "self_projects",
            "rule": "some_quantified_outcomes",
            "delta": +5,
            "note": f"{bullets_with_numbers} bullets contain quantified outcomes — add more for full credit",
        })
    else:
        deduction += 2
        rationale.append({
            "category": "self_projects",
            "rule": "no_quantified_outcomes",
            "delta": -2,
            "note": "Few or no bullets quantify outcomes (%, $, scale) — recruiters scan for impact",
        })

    # ---------------- production --------------------
    # Upstream rewards production-tense vocabulary: shipped, deployed, scaled.
    verbs = _count_action_verbs(text)
    if verbs >= 12:
        by_category["production"] += 15
        rationale.append({
            "category": "production",
            "rule": "production_verb_density_high",
            "delta": +15,
            "note": f"{verbs} distinct production verbs (shipped/deployed/scaled/optimized/etc.)",
        })
    elif verbs >= 7:
        by_category["production"] += 8
        rationale.append({
            "category": "production",
            "rule": "production_verb_density_mid",
            "delta": +8,
            "note": f"{verbs} distinct production verbs — adding a few more strengthens impact",
        })
    else:
        deduction += 3
        rationale.append({
            "category": "production",
            "rule": "production_verb_density_low",
            "delta": -3,
            "note": "Only " + str(verbs) + " production verbs — rewrite bullets as built/led/shipped/owned",
        })

    # ---------------- technical_skills --------------------
    if _section_present(text, "skills"):
        by_category["technical_skills"] += 8
        rationale.append({
            "category": "technical_skills",
            "rule": "skills_section_present",
            "delta": +8,
            "note": "Skills section present",
        })
    if skills:
        n = len({s.strip().lower() for s in skills if s and s.strip()})
        if n >= 15:
            by_category["technical_skills"] += 10
            rationale.append({
                "category": "technical_skills",
                "rule": "broad_skill_set",
                "delta": +10,
                "note": f"{n} distinct skills extracted",
            })
        elif n >= 8:
            by_category["technical_skills"] += 6
            rationale.append({
                "category": "technical_skills",
                "rule": "mid_skill_set",
                "delta": +6,
                "note": f"{n} distinct skills — consider grouping by domain",
            })
        elif n >= 3:
            by_category["technical_skills"] += 3
            rationale.append({
                "category": "technical_skills",
                "rule": "narrow_skill_set",
                "delta": +3,
                "note": f"{n} distinct skills — broaden for ATS keyword coverage",
            })
    if not _section_present(text, "skills"):
        deduction += 4
        rationale.append({
            "category": "technical_skills",
            "rule": "missing_skills_section",
            "delta": -4,
            "note": "No labelled 'Skills' section — ATS keyword scanners and recruiters both assume one",
        })

    # ---------------- bonuses --------------------
    if has_github and _section_present(text, "projects"):
        bonus += 5
        rationale.append({
            "category": "bonus",
            "rule": "github_plus_projects",
            "delta": +5,
            "note": "GitHub + Projects together signal verifiable work",
        })
    if _section_present(text, "education") or _section_present(text, "certifications"):
        bonus += 3
        rationale.append({
            "category": "bonus",
            "rule": "education_or_certifications",
            "delta": +3,
            "note": "Education / Certifications section present",
        })
    if _count_numeric_bullets(text) >= 8:
        bonus += 4
        rationale.append({
            "category": "bonus",
            "rule": "impact_metrics_dense",
            "delta": +4,
            "note": "Dense quantified outcomes across the resume",
        })
    if len(text) >= 1500:
        bonus += 2
        rationale.append({
            "category": "bonus",
            "rule": "resume_length_substantive",
            "delta": +2,
            "note": "Substantive resume length (≥1500 chars parsed) — not padded, but readable",
        })

    bonus = min(bonus, MAX_BONUS_POINTS)
    deduction = max(-MAX_DEDUCTION_POINTS, min(0, -deduction))
    cat_sum = sum(by_category.values())
    total = cat_sum + bonus + deduction
    total = max(MIN_FINAL_SCORE, min(MAX_FINAL_SCORE, total))

    inspirations.append(
        "Taxonomy mirrors interviewstreet/hiring-agent (open_source / self_projects / "
        "production / technical_skills + capped bonus/deduction). Scoring engine is "
        "fully custom rule-based — no upstream code or LLM."
    )

    return ScoreReport(
        total=total,
        by_category=by_category,
        bonus=bonus,
        deduction=deduction,
        rationale=rationale,
        inspirations=inspirations,
    )


@dataclass
class JobScoreReport:
    total: int
    breakdown: dict[str, Any]
    reasons: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)
    inspirations: list[str] = field(default_factory=list)
    evidence_snippets: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "breakdown": self.breakdown,
            "reasons": self.reasons,
            "red_flags": self.red_flags,
            "inspirations": self.inspirations,
            "evidence_snippets": self.evidence_snippets,
        }


def score_job(
    job: dict[str, Any],
    profile: dict[str, Any],
    prefs: Optional[dict[str, Any]] = None,
    dense_sim: float = 0.0,
    sparse_overlap: float = 0.0,
) -> JobScoreReport:
    """Compute explicit 0-100 categorical score breakdown for a job match.

    Breakdown categories and weights (sum = 100):
      - skills: max 30
      - role: max 20
      - seniority: max 20
      - location: max 15
      - salary: max 10
      - freshness: max 5
    """
    prefs = prefs or {}
    breakdown = {
        "skills": 0,
        "role": 0,
        "seniority": 0,
        "location": 0,
        "salary": 0,
        "freshness": 0,
    }
    reasons: list[str] = []
    red_flags: list[str] = []

    # --- 1. Skills (max 30) ---
    cand_skills = {s.strip().lower() for s in (profile.get("skills") or []) if s and s.strip()}
    summary_text = str(profile.get("summary") or profile.get("raw_text") or "").lower()
    for s in cand_skills:
        pass  # cand_skills set built

    job_text = f"{job.get('title', '')} {job.get('description', '')} {' '.join(job.get('tags') or [])}".lower()
    hits = sum(1 for s in cand_skills if s in job_text)
    keyword_score = min(30, int(hits * 6)) if cand_skills else 15
    sim_score = int(dense_sim * 30 + sparse_overlap * 15)
    breakdown["skills"] = min(30, max(keyword_score, sim_score))

    # --- 2. Role (max 20) ---
    job_title = str(job.get("title") or "").lower()
    target_titles = [str(t).lower().strip() for t in (prefs.get("titles") or []) if t]
    recent_roles = []
    for exp in (profile.get("experience") or []):
        if isinstance(exp, dict) and exp.get("title"):
            recent_roles.append(str(exp["title"]).lower())
        elif isinstance(exp, str):
            recent_roles.append(exp.lower())

    if any(t in job_title or job_title in t for t in target_titles + recent_roles if t):
        breakdown["role"] = 20
    elif any(k in job_title for k in ("engineer", "developer", "architect", "programmer", "scientist", "analyst")):
        breakdown["role"] = 15
    else:
        breakdown["role"] = 10

    # --- 3. Seniority (max 20) ---
    seniority_levels = {
        "intern": 0,
        "junior": 1,
        "mid": 2,
        "senior": 3,
        "lead": 4,
        "staff": 5,
        "principal": 6,
        "director": 7,
        "vp": 8,
    }
    job_level = 2
    for kw, lvl in seniority_levels.items():
        if re.search(rf"\b{kw}\b", job_title):
            job_level = lvl
            break

    cand_pref_level = prefs.get("seniority", "").lower()
    if cand_pref_level in seniority_levels:
        cand_level = seniority_levels[cand_pref_level]
    else:
        yrs = int(profile.get("years_experience") or 3)
        if yrs <= 1:
            cand_level = 1
        elif yrs <= 3:
            cand_level = 2
        elif yrs <= 6:
            cand_level = 3
        elif yrs <= 10:
            cand_level = 4
        else:
            cand_level = 5

    diff = abs(job_level - cand_level)
    if diff == 0:
        breakdown["seniority"] = 20
    elif diff == 1:
        breakdown["seniority"] = 14
    elif diff == 2:
        breakdown["seniority"] = 8
    else:
        breakdown["seniority"] = 3
        red_flags.append(f"Seniority mismatch (level {job_level} vs candidate level {cand_level})")

    # --- 4. Location (max 15) ---
    is_remote = bool(job.get("remote", 1)) or "remote" in job_title or "remote" in str(job.get("location", "")).lower()
    if is_remote:
        breakdown["location"] = 15
    elif prefs.get("remote_only"):
        breakdown["location"] = 0
        red_flags.append("Requires on-site/hybrid outside preferred remote setting")
    else:
        cand_loc = str(prefs.get("location") or profile.get("location") or "").lower()
        job_loc = str(job.get("location") or "").lower()
        if cand_loc and (cand_loc in job_loc or job_loc in cand_loc):
            breakdown["location"] = 15
        else:
            breakdown["location"] = 10

    # --- 5. Salary (max 10) ---
    min_sal = prefs.get("min_salary")
    sal_max = job.get("salary_max") or job.get("salary_min")
    if isinstance(min_sal, (int, float)) and min_sal > 0 and isinstance(sal_max, (int, float)) and sal_max > 0:
        if sal_max >= min_sal:
            breakdown["salary"] = 10
        else:
            breakdown["salary"] = 0
            red_flags.append(f"Salary maximum (${sal_max}) below candidate minimum (${min_sal})")
    else:
        breakdown["salary"] = 10

    # --- 6. Freshness (max 5) ---
    date_str = job.get("posted_at") or job.get("fetched_at")
    days_old = 1
    if date_str:
        try:
            dt = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            days_old = max(0, (datetime.now(timezone.utc) - dt).days)
        except Exception:
            days_old = 5
    if days_old <= 2:
        breakdown["freshness"] = 5
    elif days_old <= 7:
        breakdown["freshness"] = 4
    elif days_old <= 14:
        breakdown["freshness"] = 3
    elif days_old <= 30:
        breakdown["freshness"] = 2
    else:
        breakdown["freshness"] = 1

    total = sum(v for k, v in breakdown.items() if isinstance(v, (int, float)))
    total = max(0, min(100, int(total)))

    evidence_snippets = []
    desc_text = str(job.get("description") or "")
    if desc_text and cand_skills:
        clauses = re.split(r'[.!?\n]+', desc_text)
        for clause in clauses:
            cleaned = clause.strip()
            if len(cleaned) < 15 or len(cleaned) > 250:
                continue
            cleaned_lower = cleaned.lower()
            matching_sk = [sk for sk in cand_skills if sk in cleaned_lower and len(sk) >= 3]
            if matching_sk:
                evidence_snippets.append(f'"{cleaned}" (matched: {", ".join(matching_sk[:2])})')
                if len(evidence_snippets) >= 3:
                    break

    breakdown["evidence_snippets"] = evidence_snippets

    if hits > 0:
        reasons.append(f"Matched {hits} key skills with {breakdown['role']}/20 role alignment")
    else:
        reasons.append(f"Fit score {total}/100 based on role and seniority compatibility")

    return JobScoreReport(
        total=total,
        breakdown=breakdown,
        reasons=reasons,
        red_flags=red_flags,
        inspirations=["Deterministic rubric evaluation for explicit 0-100 categorical breakdown."],
        evidence_snippets=evidence_snippets,
    )
