"""Parametric test suite for Career Intelligence OS modules."""
from __future__ import annotations

import pytest
from src.ats_simulator import simulate_adversarial_ats, _extract_ngrams
from src.salary_arbitrage import calculate_compa_ratio, get_market_benchmark
from src.sources import ashby, greenhouse, lever


# --- 1. Adversarial ATS Simulator Tests ---

def test_ats_simulator_knockout_detection():
    """Verify that hard knockout disqualifiers are detected and penalize survival score."""
    jd = (
        "We are hiring a Principal Systems Architect. "
        "Candidate MUST hold an Active Security Clearance (TS/SCI required). "
        "15+ years of experience required."
    )
    res = (
        "Experienced Principal Systems Architect with 8 years building cloud backends. "
        "Expert in Go, Rust, and Distributed Systems."
    )
    result = simulate_adversarial_ats(jd, res)

    assert len(result["hard_disqualifiers"]) >= 1
    assert any("Security Clearance" in dq for dq in result["hard_disqualifiers"])
    # Survival probability drops drastically when hard knockout is tripped
    assert result["survival_score"] <= 40


def test_ats_simulator_keyword_coverage_and_verbs():
    """Verify keyword extraction, matching, and action verb quantification."""
    jd = (
        "Looking for a Backend Engineer with expertise in Python, FastAPI, Docker, and PostgreSQL. "
        "Responsible for scaling microservices and designing relational schemas."
    )
    res = (
        "Backend Engineer who engineered and scaled microservices using Python and FastAPI. "
        "Architected PostgreSQL databases, optimizing query latency by 45% across 20M requests."
    )
    result = simulate_adversarial_ats(jd, res)

    assert "python" in result["matched_ngrams"]
    assert "fastapi" in result["matched_ngrams"]
    assert "postgresql" in result["matched_ngrams"]
    assert result["metric_quantifier_count"] >= 1  # 45% or 20M
    assert "scaled" in result["strong_verbs_found"] or "engineered" in result["strong_verbs_found"]
    assert result["survival_score"] >= 40
    assert result["keyword_coverage_pct"] >= 30


def test_ats_simulator_empty_graceful():
    """Verify graceful fallback on empty strings."""
    result = simulate_adversarial_ats("", "")
    assert result["survival_score"] == 0
    assert result["hard_disqualifiers"] == []


# --- 2. Salary Compa-Ratio & Arbitrage Tests ---

def test_compa_ratio_under_market():
    """Verify Compa-Ratio calculation and tactical leverage advice when offer is below market."""
    res = calculate_compa_ratio(
        salary_min=130000,
        salary_max=150000,
        job_title="Senior Software Engineer",
        location="Remote"
    )
    assert res["has_compensation"] is True
    assert res["offered_midpoint"] == 140000
    assert res["market_midpoint"] == 185000
    # 140000 / 185000 = ~75.7%
    assert res["compa_ratio"] < 80.0
    assert "Below Market" in res["market_tier"]
    assert res["geo_arbitrage_multiplier"] > 1.0


def test_compa_ratio_above_market():
    """Verify Compa-Ratio calculation when offer is at top of market."""
    res = calculate_compa_ratio(
        salary_min=240000,
        salary_max=280000,
        job_title="Senior Software Engineer",
        location="San Francisco, CA"
    )
    assert res["has_compensation"] is True
    assert res["offered_midpoint"] == 260000
    assert res["compa_ratio"] > 120.0
    assert "Above Market" in res["market_tier"] or "Top of Market" in res["market_tier"]


def test_compa_ratio_unlisted():
    """Verify graceful handling when salary band is not listed."""
    res = calculate_compa_ratio(
        salary_min=None,
        salary_max=None,
        job_title="Staff Engineer",
        location="Remote"
    )
    assert res["has_compensation"] is False
    assert res["compa_ratio"] is None
    assert res["market_midpoint"] == 240000


# --- 3. Direct First-Party ATS Ingestion Tests ---

def test_ashby_default_boards_configured():
    """Ensure default Ashby board pool is non-empty and accessible."""
    assert len(ashby.DEFAULT_ASHBY_BOARDS) >= 5
    assert "linear" in ashby.DEFAULT_ASHBY_BOARDS


def test_greenhouse_default_boards_configured():
    """Ensure default Greenhouse board pool is non-empty and accessible."""
    assert len(greenhouse.DEFAULT_GREENHOUSE_BOARDS) >= 5
    assert "stripe" in greenhouse.DEFAULT_GREENHOUSE_BOARDS


def test_lever_default_boards_configured():
    """Ensure default Lever board pool is non-empty and accessible."""
    assert len(lever.DEFAULT_LEVER_BOARDS) >= 3
    assert "spotify" in lever.DEFAULT_LEVER_BOARDS
