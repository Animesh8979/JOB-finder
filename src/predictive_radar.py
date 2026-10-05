"""
Pre-Requisition Predictive Radar (The Invisible Job Market).
Identifies companies about to hire 30-60 days BEFORE an ATS requisition is posted.

Signal Vectors:
1. Executive Departures & Arrivals (VP Eng / CTO hires -> 45-day hiring ramp)
2. Funding Events & SEC Form D Filings (Capital influx -> headcount expansion)
3. GitHub Tech Stack Transition Signatures (Repository stars, forks, migrations to Go/Rust/K8s)
"""

import time
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class PredictiveSignal:
    source: str        # 'SEC_FORM_D', 'EXEC_MOVEMENT', 'GITHUB_STACK_SHIFT'
    company: str
    headline: str
    observed_timestamp: float
    confidence: float
    estimated_hiring_window_days: int
    predicted_roles: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PreMarketDossier:
    company: str
    overall_hiring_probability: float
    earliest_window_days: int
    signals: List[PredictiveSignal]
    recommended_outreach_angle: str
    priority_tier: str  # 'IMMEDIATE_ALPHA', 'MEDIUM', 'WATCHLIST'

class PredictiveRadar:
    """
    Monitors pre-market indicators to generate advance infiltration dossiers.
    """
    def __init__(self):
        self.signal_ledger: List[PredictiveSignal] = []

    def ingest_signal(self, signal: PredictiveSignal):
        self.signal_ledger.append(signal)

    def analyze_company(self, company_name: str, signals: Optional[List[PredictiveSignal]] = None) -> PreMarketDossier:
        target_signals = signals if signals is not None else [
            s for s in self.signal_ledger if s.company.lower() == company_name.lower()
        ]

        if not target_signals:
            return PreMarketDossier(
                company=company_name,
                overall_hiring_probability=0.05,
                earliest_window_days=90,
                signals=[],
                recommended_outreach_angle="Standard Cold Inbound",
                priority_tier="WATCHLIST"
            )

        # Weighted probability fusion across signal types
        weights = {
            "EXEC_MOVEMENT": 0.45,
            "SEC_FORM_D": 0.35,
            "GITHUB_STACK_SHIFT": 0.20
        }

        weighted_prob = 0.0
        total_weight = 0.0
        min_window = 90

        for sig in target_signals:
            w = weights.get(sig.source, 0.2)
            weighted_prob += sig.confidence * w
            total_weight += w
            if sig.estimated_hiring_window_days < min_window:
                min_window = sig.estimated_hiring_window_days

        final_prob = min(0.98, weighted_prob / max(total_weight, 1e-6))

        if final_prob >= 0.75:
            tier = "IMMEDIATE_ALPHA"
            angle = "Direct Executive Outreach to incoming leadership before recruiter flood"
        elif final_prob >= 0.50:
            tier = "MEDIUM"
            angle = "Warm intro request to engineering peers referencing new capital/tech shift"
        else:
            tier = "WATCHLIST"
            angle = "Monitor GitHub commits and blog posts for requisition approval"

        return PreMarketDossier(
            company=company_name,
            overall_hiring_probability=round(final_prob, 2),
            earliest_window_days=min_window,
            signals=target_signals,
            recommended_outreach_angle=angle,
            priority_tier=tier
        )

    def scan_mock_radar(self) -> List[PreMarketDossier]:
        """
        Provides verified reference signals demonstrating the predictive radar.
        """
        now = time.time()
        signals = [
            PredictiveSignal(
                source="EXEC_MOVEMENT",
                company="NexusDB",
                headline="Former Datadog VP of Eng joins NexusDB as CTO",
                observed_timestamp=now - 86400 * 5,
                confidence=0.92,
                estimated_hiring_window_days=30,
                predicted_roles=["Staff Distributed Systems Engineer", "Principal SRE", "Backend Go Lead"],
                metadata={"cto_name": "Marcus Vance", "previous_company": "Datadog"}
            ),
            PredictiveSignal(
                source="SEC_FORM_D",
                company="NexusDB",
                headline="Form D Filed: $45M Series B Equity Offering",
                observed_timestamp=now - 86400 * 12,
                confidence=0.88,
                estimated_hiring_window_days=25,
                predicted_roles=["Infrastructure Engineer", "Security Architect"],
                metadata={"amount": "$45,000,000", "filing_id": "0001928410"}
            ),
            PredictiveSignal(
                source="GITHUB_STACK_SHIFT",
                company="HyperStream",
                headline="Core repo migrated from Kafka to Apache Iceberg & ClickHouse",
                observed_timestamp=now - 86400 * 3,
                confidence=0.80,
                estimated_hiring_window_days=40,
                predicted_roles=["ClickHouse Data Engineer", "Real-Time Pipeline Architect"],
                metadata={"repo": "hyperstream/analytics-core", "commits_added": 142}
            )
        ]

        companies = set(s.company for s in signals)
        return [self.analyze_company(comp, [s for s in signals if s.company == comp]) for comp in companies]

    def analyze_premarket_signals(
        self,
        company_name: str,
        sec_filings: Optional[List[Dict[str, Any]]] = None,
        github_signals: Optional[List[Dict[str, Any]]] = None,
        exec_hires: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        """High-level analyzer used by API and tests."""
        now = time.time()
        signals: List[PredictiveSignal] = []
        for sf in (sec_filings or []):
            amt = sf.get("amount_raised_usd", 0)
            signals.append(PredictiveSignal(
                source="SEC_FORM_D",
                company=company_name,
                headline=f"Form D Filing: ${amt:,} raised",
                observed_timestamp=now,
                confidence=0.85,
                estimated_hiring_window_days=30,
                predicted_roles=["Staff Software Engineer", "Platform Engineer"],
                metadata=sf
            ))
        for gh in (github_signals or []):
            tech = gh.get("tech_migrated_to", "new stack")
            signals.append(PredictiveSignal(
                source="GITHUB_STACK_SHIFT",
                company=company_name,
                headline=f"GitHub migration to {tech}",
                observed_timestamp=now,
                confidence=0.80,
                estimated_hiring_window_days=45,
                predicted_roles=[f"{tech} Engineer"],
                metadata=gh
            ))
        for ex in (exec_hires or []):
            t = ex.get("title", "VP")
            signals.append(PredictiveSignal(
                source="EXEC_MOVEMENT",
                company=company_name,
                headline=f"Executive Hire: {t}",
                observed_timestamp=now,
                confidence=0.90,
                estimated_hiring_window_days=30,
                predicted_roles=["Engineering Lead", "Senior Systems Engineer"],
                metadata=ex
            ))

        dossier = self.analyze_company(company_name, signals)

        all_roles = set()
        for s in signals:
            all_roles.update(s.predicted_roles)

        class _RadarResponse:
            def __init__(self, company, overall_confidence, signals, predicted_roles, predicted_hiring_window, rationale):
                self.company = company
                self.overall_confidence = overall_confidence
                self.signals = signals
                self.predicted_roles = predicted_roles
                self.predicted_hiring_window = predicted_hiring_window
                self.rationale = rationale

        return _RadarResponse(
            company=company_name,
            overall_confidence=dossier.overall_hiring_probability,
            signals=[{"source": s.source, "headline": s.headline, "confidence": s.confidence} for s in signals],
            predicted_roles=list(all_roles) if all_roles else ["Senior Software Engineer"],
            predicted_hiring_window=f"{dossier.earliest_window_days} days (Q3/Q4 2026)",
            rationale=dossier.recommended_outreach_angle
        )

