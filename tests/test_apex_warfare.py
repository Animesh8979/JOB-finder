"""Comprehensive Unit & Integration Test Suite for Apex Career Autonomous Warfare Engine.

Covers:
1. Jev System-1 Parallel Decision Primitives
2. Pre-Market Requisition Predictive Radar
3. Ghost Job & Hiring Intent Forensics
4. Adversarial Shadow Hiring Tournament
5. Proof-of-Value Trojan Horse Dispatch
6. ATS Reverse-Compiler & Extraction Fidelity Index (EFI)
7. Backchannel Pathfinder & Engineering Org Graph
8. 48-Hour Skill Scaffolder & Repository Generator
9. Telemetry Multi-Armed Bandit & Survival Analysis
10. Bitemporal Knowledge Graph & Memory Reconciliation
11. Multi-Pipeline Pacing & Offer Game Theory
12. Real-Time Interview Whisper HUD
13. Recursive Codebase Self-Evolution Engine
"""
from __future__ import annotations



def test_system_one_primitives():
    from src.system_one import get_system_one_engine

    engine = get_system_one_engine()
    query = "Senior Distributed Systems Engineer (Kafka, ClickHouse, Rust)"
    candidates = [
        "Frontend React Developer with CSS styling experience",
        "Staff Systems & Distributed Infrastructure Engineer (Kafka, Rust)",
        "Junior Marketing Data Analyst"
    ]

    choice = engine.choice(query, candidates)
    assert choice.selected == candidates[1]
    assert choice.index == 1
    assert choice.calibrated_p > 0.5
    assert choice.latency_ms >= 0.0

    score = engine.score(query, candidates[1])
    assert score.score > 0.5
    assert score.confidence > 0.5


def test_predictive_radar():
    from src.predictive_radar import PredictiveRadar

    radar = PredictiveRadar()
    signal = radar.analyze_premarket_signals(
        company_name="Vercel",
        sec_filings=[{"filing_date": "2026-08-15", "amount_raised_usd": 50000000}],
        github_signals=[{"repo": "turborepo", "tech_migrated_to": "Rust", "commit_date": "2026-08-20"}],
        exec_hires=[{"title": "VP of AI Infrastructure", "start_date": "2026-08-01"}]
    )

    assert signal.company == "Vercel"
    assert signal.overall_confidence > 0.6
    assert len(signal.signals) == 3
    assert len(signal.predicted_roles) > 0
    assert "2026" in signal.predicted_hiring_window


def test_forensic_filter():
    from src.forensic_filter import ForensicFilter

    filter_engine = ForensicFilter()

    # Test Ghost Job
    ghost_verdict = filter_engine.audit_posting(
        title="Senior Software Engineer",
        company="GhostVentures",
        description="Fast-paced dynamic environment looking for rockstar ninja developer to do everything.",
        days_active=120,
        repost_count=5
    )
    assert ghost_verdict.is_ghost_job is True
    assert ghost_verdict.hiring_intent_score < 0.6
    assert len(ghost_verdict.signals) > 0

    # Test Legitimate Job
    legit_verdict = filter_engine.audit_posting(
        title="Staff Backend Engineer",
        company="Stripe",
        description="Join the core ledger team to design idempotent transaction processing pipelines in Go and Kafka. Requirements: 5+ years distributed systems.",
        days_active=12,
        repost_count=0
    )
    assert legit_verdict.is_ghost_job is False
    assert legit_verdict.hiring_intent_score >= 0.7


def test_shadow_tournament():
    from src.shadow_tournament import ShadowHiringTournament

    tournament = ShadowHiringTournament()
    jd = "Required: Kubernetes, Go, Kafka, Distributed Systems. 5+ years experience."
    strong_resume = "Staff Software Engineer with 7 years architecting distributed stream processing using Go, Kafka, and Kubernetes. Handled 500k events/sec."

    result = tournament.simulate_tournament(job_description=jd, resume_text=strong_resume, simulations=20)

    assert result.total_simulations == 20
    assert result.win_rate > 0.5
    assert result.bayesian_prior_alpha > 1.0
    assert result.committee_breakdown["ats_pass_rate"] > 0.7


def test_trojan_horse():
    from src.trojan_horse import TrojanHorseEngine

    engine = TrojanHorseEngine()
    package = engine.synthesize_proof_of_value(
        target_company="Stripe",
        target_repo_or_product="stripe-python",
        candidate_skills=["Python", "Distributed Systems", "Rate Limiting"],
        known_issue="High lock contention during checkout spike"
    )

    assert package.target_company == "Stripe"
    assert "stripe-python" in package.target_repo
    assert len(package.pitch_memo) > 50
    assert len(package.solution_architecture) > 20
    assert len(package.pr_blueprint.title) > 0


def test_ats_reverse_compiler():
    from src.ats_reverse_compiler import ATSReverseCompiler

    compiler = ATSReverseCompiler()
    raw_resume = """Alex Mercer | alex@example.com | +1 (555) 123-4567 | github.com/alex
    SUMMARY
    Senior Distributed Systems Engineer specializing in high-throughput pipelines.
    EXPERIENCE
    Staff Systems Engineer - Acme Corp
    - Architected real-time event streaming pipeline processing 200k ops/sec.
    TECHNICAL SKILLS
    Python, Go, Kafka, Docker, Kubernetes
    EDUCATION
    BS Computer Science - MIT (2018)
    """

    score = compiler.audit_text_fidelity(
        extracted_text=raw_resume,
        expected_keywords=["python", "go", "kafka", "kubernetes"]
    )

    assert score.overall_efi >= 0.95
    assert score.contact_info_detected["email"] is True
    assert score.contact_info_detected["phone"] is True
    assert "experience" in score.detected_sections
    assert "skills" in score.detected_sections
    assert score.is_ats_safe is True


def test_backchannel_pathfinder():
    from src.backchannel_pathfinder import BackchannelPathfinder

    pathfinder = BackchannelPathfinder()
    emails = pathfinder.generate_email_permutations("alex", "mercer", "stripe.com")
    assert "alex.mercer@stripe.com" in emails
    assert "alex@stripe.com" in emails

    route = pathfinder.route_backchannel(
        company_name="Datadog",
        target_role="Staff Systems Engineer",
        domain="datadoghq.com",
        candidate_profile={"name": "Alex Mercer", "skills": ["Go", "Kafka"]},
        job_details={"company": "Datadog", "title": "Staff Systems Engineer"}
    )

    assert route.company == "Datadog"
    assert len(route.nodes) > 0
    assert route.primary_contact is not None
    assert len(route.memos) > 0
    assert route.warmth_score > 0.5


def test_skill_scaffolder(tmp_path):
    from src.skill_scaffolder import SkillScaffolder

    scaffolder = SkillScaffolder()
    gaps = scaffolder.analyze_skill_gaps(
        candidate_skills=["Python", "SQL"],
        target_jobs=[{"title": "Backend Lead", "description": "Looking for expertise in Kafka, Redis, and Kubernetes"}]
    )

    assert len(gaps) > 0
    assert any(g.skill_name == "kafka" for g in gaps)

    blueprint = scaffolder.scaffold_project("kafka", output_directory=tmp_path)
    assert blueprint.target_skill == "kafka"
    assert len(blueprint.files) >= 4
    assert (tmp_path / blueprint.project_name / "README.md").exists()
    assert (tmp_path / blueprint.project_name / "src" / "producer.py").exists()


def test_telemetry_bandit(tmp_path):
    from src.telemetry_bandit import TelemetryEngine, LifecycleStage

    db_file = tmp_path / "test_telemetry.db"
    engine = TelemetryEngine(db_path=db_file)

    # Initial arm selection
    selected_arm = engine.bandit.select_arm()
    assert selected_arm is not None

    # Record conversion event (success)
    evt = engine.record_transition(
        job_id=101,
        arm_id="perf",
        new_stage=LifecycleStage.SCREEN,
        previous_stage=LifecycleStage.SUBMITTED,
        days_elapsed=5.0
    )
    assert evt.new_stage == LifecycleStage.SCREEN
    assert engine.bandit.arms["perf"].conversions == 1
    assert engine.bandit.arms["perf"].alpha > 1.0

    funnel = engine.get_funnel_summary()
    assert len(funnel["arms"]) == 4
    assert funnel["median_survival_days"] > 0


def test_memory_graph(tmp_path):
    from src.memory_graph import BitemporalMemoryGraph

    db_file = tmp_path / "test_memory.db"
    graph = BitemporalMemoryGraph(db_path=db_file)

    # Add entity
    act1 = graph.add_or_update_node("comp_stripe", "COMPANY", "Stripe", {"primary_lang": "Ruby"})
    assert act1.action_type == "ADD"

    node = graph.get_active_node("comp_stripe")
    assert node is not None
    assert node.properties["primary_lang"] == "Ruby"

    # Update entity (bitemporal invalidation)
    act2 = graph.add_or_update_node("comp_stripe", "COMPANY", "Stripe", {"primary_lang": "Go"})
    assert act2.action_type == "UPDATE"

    # Add relationship
    graph.add_edge("cand_alex", "comp_stripe", "INTERVIEWED_AT")
    subgraph = graph.get_subgraph("cand_alex")
    assert len(subgraph["edges"]) == 1


def test_offer_game_theory():
    from src.offer_game_theory import OfferGameTheoryEngine, OfferPackage

    engine = OfferGameTheoryEngine()
    packages = [
        OfferPackage(
            company="Acme Corp",
            stage="OFFER",
            base_salary=180000,
            equity_annual_usd=40000,
            signing_bonus=20000,
            location="San Francisco",
            cost_of_living_index=1.35,
            offer_deadline_iso="2026-09-25",
            preference_rank=2
        ),
        OfferPackage(
            company="HyperScale AI",
            stage="FINAL_ROUND",
            base_salary=200000,
            equity_annual_usd=70000,
            signing_bonus=30000,
            location="Remote",
            cost_of_living_index=1.0,
            preference_rank=1
        )
    ]

    plan = engine.analyze_pipeline_pacing(packages)
    assert plan.batna_company == "Acme Corp"
    assert plan.batna_tc > 0
    assert len(plan.pacing_actions) > 0
    # Should have ACCELERATE for HyperScale and STALL for Acme
    action_types = {a.action_type for a in plan.pacing_actions}
    assert "ACCELERATE" in action_types
    assert "STALL_EXTENSION" in action_types


def test_interview_hud():
    from src.interview_hud import InterviewHUDEngine

    hud = InterviewHUDEngine()

    # System design query
    card1 = hud.generate_hud_response("How would you design a distributed rate limiter with Redis?")
    assert card1.category == "SYSTEM_DESIGN"
    assert card1.architecture_snippet is not None
    assert len(card1.talking_points) == 3

    # Behavioral query
    card2 = hud.generate_hud_response("Tell me about a time when you disagreed with a tech lead on architecture.")
    assert card2.category == "BEHAVIORAL_STAR"
    assert len(card2.pitfall_warnings) > 0


def test_self_evolution(tmp_path):
    from src.self_evolution import SelfEvolutionEngine

    engine = SelfEvolutionEngine()
    # Test valid python sandbox validation
    valid_code = "def add(a, b):\n    return a + b\n"
    is_valid, out = engine.verify_python_code_sandbox(valid_code)
    assert is_valid is True

    # Test invalid python syntax
    invalid_code = "def broken(\n"
    is_valid, out = engine.verify_python_code_sandbox(invalid_code)
    assert is_valid is False

    # Test dangerous code (eval)
    dangerous_code = "eval('1 + 1')"
    is_valid, out = engine.verify_python_code_sandbox(dangerous_code)
    assert is_valid is False

    # Record lesson
    lesson = engine.record_lesson(
        trigger_source="TELEMETRY",
        observation="Candidate conversion increased 35% with Systems Performance angle",
        root_cause="Recruiter rubrics heavily weight low-latency benchmarks",
        action_taken="Boosted perf arm prior in Thompson Sampling bandit"
    )
    assert lesson.lesson_id.startswith("les_")
