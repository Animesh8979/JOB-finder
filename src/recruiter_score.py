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
from typing import Optional

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
    deduction = max(-MAX_DEDUCTION_POINTS, min(0, deduction))
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
