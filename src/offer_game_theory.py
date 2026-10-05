"""Offer Game Theory & Multi-Pipeline Pacing Orchestrator.

Implements game-theoretic negotiation strategies for candidates with multiple concurrent opportunities:
- Pipeline Pacing Synchronizer (aligns interview timelines to force simultaneous offer windows).
- Compa-Ratio & Total Compensation (TC) Arbitrage (normalizing base, equity, bonus, and COL).
- BATNA (Best Alternative to a Negotiated Agreement) & Reservation Price calculation.
- Dynamic Counter-Anchor Generator & Deadline Extension scripts.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class OfferPackage:
    company: str
    stage: str  # "OFFER", "FINAL_ROUND", "TECH_SCREEN", "APPLIED"
    base_salary: float
    equity_annual_usd: float = 0.0
    signing_bonus: float = 0.0
    annual_bonus_target: float = 0.0
    location: str = "Remote"
    cost_of_living_index: float = 1.0  # SF/NYC = 1.35, Austin/Seattle = 1.1, Remote/Midwest = 1.0
    offer_deadline_iso: Optional[str] = None
    preference_rank: int = 1  # 1 = top choice

    @property
    def nominal_total_compensation(self) -> float:
        return self.base_salary + self.equity_annual_usd + self.signing_bonus + self.annual_bonus_target

    @property
    def col_adjusted_total_compensation(self) -> float:
        return round(self.nominal_total_compensation / max(0.5, self.cost_of_living_index), 2)


@dataclass
class PacingAction:
    company: str
    action_type: str  # "ACCELERATE", "STALL_EXTENSION", "HOLD_PATTERN", "ANCHOR_COUNTER"
    urgency: str      # "CRITICAL", "HIGH", "NORMAL"
    recommended_action: str
    email_template: str


@dataclass
class GameTheoryPlan:
    batna_company: Optional[str]
    batna_tc: float
    reservation_price: float
    highest_leverage_offer: Optional[str]
    pacing_actions: List[PacingAction]
    negotiation_recommendation: str


class OfferGameTheoryEngine:
    """Orchestrates multi-offer negotiation leverage and pipeline schedule alignment."""

    COL_BENCHMARKS = {
        "san francisco": 1.35,
        "new york": 1.35,
        "seattle": 1.15,
        "austin": 1.05,
        "boston": 1.15,
        "remote": 1.00,
        "london": 1.10,
        "toronto": 0.95,
        "india": 0.35,
        "berlin": 0.90,
    }

    def __init__(self, market_median_tc: float = 180000.0):
        self.market_median_tc = market_median_tc

    def get_col_index(self, location: str) -> float:
        loc = location.lower().strip()
        for k, v in self.COL_BENCHMARKS.items():
            if k in loc:
                return v
        return 1.0

    def calculate_compa_ratio(self, offered_salary: float, midpoint: Optional[float] = None) -> float:
        """Compa-Ratio = Offered Salary / Market Midpoint."""
        mid = midpoint or self.market_median_tc
        return round(offered_salary / max(1.0, mid), 3)

    def analyze_pipeline_pacing(self, packages: List[OfferPackage]) -> GameTheoryPlan:
        """Evaluate active pipelines and generate synchronized pacing actions."""
        if not packages:
            return GameTheoryPlan(
                batna_company=None,
                batna_tc=0.0,
                reservation_price=self.market_median_tc * 0.85,
                highest_leverage_offer=None,
                pacing_actions=[],
                negotiation_recommendation="No active pipelines to synchronize."
            )

        # Sort packages by COL-adjusted total compensation
        sorted_offers = sorted(packages, key=lambda p: p.col_adjusted_total_compensation, reverse=True)

        # Identify explicit active offers vs pending pipelines
        formal_offers = [p for p in sorted_offers if p.stage.upper() == "OFFER"]
        pending_pipelines = [p for p in sorted_offers if p.stage.upper() in ("FINAL_ROUND", "TECH_SCREEN")]

        batna_pkg = formal_offers[0] if formal_offers else (sorted_offers[0] if sorted_offers else None)
        batna_company = batna_pkg.company if batna_pkg else None
        batna_tc = batna_pkg.col_adjusted_total_compensation if batna_pkg else 0.0

        # Reservation price is 90% of BATNA or 80% of market median
        reservation_price = max(batna_tc * 0.90, self.market_median_tc * 0.80)

        pacing_actions: List[PacingAction] = []

        # Case 1: Active exploding offer exists while other companies are pending
        exploding_offers = [p for p in formal_offers if p.offer_deadline_iso]

        if exploding_offers and pending_pipelines:
            exp = exploding_offers[0]
            # 1. Action to pending companies: ACCELERATE
            for pending in pending_pipelines:
                pacing_actions.append(PacingAction(
                    company=pending.company,
                    action_type="ACCELERATE",
                    urgency="CRITICAL" if pending.preference_rank <= exp.preference_rank else "HIGH",
                    recommended_action=f"Inform {pending.company} recruiter of active offer deadline to compress remaining rounds.",
                    email_template=(
                        f"Hi [Recruiter Name],\n\n"
                        f"I wanted to share a quick scheduling update. I have received a formal offer with an expiration "
                        f"deadline of {exp.offer_deadline_iso}. Because {pending.company} remains one of my top choices due to "
                        f"[specific team/product reason], I would love to see if we could compress our remaining rounds or expedited "
                        f"team debrief before that date.\n\n"
                        f"Looking forward to finding a time that works.\n\nBest,\n[My Name]"
                    )
                ))

            # 2. Action to exploding offer company: STALL_EXTENSION
            pacing_actions.append(PacingAction(
                company=exp.company,
                action_type="STALL_EXTENSION",
                urgency="HIGH",
                recommended_action=f"Request a 5 to 7 day extension from {exp.company} to complete due diligence.",
                email_template=(
                    f"Hi [Recruiter Name],\n\n"
                    f"Thank you so much for extending this offer. I am genuinely thrilled about the opportunity at {exp.company}.\n\n"
                    f"Given the significance of this career decision and my commitment to giving this 100% focus, "
                    f"would it be possible to extend the decision deadline by a few business days? This will give me sufficient "
                    f"time to review health/equity details thoroughly and ensure everything is aligned for day one.\n\n"
                    f"Thank you for understanding,\n[My Name]"
                )
            ))

        # Case 2: Formal offer ready for counter-anchoring
        for off in formal_offers:
            compa = self.calculate_compa_ratio(off.nominal_total_compensation)
            # Anchor strategy: +12% to +18% based on leverage
            counter_target = round(off.nominal_total_compensation * (1.15 if batna_tc > 0 else 1.10), -3)

            pacing_actions.append(PacingAction(
                company=off.company,
                action_type="ANCHOR_COUNTER",
                urgency="NORMAL",
                recommended_action=f"Counter-anchor {off.company} at ${counter_target:,.0f} Total Comp (Compa-ratio: {compa}).",
                email_template=(
                    f"Hi [Recruiter Name],\n\n"
                    f"Thank you again for the offer to join {off.company}. The team and engineering scope are exceptional.\n\n"
                    f"After reviewing market benchmarks and my current competing considerations, I would be excited to sign "
                    f"immediately if we can bring the total compensation to ${counter_target:,.0f} (either through an increase in "
                    f"base salary to ${off.base_salary * 1.10:,.0f} or an adjusted signing/equity grant).\n\n"
                    f"I am ready to commit as soon as we can finalize these details.\n\nBest,\n[My Name]"
                )
            ))

        recommendation = (
            f"Highest leverage position is with {batna_company} ($ {batna_tc:,.0f} COL-adjusted TC). "
            f"Use this anchor to compress pending interviews while securing a safety extension on active deadlines."
        )

        return GameTheoryPlan(
            batna_company=batna_company,
            batna_tc=batna_tc,
            reservation_price=reservation_price,
            highest_leverage_offer=batna_company,
            pacing_actions=pacing_actions,
            negotiation_recommendation=recommendation
        )
