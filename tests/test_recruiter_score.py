"""Parametric tests for src/recruiter_score.

Follows the established matrix pattern (see tests/test_safe_selector.py):
- Build SAFE_CASES / UNDERWEIGHT_CASES / STRONG_CASES as module constants.
- One focused test_* function per behavioural guarantee.
- Pure functions, no fixtures, no fixture order dependency.
Goal: proves the rule-based scorer (a) clamps to score bounds, (b) rewards
real resumes, (c) recognises GitHub handles, (d) produces explainable
rationale entries.
"""
from src.recruiter_score import (
    score,
    MAX_FINAL_SCORE,
    MIN_FINAL_SCORE,
    MAX_BONUS_POINTS,
    MAX_DEDUCTION_POINTS,
    CATEGORIES,
)


EMPTY_INPUT = ""

WEAK_RESUME = (
    "Name: Test User\n"
    "Email: test@example.com\n"
)

# Has GitHub + quantified bullets + many production verbs + skills section
STRONG_RESUME = """
Name: Ada Lovelace
Email: ada@example.com
github.com/ada

SKILLS
Python, TypeScript, React, FastAPI, PostgreSQL, SQLite, Docker, Kubernetes,
Terraform, AWS, GCP, Azure, GraphQL, gRPC, Redis, Kaf

EXPERIENCE
- Led migration of monolith to microservices, reduced latency by 65%
- Built ML pipeline that shipped 3x faster, $4.2M annual savings
- Deployed 12 services, 99.99% uptime over 18 months
- Owned observability stack, increased MTTR by 40%
- Refactored auth system, reduced token-exchange time by 80%
- Automated deploy pipeline, shipped 200+ releases without rollback
- Mentored 6 engineers, 4 promoted to senior
- Optimized query planner, 10x throughput on hot path
- Architected multi-region failover, restored service in <90s
- Designed event-sourced ledger, 0 data-loss incidents

PROJECTS
- Open-source analytics SDK — 4.2k stars, 280+ contributors
- Personal search engine over 10M docs, 200ms p99 latency
- Realtime collaborative editor (CRDT), 500 concurrent users

EDUCATION
B.Sc Computer Science, MIT
""".strip()


# ---------------------------------------------------------------------------
# Bounds
# ---------------------------------------------------------------------------
def test_score_clamps_at_max_for_strong_resume():
    r = score(STRONG_RESUME, github_handle="ada", skills=[f"skill_{i}" for i in range(40)])
    assert r.total <= MAX_FINAL_SCORE, f"total {r.total} exceeds cap"


def test_score_clamps_at_min_for_empty_resume():
    r = score(EMPTY_INPUT, github_handle=None, skills=None)
    assert r.total >= MIN_FINAL_SCORE


def test_bonus_cannot_exceed_cap():
    r = score(STRONG_RESUME, github_handle="ada", skills=[f"x_{i}" for i in range(60)])
    assert r.bonus <= MAX_BONUS_POINTS


def test_deduction_cannot_exceed_cap_in_magnitude():
    r = score(EMPTY_INPUT, github_handle=None, skills=None)
    # deduction is stored as a non-positive int per implementation
    assert r.deduction >= -MAX_DEDUCTION_POINTS


# ---------------------------------------------------------------------------
# Rationale is explainable
# ---------------------------------------------------------------------------
def test_rationale_lists_each_rule_with_all_fields():
    r = score(STRONG_RESUME, github_handle="ada", skills=["python"])
    for item in r.rationale:
        assert "category" in item
        assert "rule" in item
        assert "delta" in item
        assert "note" in item
        assert isinstance(item["delta"], int)


def test_rationale_contains_github_handle_rule_when_handle_present():
    r = score(STRONG_RESUME, github_handle="ada", skills=["python"])
    assert any(rule["rule"] == "github_handle_present" for rule in r.rationale)


def test_rationale_contains_no_github_signal_rule_when_handle_missing():
    r = score(WEAK_RESUME, github_handle=None, skills=None)
    assert any(rule["rule"] == "no_github_signal" for rule in r.rationale)


# ---------------------------------------------------------------------------
# Category membership
# ---------------------------------------------------------------------------
def test_by_category_has_all_four_categories():
    r = score(STRONG_RESUME, github_handle="ada", skills=["python"])
    for cat in CATEGORIES:
        assert cat in r.by_category


def test_strong_resume_scores_higher_than_weak():
    strong = score(STRONG_RESUME, github_handle="ada", skills=["python"] * 15)
    weak = score(WEAK_RESUME, github_handle=None, skills=None)
    assert strong.total > weak.total


# ---------------------------------------------------------------------------
# Inspirer attribution
# ---------------------------------------------------------------------------
def test_inspiration_attributed_to_hiring_agent():
    r = score(STRONG_RESUME, github_handle="ada", skills=["python"])
    joined = " ".join([r.inspirer] + r.inspirations)
    assert "interviewstreet/hiring-agent" in joined or "hiring-agent" in joined
    assert "rule-based" in joined.lower() or "custom" in joined.lower()


# ---------------------------------------------------------------------------
# Pydantic-like to_dict shape
# ---------------------------------------------------------------------------
def test_to_dict_includes_total_and_rationale():
    r = score(STRONG_RESUME, github_handle="ada", skills=["python"])
    d = r.to_dict()
    assert "total" in d
    assert "by_category" in d
    assert "rationale" in d
    assert "bonus" in d
    assert "deduction" in d
