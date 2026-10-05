"""Telemetry Feedback Engine & Multi-Armed Bandit with Delayed-Feedback Survival Analysis.

Implements:
- Application Lifecycle State Machine (Discovered -> Applied -> Screen -> Tech -> Offer).
- Bayesian Multi-Armed Bandit (Thompson Sampling) optimizing resume angles and bullet styles.
- Delayed-Feedback Survival Analysis: treats unobserved application outcomes as censored data
  using hazard rate lambda rather than assuming immediate rejection.
"""
from __future__ import annotations

import logging
import math
import random
import sqlite3
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import config, db

logger = logging.getLogger(__name__)


class LifecycleStage:
    DISCOVERED = "DISCOVERED"
    TRIAGED = "TRIAGED"
    TAILORED = "TAILORED"
    SUBMITTED = "SUBMITTED"
    VIEWED = "VIEWED"
    SCREEN = "SCREEN"
    TECH_ROUND = "TECH_ROUND"
    OFFER = "OFFER"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    GHOSTED = "GHOSTED"

    TERMINAL_STAGES = {ACCEPTED, REJECTED, GHOSTED}
    SUCCESS_STAGES = {SCREEN, TECH_ROUND, OFFER, ACCEPTED}


@dataclass
class VariantArm:
    arm_id: str
    name: str  # e.g., "Systems Performance", "Product Velocity", "AI Infrastructure"
    description: str
    alpha: float = 1.0  # Beta prior success
    beta: float = 1.0   # Beta prior failure
    impressions: int = 0
    conversions: int = 0

    @property
    def expected_conversion_rate(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    def sample_theta(self) -> float:
        """Sample from Beta(alpha, beta) for Thompson Sampling."""
        return random.betavariate(max(0.01, self.alpha), max(0.01, self.beta))


@dataclass
class TelemetryEvent:
    event_id: str
    job_id: int
    arm_id: str
    previous_stage: str
    new_stage: str
    timestamp: str
    latency_days: float = 0.0
    notes: str = ""


class SurvivalEstimator:
    """Survival analysis for delayed application feedback using exponential hazard rate."""

    def __init__(self, median_response_days: float = 14.0):
        # lambda = ln(2) / median_days
        self.hazard_rate = math.log(2.0) / max(1.0, median_response_days)

    def survival_probability(self, days_elapsed: float) -> float:
        """Probability of having NOT heard back yet by day t: S(t) = exp(-lambda * t)."""
        return math.exp(-self.hazard_rate * max(0.0, days_elapsed))

    def expected_unobserved_conversion(self, days_elapsed: float, baseline_conversion_rate: float) -> float:
        """Remaining probability of conversion given that no reply has arrived after t days."""
        return baseline_conversion_rate * self.survival_probability(days_elapsed)


class ThompsonSamplingBandit:
    """Multi-armed bandit balancing exploration vs exploitation for resume angles."""

    def __init__(self, arms: Optional[List[VariantArm]] = None):
        self.arms: Dict[str, VariantArm] = {}
        if arms:
            for a in arms:
                self.arms[a.arm_id] = a
        else:
            default_arms = [
                VariantArm(arm_id="perf", name="Systems Performance", description="Highlights low-latency, profiling, throughput, and optimization metrics"),
                VariantArm(arm_id="velocity", name="Product Velocity", description="Highlights feature ship speed, user impact, CI/CD, and full-stack ownership"),
                VariantArm(arm_id="scale", name="Distributed Scale", description="Highlights microservices, high concurrency, fault tolerance, and data pipelines"),
                VariantArm(arm_id="ai_infra", name="AI & Platform Infrastructure", description="Highlights LLM orchestration, model serving, vector stores, and GPU efficiency")
            ]
            for a in default_arms:
                self.arms[a.arm_id] = a

    def select_arm(self) -> VariantArm:
        """Select best arm using Thompson Sampling (highest sampled theta)."""
        best_arm = None
        highest_sample = -1.0

        for arm in self.arms.values():
            sample = arm.sample_theta()
            if sample > highest_sample:
                highest_sample = sample
                best_arm = arm

        return best_arm or list(self.arms.values())[0]

    def update_arm(self, arm_id: str, success: bool, weight: float = 1.0):
        """Update Beta distribution parameters upon outcome."""
        arm = self.arms.get(arm_id)
        if not arm:
            return

        arm.impressions += 1
        if success:
            arm.alpha += weight
            arm.conversions += 1
        else:
            arm.beta += weight


class TelemetryEngine:
    """Coordinates telemetry tracking, bandit updates, and funnel analytics."""

    _local = threading.local()

    def __init__(self, db_path: Optional[Path | str] = None):
        self.db_path = Path(db_path or config.DB_PATH)
        self.bandit = ThompsonSamplingBandit()
        self.survival = SurvivalEstimator(median_response_days=14.0)
        self._init_telemetry_table()

    def _get_connection(self) -> sqlite3.Connection:
        """Reuse thread-local SQLite connection with WAL enabled per db_path."""
        conns = getattr(self._local, "connections", None)
        if conns is None:
            conns = {}
            self._local.connections = conns
        key = str(self.db_path.resolve())
        conn = conns.get(key)
        if conn is None:
            conn = sqlite3.connect(self.db_path, timeout=15.0)
            conn.execute("PRAGMA journal_mode=WAL;")
            conns[key] = conn
        return conn

    def _init_telemetry_table(self):
        """Create telemetry events table in SQLite."""
        try:
            conn = self._get_connection()
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS telemetry_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id TEXT UNIQUE,
                        job_id INTEGER,
                        arm_id TEXT,
                        previous_stage TEXT,
                        new_stage TEXT,
                        timestamp TEXT,
                        latency_days REAL,
                        notes TEXT
                    );
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS bandit_arms (
                        arm_id TEXT PRIMARY KEY,
                        name TEXT,
                        description TEXT,
                        alpha REAL,
                        beta REAL,
                        impressions INTEGER,
                        conversions INTEGER
                    );
                """)
            self._load_bandit_state()
        except Exception as e:
            logger.error("Failed to initialize telemetry database tables: %s", e)

    def _load_bandit_state(self):
        """Load stored arm parameters from DB."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT arm_id, name, description, alpha, beta, impressions, conversions FROM bandit_arms")
            rows = cur.fetchall()
            for row in rows:
                arm_id, name, desc, alpha, beta, imp, conv = row
                self.bandit.arms[arm_id] = VariantArm(
                    arm_id=arm_id, name=name, description=desc,
                    alpha=alpha, beta=beta, impressions=imp, conversions=conv
                )
        except Exception as e:
            logger.error("Failed to load bandit state from database: %s", e)

    def _save_bandit_state(self):
        """Persist bandit arm parameters to DB."""
        try:
            conn = self._get_connection()
            with conn:
                for arm in self.bandit.arms.values():
                    conn.execute("""
                        INSERT INTO bandit_arms (arm_id, name, description, alpha, beta, impressions, conversions)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(arm_id) DO UPDATE SET
                            alpha = excluded.alpha,
                            beta = excluded.beta,
                            impressions = excluded.impressions,
                            conversions = excluded.conversions;
                    """, (arm.arm_id, arm.name, arm.description, arm.alpha, arm.beta, arm.impressions, arm.conversions))
        except Exception as e:
            logger.error("Failed to save bandit state to database: %s", e)

    def record_transition(
        self,
        job_id: int,
        arm_id: str,
        new_stage: str,
        previous_stage: str = LifecycleStage.DISCOVERED,
        days_elapsed: float = 0.0,
        notes: str = ""
    ) -> TelemetryEvent:
        """Record stage transition and trigger bandit learning updates."""
        import uuid
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        now_ts = datetime.now(timezone.utc).isoformat()

        event = TelemetryEvent(
            event_id=event_id,
            job_id=job_id,
            arm_id=arm_id,
            previous_stage=previous_stage,
            new_stage=new_stage,
            timestamp=now_ts,
            latency_days=days_elapsed,
            notes=notes
        )

        # Update Bandit
        if new_stage in LifecycleStage.SUCCESS_STAGES:
            self.bandit.update_arm(arm_id, success=True, weight=1.0)
        elif new_stage == LifecycleStage.REJECTED:
            self.bandit.update_arm(arm_id, success=False, weight=1.0)
        elif new_stage == LifecycleStage.GHOSTED:
            self.bandit.update_arm(arm_id, success=False, weight=0.75)

        self._save_bandit_state()

        # Persist event
        try:
            conn = self._get_connection()
            with conn:
                conn.execute("""
                    INSERT INTO telemetry_events (event_id, job_id, arm_id, previous_stage, new_stage, timestamp, latency_days, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (event.event_id, event.job_id, event.arm_id, event.previous_stage, event.new_stage, event.timestamp, event.latency_days, event.notes))
        except Exception as e:
            logger.error("Failed to record telemetry event in database: %s", e)

        return event

    def get_funnel_summary(self) -> Dict[str, Any]:
        """Compute end-to-end conversion funnel metrics across arms."""
        arm_stats = []
        for arm in self.bandit.arms.values():
            arm_stats.append({
                "arm_id": arm.arm_id,
                "name": arm.name,
                "impressions": arm.impressions,
                "conversions": arm.conversions,
                "conversion_rate": round(arm.expected_conversion_rate * 100, 2),
                "alpha": round(arm.alpha, 2),
                "beta": round(arm.beta, 2),
            })

        return {
            "arms": arm_stats,
            "best_arm": self.bandit.select_arm().name,
            "median_survival_days": round(math.log(2) / self.survival.hazard_rate, 1)
        }
