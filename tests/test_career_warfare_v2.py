"""Comprehensive Verification Suite for Career Warfare V2, Browser Agent, and Desktop Fallback."""
from pathlib import Path
import pytest
from unittest.mock import MagicMock, AsyncMock

from src.browser_agent import AutonomousBrowserAgent, BrowserAgentResult
from src.desktop_agent import DesktopComputerUseAgent
from src.career_agent import CareerAgentOrchestrator, CareerPipelineConfig
from src.forensic_filter import ForensicFilter
from src.trojan_horse import TrojanHorseEngine, ProblemSignature
from src.interview_hud import InterviewHUDEngine
from src.shadow_tournament import ShadowHiringTournament
from src.skill_scaffolder import SkillScaffolder
from src.telemetry_bandit import TelemetryEngine, LifecycleStage
from src.memory_graph import BitemporalMemoryGraph
from src.self_evolution import SelfEvolutionEngine


def test_browser_agent_structure():
    agent = AutonomousBrowserAgent(headless=True)
    assert agent.headless is True
    assert agent.user_data_dir is not None

    res = BrowserAgentResult(
        status="REVIEW_REQUIRED",
        url="https://example.com/apply",
        job_id=42,
        steps_executed=3,
        fields_filled=8,
        snapshot_summary="Form filled successfully"
    )
    assert res.status == "REVIEW_REQUIRED"
    assert res.fields_filled == 8


@pytest.mark.asyncio
async def test_browser_agent_captcha_and_login_detection():
    agent = AutonomousBrowserAgent(headless=True)
    mock_page = AsyncMock()

    # Mock captcha content
    mock_page.content.return_value = "<html><body>Please solve the cloudflare cf-turnstile challenge</body></html>"
    mock_page.frames = []
    assert await agent.detect_captcha(mock_page) is True

    # Mock clean content
    mock_page.content.return_value = "<html><body>Standard job form</body></html>"
    assert await agent.detect_captcha(mock_page) is False

    # Mock login url
    mock_page.url = "https://ats.workday.com/company/login?redirect=apply"
    mock_page.query_selector.return_value = None
    assert await agent.detect_login_wall(mock_page) is True


def test_desktop_agent_action_safety():
    agent = DesktopComputerUseAgent()
    # Test bounds checking
    res = agent.execute_action("click", x=999999, y=999999)
    assert res.success is False
    assert "bounds" in res.error.lower() or "unsupported" in res.error.lower()

    # Test key whitelist rejection
    res_bad_key = agent.execute_action("press_key", key="ctrl+alt+del")
    assert res_bad_key.success is False
    assert "not in allowed keys" in res_bad_key.error.lower() or "unsupported" in res_bad_key.error.lower()


def test_forensic_filter_audit():
    flt = ForensicFilter()
    # Test known bench pooling company
    verdict = flt.audit_job({
        "company": "Revature",
        "title": "Software Developer",
        "description": "Dynamic rockstar ninja team-player wearing many hats",
        "days_active": 120,
        "repost_count": 5
    }, use_llm=False)
    assert verdict.is_ghost_job is True
    assert verdict.audit_tier == "CONFIRMED_GHOST"
    assert len(verdict.risk_factors) >= 2


def test_trojan_horse_synthesis():
    engine = TrojanHorseEngine()
    prob = ProblemSignature(
        company="Stripe",
        target_repo="stripe/stripe-go",
        issue_title="Deadlock under concurrent webhook delivery",
        issue_description="Mutex lock contention causes worker starvation under 10k req/s",
        severity="CRITICAL",
        source_url="https://github.com/stripe/stripe-go/issues/100"
    )
    artifact = engine.synthesize_solution(prob, {"name": "Alex Vance", "skills": ["Go", "Distributed Systems"]}, use_llm=False)
    assert "RingBufferPool" in artifact.patch_code
    assert "Alex Vance" in artifact.executive_email_pitch
    assert artifact.estimated_conversion_rate > 0.5


def test_interview_hud_fast_classification():
    hud = InterviewHUDEngine()
    card_sys = hud.generate_hud_response("How would you design a distributed rate limiter with Redis?")
    assert card_sys.category == "SYSTEM_DESIGN"
    assert card_sys.architecture_snippet is not None
    assert len(card_sys.talking_points) >= 3

    card_star = hud.generate_hud_response("Tell me about a time you had a serious conflict with an engineering lead.")
    assert card_star.category == "BEHAVIORAL_STAR"
    assert len(card_star.pitfall_warnings) >= 1


def test_shadow_tournament_simulation():
    tournament = ShadowHiringTournament()
    result = tournament.simulate_tournament(
        job_description="Staff Backend Engineer with Raft consensus, distributed p99 latency optimization, and Kafka.",
        resume_text="Experienced systems engineer with Go, distributed systems, p99 latency profiling, and microservices.",
        simulations=10
    )
    assert result.win_rate > 0.5
    assert result.bayesian_prior_alpha > 1.0


def test_skill_scaffolder_catalog_and_arbitrary():
    scaffolder = SkillScaffolder()
    # Test cataloged skill
    bp_kafka = scaffolder.scaffold_project("kafka")
    assert bp_kafka.project_name == "event-stream-distributed-pipeline"
    assert any("producer.py" in f.relative_path for f in bp_kafka.files)

    # Test uncataloged skill
    bp_custom = scaffolder.scaffold_project("distributed-tracing")
    assert "distributed-tracing" in bp_custom.project_name
    assert len(bp_custom.files) >= 3


def test_telemetry_bandit_lifecycle():
    engine = TelemetryEngine()
    event = engine.record_transition(
        job_id=999,
        arm_id="perf",
        new_stage=LifecycleStage.SCREEN,
        previous_stage=LifecycleStage.SUBMITTED,
        notes="Recruiter phone screen scheduled"
    )
    assert event.new_stage == LifecycleStage.SCREEN
    assert engine.bandit.arms["perf"].conversions >= 1
    summary = engine.get_funnel_summary()
    assert "arms" in summary
    assert len(summary["arms"]) >= 4


def test_memory_graph_operations():
    graph = BitemporalMemoryGraph()
    # Add nodes
    graph.add_or_update_node("cand_test", "PERSON", "Candidate Test", {"title": "Staff Engineer"})
    graph.add_or_update_node("comp_test", "COMPANY", "TestCorp", {"industry": "Fintech"})
    # Add edge
    edge = graph.add_edge("cand_test", "comp_test", "INTERVIEWED_AT", {"round": "Final"})
    assert edge.relation == "INTERVIEWED_AT"

    # Query subgraph
    sub = graph.get_subgraph("cand_test", max_depth=1)
    assert len(sub["nodes"]) >= 2
    assert len(sub["edges"]) >= 1


def test_self_evolution_learning():
    evolution = SelfEvolutionEngine()
    # Record lesson
    lesson = evolution.record_lesson(
        trigger_source="PARSER_FAILURE",
        observation="Table layout in two-column resume caused text extraction truncation",
        root_cause="PDF parser lacks column-boundary flow heuristics",
        action_taken="Switched to single-column markdown normalized compilation"
    )
    assert lesson.lesson_id.startswith("les_")

    # AST verification
    valid, _ = evolution.verify_python_code_sandbox("def compute():\n    return 42 * 2\n")
    assert valid is True

    invalid, _ = evolution.verify_python_code_sandbox("def bad(:\n")
    assert invalid is False


@pytest.mark.asyncio
async def test_career_agent_pipeline_conservative():
    orchestrator = CareerAgentOrchestrator()
    sample_jobs = [
        {
            "id": 101,
            "company": "CloudFlow",
            "title": "Senior Systems Engineer",
            "url": "https://example.com/jobs/101",
            "description": "Looking for Go and distributed systems engineers with Kafka and low latency p99 optimization."
        },
        {
            "id": 102,
            "company": "Revature",
            "title": "Junior Associate",
            "url": "https://example.com/jobs/102",
            "description": "Dynamic team player synergy rockstar wearing many hats in fast paced environment."
        }
    ]

    profile = {
        "name": "Jordan Lee",
        "summary": "Distributed systems engineer with Go and Kafka experience.",
        "skills": ["Go", "Kafka", "Distributed Systems", "PostgreSQL"]
    }

    cfg = CareerPipelineConfig(
        mode="conservative",
        max_jobs_per_run=2,
        min_match_score=0.20,
        filter_ghost_jobs=True
    )

    summary = await orchestrator.run_pipeline(sample_jobs, profile, cfg)
    assert summary.total_jobs_evaluated == 2
    assert summary.jobs_passed_forensics == 1  # CloudFlow passed, Revature flagged as ghost
    assert len(summary.reports) == 2
    assert summary.reports[1].is_ghost_job is True
    assert summary.reports[0].navigation_status == "STAGED_CONSERVATIVE_MODE"


@pytest.mark.asyncio
async def test_browser_agent_async_form_fill():
    from unittest.mock import AsyncMock

    agent = AutonomousBrowserAgent(headless=True)
    mock_page = AsyncMock()
    mock_frame = MagicMock()
    mock_page.main_frame = mock_frame
    mock_frame.child_frames = []

    mock_el_fname = AsyncMock()
    mock_el_fname.is_visible = AsyncMock(return_value=True)
    mock_el_fname.is_enabled = AsyncMock(return_value=True)
    mock_el_fname.evaluate = AsyncMock(return_value="input")
    mock_el_fname.get_attribute = AsyncMock(side_effect=lambda attr: "first_name" if attr == "name" else ("text" if attr == "type" else None))

    mock_el_email = AsyncMock()
    mock_el_email.is_visible = AsyncMock(return_value=True)
    mock_el_email.is_enabled = AsyncMock(return_value=True)
    mock_el_email.evaluate = AsyncMock(return_value="input")
    mock_el_email.get_attribute = AsyncMock(side_effect=lambda attr: "email" if attr == "name" else ("email" if attr == "type" else None))

    mock_locator = MagicMock()
    mock_locator.all = AsyncMock(return_value=[mock_el_fname, mock_el_email])
    mock_frame.locator = MagicMock(return_value=mock_locator)

    fill_cfg = {
        "first_name": "Jordan",
        "email": "jordan@example.com"
    }
    fill_log = []
    filled = await agent._fill_page_async(mock_page, fill_cfg, fill_log)
    assert filled == 2
    assert len(fill_log) == 2
    mock_el_fname.fill.assert_awaited_once_with("Jordan")
    mock_el_email.fill.assert_awaited_once_with("jordan@example.com")


def test_stealth_browser_profile_isolation(tmp_path):
    from pathlib import Path
    from src.stealth_browser import _engine_profile_dir
    import os

    profile_dir = tmp_path / "bot_profile"
    engine_dir = _engine_profile_dir(profile_dir)
    assert f"worker_{os.getpid()}" in engine_dir
    assert Path(engine_dir).exists()

    # Simulate stale parent.lock left from dead process
    lock_file = Path(engine_dir) / "parent.lock"
    lock_file.write_text("locked", encoding="utf-8")
    assert lock_file.exists()

    # Next launch must clean stale lock
    _engine_profile_dir(profile_dir)
    assert not lock_file.exists()


def test_typst_direct_compilation(tmp_path):
    from src.cv_builder import render_typst_direct

    sample_typ = "= Jane Doe\nStaff Distributed Systems Engineer\n== Experience\n- Engineered Raft consensus"
    out_pdf = tmp_path / "test_resume.pdf"
    res = render_typst_direct(sample_typ, out_pdf)
    assert res is not None
    assert Path(res).exists()
    assert Path(res).stat().st_size > 1000


def test_agent_checkpointing():
    from src.career_agent import save_agent_checkpoint, get_agent_checkpoint

    test_run_id = "run_test_chk_123"
    save_agent_checkpoint(test_run_id, "TEST_STAGE", 4, {"status": "ok", "arm": "perf"})
    chk = get_agent_checkpoint(test_run_id, "TEST_STAGE")
    assert chk is not None
    assert chk["step_index"] == 4
    assert chk["state"]["arm"] == "perf"


def test_sqlite_fts5_bm25_search():
    from src.matcher import search_jobs_fts5

    results = search_jobs_fts5("distributed python", limit=5)
    assert isinstance(results, list)

