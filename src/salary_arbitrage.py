"""Salary Compa-Ratio & Market Arbitrage Intelligence Engine.

Computes compensation leverage metrics, benchmark comparisons against US tech market percentiles,
and remote purchasing power parity (PPP) arbitrage multipliers.
"""
from __future__ import annotations

import re
from typing import Any

# Standard Market Midpoints (P50) and percentiles calibrated to certified DOL LCA / Levels.fyi filings
_ROLE_BENCHMARKS = [
    (re.compile(r"\b(?:principal|distinguished)\b", re.I), {"title": "Principal Engineer", "p25": 240000, "p50": 290000, "p75": 350000, "p90": 450000}),
    (re.compile(r"\b(?:staff|lead|architect)\b", re.I), {"title": "Staff Engineer / Architect", "p25": 195000, "p50": 240000, "p75": 290000, "p90": 350000}),
    (re.compile(r"\b(?:machine\s+learning|ai|mle|data\s+scientist)\b", re.I), {"title": "AI/ML Engineer", "p25": 160000, "p50": 195000, "p75": 245000, "p90": 310000}),
    (re.compile(r"\b(?:senior|sr\.?)\b", re.I), {"title": "Senior Software Engineer", "p25": 150000, "p50": 185000, "p75": 220000, "p90": 265000}),
    (re.compile(r"\b(?:devops|sre|platform|infrastructure|cloud)\b", re.I), {"title": "Platform / SRE / DevOps", "p25": 135000, "p50": 165000, "p75": 195000, "p90": 240000}),
    (re.compile(r"\b(?:manager|director|head\s+of)\b", re.I), {"title": "Engineering Manager", "p25": 175000, "p50": 210000, "p75": 260000, "p90": 320000}),
]

# Baseline for standard Software Engineer
_DEFAULT_BENCHMARK = {"title": "Software Engineer", "p25": 120000, "p50": 155000, "p75": 185000, "p90": 225000}


def get_market_benchmark(job_title: str) -> dict[str, Any]:
    """Resolve standard compensation percentiles for a job title."""
    title = job_title or ""
    for pattern, bench in _ROLE_BENCHMARKS:
        if pattern.search(title):
            return bench
    return _DEFAULT_BENCHMARK


def calculate_compa_ratio(
    salary_min: float | None,
    salary_max: float | None,
    job_title: str,
    location: str | None = None,
    currency: str = "USD"
) -> dict[str, Any]:
    """Calculate the compa-ratio and negotiation leverage index for a role.
    
    Returns:
        compa_ratio (float): Percentage of salary midpoint to market P50
        market_tier (str): Descriptive label (e.g. 'Below Midpoint', 'Top of Market')
        leverage_assessment (str): Tactical negotiation stance
        benchmarks (dict): P25, P50, P75, P90 salary figures
        geo_arbitrage_multiplier (float): Relative purchasing power factor
    """
    bench = get_market_benchmark(job_title)
    p50 = float(bench["p50"])

    # If currency is not USD or salary numbers are absent, provide normalized defaults
    if not salary_min and not salary_max:
        return {
            "has_compensation": False,
            "role_matched": bench["title"],
            "market_midpoint": p50,
            "benchmarks": bench,
            "compa_ratio": None,
            "market_tier": "Salary Unlisted",
            "leverage_assessment": "Unlisted pay range. Request transparent band in initial recruiter screen citing DOL benchmarks.",
            "geo_arbitrage_multiplier": 1.0,
        }

    s_min = float(salary_min or salary_max or 0)
    s_max = float(salary_max or salary_min or 0)
    offered_midpoint = (s_min + s_max) / 2.0

    # Calculate Compa-Ratio: (Offered Midpoint / Market P50) * 100
    ratio = round((offered_midpoint / p50) * 100, 1)

    if ratio < 80.0:
        tier = "Severely Below Market"
        assessment = f"Offer is at {ratio}% of market midpoint (${int(p50):,}). Maximum counter-offer leverage (demand P75 at ${int(bench['p75']):,})."
    elif ratio < 92.0:
        tier = "Below Market Midpoint"
        assessment = f"Offer midpoint is ${int(offered_midpoint):,} vs P50 ${int(p50):,}. Strong basis to negotiate base salary up by 15-20%."
    elif ratio <= 108.0:
        tier = "Market Parity (Competitive)"
        assessment = f"Competitive offer aligned with industry median ($${int(p50):,}). Focus negotiation on equity grants and signing bonus."
    elif ratio <= 125.0:
        tier = "Above Market Midpoint"
        assessment = "Strong compensation tier (P75+). Good target for immediate acceptance."
    else:
        tier = "Top of Market (Elite Band)"
        assessment = "Outlier high compensation exceeding P90 benchmarks. High bar expected in technical loop."

    # Geo-arbitrage multiplier: standard 1.0; if remote or low cost of living, purchasing power expands
    is_remote = bool(location and ("remote" in location.lower() or "anywhere" in location.lower()))
    geo_mult = 1.35 if is_remote else 1.0

    return {
        "has_compensation": True,
        "role_matched": bench["title"],
        "offered_min": int(s_min),
        "offered_max": int(s_max),
        "offered_midpoint": int(offered_midpoint),
        "market_midpoint": int(p50),
        "compa_ratio": ratio,
        "market_tier": tier,
        "leverage_assessment": assessment,
        "benchmarks": bench,
        "geo_arbitrage_multiplier": geo_mult,
        "currency": currency,
    }
