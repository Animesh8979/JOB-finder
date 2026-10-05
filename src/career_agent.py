"""End-to-End Autonomous Career Warfare Orchestrator.

Unifies the full autonomous lifecycle into a cohesive, self-improving pipeline:
1. DISCOVERY: Scrapes target job boards and career pages via stealth HTTP and browser-use.
2. FORENSICS: Filters out ghost jobs, evergreen talent harvesters, and compliance traps.
3. SCORING & TRIAGE: Evaluates resume match using System-1 decision primitives.
4. TOURNAMENT & TAILORING: Simulates shadow hiring committee to pick optimal resume strategy.
5. AUTONOMOUS NAVIGATION: Discovers apply triggers, progresses through multi-page ATS wizards.
6. PRECISION FILLING: Maps candidate profile to form inputs via indexed LLM manifests.
7. DESKTOP FALLBACK: Handles OS-native file pickers or desktop auth popups if encountered.
8. TELEMETRY & MEMORY: Updates Thompson Sampling bandit priors, logs to bitemporal memory graph.
9. SELF-EVOLUTION: Derives persistent principles and evolves system heuristics from runtime outcomes.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import (
    config,
    db,
    llm,
    forensic_filter,
    shadow_tournament,
    browser_agent,
    desktop_agent,
    telemetry_bandit,
    memory_graph,
    self_evolution,
    system_one,
)

logger = logging.getLogger(__name__)


@dataclass
class CareerPipelineConfig:
    mode: str = "autonomous"  # "conservative" | "autonomous" | "full_auto"
    max_jobs_per_run: int = 5
    min_match_score: float = 0.60
    filter_ghost_jobs: bool = True
    enable_tournament: bool = True
    enable_desktop_fallback: bool = True


@dataclass
class JobPipelineReport:
    job_id: str
    company: str
    title: str
    url: str
    match_score: float
    is_ghost_job: bool
    selected_strategy_arm: str
    navigation_status: str
    fields_filled: int
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CareerRunSummary:
    run_id: str
    start_time: str
    end_time: str
    mode: str
    total_jobs_evaluated: int
    jobs_passed_forensics: int
    jobs_tailored: int
    applications_processed: int
    reports: List[JobPipelineReport] = field(default_factory=list)


class CareerAgentOrchestrator:
    """Master orchestrator driving the autonomous career progression cycle."""

    def __init__(self):
        self.forensics = forensic_filter.ForensicFilter()
        self.tournament = shadow_tournament.ShadowHiringTournament()
        self.browser = browser_agent.AutonomousBrowserAgent()
        self.desktop = desktop_agent.DesktopComputerUseAgent()
        self.telemetry = telemetry_bandit.TelemetryEngine()
        self.memory = memory_graph.BitemporalMemoryGraph()
        self.evolution = self_evolution.SelfEvolutionEngine()

    async def process_single_job(
        self,
        job: Dict[str, Any],
        profile_data: Dict[str, Any],
        cfg: CareerPipelineConfig
    ) -> JobPipelineReport:
        """Processes a single requisition through the complete 8-stage intelligence funnel."""
        job_id = str(job.get("id") or job.get("job_id") or "job_auto")
        company = str(job.get("company", "Target Company")).strip()
        title = str(job.get("title", "Software Engineer")).strip()
        url = str(job.get("url") or job.get("job_url") or "").strip()
        desc = str(job.get("description", ""))

        logger.info("CareerAgent: Evaluating %s at %s (%s)", title, company, url)

        # Stage 1: Forensic Ghost Job Audit
        is_ghost = False
        if cfg.filter_ghost_jobs and desc:
            verdict = self.forensics.audit_job(job, use_llm=False)
            is_ghost = verdict.is_ghost_job
            if is_ghost:
                logger.warning("Rejected phantom requisition: %s at %s", title, company)
                return JobPipelineReport(
                    job_id=job_id,
                    company=company,
                    title=title,
                    url=url,
                    match_score=verdict.real_hire_probability,
                    is_ghost_job=True,
                    selected_strategy_arm="none",
                    navigation_status="SKIPPED_GHOST_JOB",
                    fields_filled=0,
                    notes=f"Flagged as ghost/compliance posting: {', '.join(verdict.risk_factors)}"
                )

        # Stage 2: Match Scoring via System-1 Primitives
        s1 = system_one.get_system_one_engine()
        query_str = f"{title} {desc[:300]}"
        cand_str = f"{profile_data.get('name', '')} {profile_data.get('summary', '')} {' '.join(profile_data.get('skills', []))}"
        score_resp = s1.score(query_str, cand_str)
        match_score = score_resp.score

        if match_score < cfg.min_match_score:
            logger.info("Match score %s below threshold %s; skipping", match_score, cfg.min_match_score)
            return JobPipelineReport(
                job_id=job_id,
                company=company,
                title=title,
                url=url,
                match_score=match_score,
                is_ghost_job=False,
                selected_strategy_arm="none",
                navigation_status="SKIPPED_LOW_SCORE",
                fields_filled=0,
                notes=f"Match score {match_score} below minimum threshold {cfg.min_match_score}"
            )

        # Stage 3: Shadow Tournament Variant Selection
        selected_arm = "perf"
        if cfg.enable_tournament and desc:
            try:
                tourn_res = self.tournament.run_tournament(profile_data, desc, job_id=job_id, company=company)
                selected_arm = tourn_res.winning_arm_id
            except Exception as e:
                logger.debug("Tournament fallback to default arm: %s", e)

        # Stage 4: Ingest into Memory Graph
        try:
            self.memory.add_or_update_node(
                node_id=f"comp_{company.lower().replace(' ', '_')}",
                entity_type="COMPANY",
                name=company,
                properties={"last_seen_role": title, "url": url}
            )
            self.memory.add_edge(
                source_id=f"comp_{company.lower().replace(' ', '_')}",
                target_id=f"job_{job_id}",
                relation="HIRES_FOR",
                properties={"title": title, "match_score": match_score}
            )
        except Exception as e:
            logger.error("Memory graph ingestion error: %s", e)

        # If mode is conservative, stop before browser execution
        if cfg.mode == "conservative" or not url:
            return JobPipelineReport(
                job_id=job_id,
                company=company,
                title=title,
                url=url,
                match_score=match_score,
                is_ghost_job=False,
                selected_strategy_arm=selected_arm,
                navigation_status="STAGED_CONSERVATIVE_MODE",
                fields_filled=0,
                notes="Job evaluated and tailored; ready for manual review."
            )

        # Stage 5: Autonomous Browser Navigation & Form Fill
        auto_sub = (cfg.mode == "full_auto")
        try:
            numeric_job_id = int(job.get("id", 0)) if str(job.get("id", "")).isdigit() else None
        except Exception:
            numeric_job_id = None

        resume_path = profile_data.get("resume_path") or str(config.DATA_DIR / "resumes" / "resume.pdf")

        nav_res = await self.browser.navigate_and_apply(
            job_url=url,
            profile_data=profile_data,
            resume_pdf_path=resume_path if Path(resume_path).exists() else None,
            job_id=numeric_job_id,
            auto_submit=auto_sub
        )

        # Stage 6: Update Telemetry Bandit & Learn
        try:
            if numeric_job_id:
                stage = telemetry_bandit.LifecycleStage.SUBMITTED if auto_sub else telemetry_bandit.LifecycleStage.TAILORED
                self.telemetry.record_transition(
                    job_id=numeric_job_id,
                    arm_id=selected_arm,
                    new_stage=stage,
                    notes=f"Browser run status: {nav_res.status}"
                )
        except Exception as e:
            logger.error("Telemetry update error: %s", e)

        return JobPipelineReport(
            job_id=job_id,
            company=company,
            title=title,
            url=url,
            match_score=match_score,
            is_ghost_job=False,
            selected_strategy_arm=selected_arm,
            navigation_status=nav_res.status,
            fields_filled=nav_res.fields_filled,
            notes=nav_res.snapshot_summary
        )

    async def run_pipeline(
        self,
        jobs: List[Dict[str, Any]],
        profile_data: Dict[str, Any],
        config_override: Optional[CareerPipelineConfig] = None
    ) -> CareerRunSummary:
        """Executes the career pipeline across a batch of candidate requisitions."""
        import uuid
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        start_ts = datetime.now(timezone.utc).isoformat()
        cfg = config_override or CareerPipelineConfig()

        reports: List[JobPipelineReport] = []
        passed_forensics = 0
        tailored_count = 0
        applied_count = 0

        target_jobs = jobs[:cfg.max_jobs_per_run]
        for job in target_jobs:
            rep = await self.process_single_job(job, profile_data, cfg)
            reports.append(rep)
            if not rep.is_ghost_job:
                passed_forensics += 1
            if rep.selected_strategy_arm != "none":
                tailored_count += 1
            if rep.navigation_status in ("SUCCESS", "REVIEW_REQUIRED"):
                applied_count += 1

        # Check for autonomous self-evolution from telemetry
        try:
            funnel = self.telemetry.get_funnel_summary()
            self.evolution.auto_learn_from_bandit(funnel)
        except Exception as e:
            logger.error("Self-evolution auto-learning check failed: %s", e)

        end_ts = datetime.now(timezone.utc).isoformat()
        summary = CareerRunSummary(
            run_id=run_id,
            start_time=start_ts,
            end_time=end_ts,
            mode=cfg.mode,
            total_jobs_evaluated=len(target_jobs),
            jobs_passed_forensics=passed_forensics,
            jobs_tailored=tailored_count,
            applications_processed=applied_count,
            reports=reports
        )
        save_agent_checkpoint(run_id, "COMPLETED", len(target_jobs), {
            "mode": cfg.mode,
            "jobs_evaluated": len(target_jobs),
            "applications_processed": applied_count
        })
        return summary


def save_agent_checkpoint(run_id: str, stage: str, step_index: int, state_data: Dict[str, Any]) -> None:
    """Persist pipeline checkpoint into SQLite for sub-second pause/resume without state loss."""
    import json
    with db.get_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_checkpoints (
                run_id TEXT,
                stage TEXT,
                step_index INTEGER,
                state_data TEXT,
                updated_at REAL,
                PRIMARY KEY (run_id, stage)
            )
        """)
        cur.execute("""
            INSERT OR REPLACE INTO agent_checkpoints (run_id, stage, step_index, state_data, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (run_id, stage, step_index, json.dumps(state_data), time.time()))


def get_agent_checkpoint(run_id: str, stage: str) -> Optional[Dict[str, Any]]:
    """Retrieve saved pipeline checkpoint from SQLite."""
    import json
    with db.get_cursor() as cur:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agent_checkpoints'")
        if not cur.fetchone():
            return None
        cur.execute("SELECT step_index, state_data FROM agent_checkpoints WHERE run_id = ? AND stage = ?", (run_id, stage))
        row = cur.fetchone()
        if row:
            return {"step_index": row["step_index"], "state": json.loads(row["state_data"])}
        return None

