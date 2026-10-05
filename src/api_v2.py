"""api_v2: Versioned API contract (/api/v2) with strict Pydantic views and SSE stream.

Supports unified Command Center operations with durable run tracking.
"""
from __future__ import annotations

import json
from typing import Any
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from . import db
from .run_manager import get_run_manager

router = APIRouter(prefix="/api/v2", tags=["v2"])

# --- Pydantic Models ---------------------------------------------------------
class SearchIntent(BaseModel):
    query: str = Field(..., description="Job search keywords or title")
    location: str | None = Field(None, description="Preferred location")
    remote_only: bool = Field(True, description="Filter for remote jobs")
    sources: list[str] = Field(default_factory=list, description="Target job sources (e.g. ['remoteok', 'arbeitnow'])")
    auto_apply: bool = Field(False, description="Whether to auto-stage application after scoring")

class JobView(BaseModel):
    id: int
    title: str
    company: str
    location: str | None = None
    remote: bool = True
    url: str | None = None
    apply_url: str | None = None
    description: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str | None = None
    posted_at: str | None = None
    match_score: int | None = None
    match_reason: str | None = None
    # Stored shape comes from recruiter_score.JobScoreReport.to_dict():
    # {total:int, breakdown:dict, reasons:[str], red_flags:[str],
    #  inspirations:[str], evidence_snippets:[str]} — hence Any, not int.
    match_breakdown: dict[str, Any] | None = None
    red_flags: list[str] | None = None
    status: str = "Saved"

class RunView(BaseModel):
    run_id: str
    kind: str
    status: str
    phase: str | None = None
    progress_current: int = 0
    progress_total: int = 100
    message: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    result_json: Any = None
    error_message: str | None = None

class AuditRequest(BaseModel):
    profile: dict[str, Any] = Field(default_factory=dict)
    prefs: dict[str, Any] = Field(default_factory=dict)

# --- Helper to convert raw DB run to RunView ---------------------------------
def _to_run_view(run_dict: dict[str, Any]) -> RunView:
    res_json = run_dict.get("result_json")
    if isinstance(res_json, str):
        try:
            res_json = json.loads(res_json)
        except Exception:
            pass
    return RunView(
        run_id=run_dict["run_id"],
        kind=run_dict["kind"],
        status=run_dict["status"],
        phase=run_dict.get("phase"),
        progress_current=run_dict.get("progress_current") or 0,
        progress_total=run_dict.get("progress_total") or 100,
        message=run_dict.get("message"),
        started_at=run_dict.get("started_at"),
        finished_at=run_dict.get("finished_at"),
        result_json=res_json,
        error_message=run_dict.get("error_message")
    )

# --- Background Worker Execution Helpers -------------------------------------
def _execute_search_task(run_id: str, intent: SearchIntent) -> None:
    rm = get_run_manager()
    rm.update_progress(run_id, phase="fetching", message=f"Searching for '{intent.query}'", current=10, total=100)
    
    try:
        from .sources.search_orchestrator import SearchOrchestrator
        from . import config
        prefs = config.load_prefs()
        prefs["query"] = intent.query
        if intent.location:
            prefs["location"] = intent.location
        if intent.sources:
            prefs["sources"] = intent.sources
        orchestrator = SearchOrchestrator()
        found_jobs, errors = orchestrator.fetch_parallel(prefs=prefs)
        rm.update_progress(run_id, phase="scoring", message=f"Fetched {len(found_jobs)} jobs across enabled sources", current=80, total=100)
        
        # Save to DB
        saved_count = 0
        for j in found_jobs:
            try:
                db.upsert_job(j)
                saved_count += 1
            except Exception:
                pass
        
        rm.update_progress(
            run_id,
            phase="completed",
            message=f"Successfully fetched and saved {saved_count} jobs",
            current=100,
            total=100,
            status="completed",
            result_data={"found_count": len(found_jobs), "saved_count": saved_count}
        )
    except Exception as e:
        rm.update_progress(run_id, status="failed", error_message=str(e), message="Search execution failed")

def _execute_audit_task(run_id: str, profile: dict[str, Any], prefs: dict[str, Any]) -> None:
    rm = get_run_manager()
    rm.update_progress(run_id, phase="auditing", message="Running capability audit & resume diagnostics", current=20, total=100)
    
    try:
        from .autonomous_resume_agent import resume_audit
        result = resume_audit(profile, prefs)
        rm.update_progress(
            run_id,
            phase="completed",
            message="Audit and diagnostic verification finished",
            current=100,
            total=100,
            status="completed",
            result_data=result
        )
    except Exception as e:
        rm.update_progress(run_id, status="failed", error_message=str(e), message="Audit execution failed")

def _execute_apply_task(run_id: str, job_id: int) -> None:
    rm = get_run_manager()
    rm.update_progress(run_id, phase="staging", message=f"Preparing application payload for job #{job_id}", current=30, total=100)
    
    try:
        from .multi_ats_pipeline import prepare_application_payload
        job_obj = db.get_job(job_id)
        if not job_obj:
            raise ValueError(f"Job #{job_id} not found")
            
        profile = db.get_profile() or {"name": "Candidate", "email": "candidate@example.com"}
        staged = prepare_application_payload(profile, job_obj)
        
        # Create session tracker
        session_id = f"sess_{job_id}_{run_id[:8]}"
        db.create_application_session(
            session_id=session_id,
            job_id=job_id,
            run_id=run_id,
            status="STAGED_READY_FOR_USER_REVIEW",
            provider=staged.get("multi_ats_audit", {}).get("detected_engine")
        )
        
        rm.update_progress(
            run_id,
            phase="completed",
            message="Application payload staged and ready for user review",
            current=100,
            total=100,
            status="completed",
            result_data={"session_id": session_id, "staged_application": staged}
        )
    except Exception as e:
        rm.update_progress(run_id, status="failed", error_message=str(e), message="Staging execution failed")

# --- Endpoints ---------------------------------------------------------------
@router.post("/search", response_model=RunView)
def trigger_search(intent: SearchIntent, background_tasks: BackgroundTasks):
    """Trigger a job search run."""
    rm = get_run_manager()
    run_dict = rm.start_run(kind="search", request_data=intent.model_dump())
    background_tasks.add_task(_execute_search_task, run_dict["run_id"], intent)
    return _to_run_view(rm.get_run(run_dict["run_id"]) or run_dict)

def _safe_breakdown(raw: Any) -> dict[str, Any] | None:
    """Coerce stored match_breakdown JSON to a valid dict, or None.

    Defense-in-depth: a single malformed row must never 500 the entire
    jobs feed (it previously did via a strict dict[str, int] model).
    """
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None
    return None


@router.get("/jobs", response_model=list[JobView])
def list_jobs_v2(
    limit: int = Query(50, le=200),
    min_score: int | None = Query(None),
    remote_only: bool = Query(False)
):
    """List recent saved jobs with filtering."""
    raw_jobs = db.list_jobs(limit=limit, min_score=min_score or 0, remote_only=remote_only)
    views = []
    for j in raw_jobs:
        # Check if there's an application status for this job
        app = db.get_application(j["id"])
        status = app["status"] if app else "Saved"
        views.append(JobView(
            id=j["id"],
            title=j.get("title") or "Unknown Title",
            company=j.get("company") or "Unknown Company",
            location=j.get("location"),
            remote=bool(j.get("remote", 1)),
            url=j.get("url"),
            apply_url=j.get("apply_url"),
            description=j.get("description"),
            salary_min=j.get("salary_min"),
            salary_max=j.get("salary_max"),
            currency=j.get("currency"),
            posted_at=j.get("posted_at"),
            match_score=j.get("match_score"),
            match_reason=j.get("match_reason"),
            match_breakdown=_safe_breakdown(j.get("match_breakdown")),
            red_flags=j.get("red_flags"),
            status=status
        ))
    return views

@router.get("/jobs/{id}", response_model=JobView)
def get_job_v2(id: int):
    """Get details of a specific job by ID."""
    j = db.get_job(id)
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")
    app = db.get_application(id)
    status = app["status"] if app else "Saved"
    return JobView(
        id=j["id"],
        title=j.get("title") or "Unknown Title",
        company=j.get("company") or "Unknown Company",
        location=j.get("location"),
        remote=bool(j.get("remote", 1)),
        url=j.get("url"),
        apply_url=j.get("apply_url"),
        description=j.get("description"),
        salary_min=j.get("salary_min"),
        salary_max=j.get("salary_max"),
        currency=j.get("currency"),
        posted_at=j.get("posted_at"),
        match_score=j.get("match_score"),
        match_reason=j.get("match_reason"),
        match_breakdown=_safe_breakdown(j.get("match_breakdown")),
        red_flags=j.get("red_flags"),
        status=status
    )

@router.post("/jobs/{id}/audit", response_model=RunView)
def trigger_audit(id: int, req: AuditRequest, background_tasks: BackgroundTasks):
    """Trigger a capability & claim audit run on a candidate profile for a job."""
    j = db.get_job(id)
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")
    rm = get_run_manager()
    profile = req.profile or db.get_profile() or {}
    run_dict = rm.start_run(kind="audit", request_data={"job_id": id, "profile_name": profile.get("name")})
    background_tasks.add_task(_execute_audit_task, run_dict["run_id"], profile, req.prefs)
    return _to_run_view(rm.get_run(run_dict["run_id"]) or run_dict)

@router.post("/jobs/{id}/apply", response_model=RunView)
def trigger_apply_staging(id: int, background_tasks: BackgroundTasks):
    """Trigger application payload staging (STAGED_READY_FOR_USER_REVIEW)."""
    j = db.get_job(id)
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")
    rm = get_run_manager()
    run_dict = rm.start_run(kind="apply", request_data={"job_id": id})
    background_tasks.add_task(_execute_apply_task, run_dict["run_id"], id)
    return _to_run_view(rm.get_run(run_dict["run_id"]) or run_dict)

@router.get("/runs", response_model=list[RunView])
def list_runs_v2(limit: int = Query(50, le=100), status: str | None = Query(None)):
    """List recent runs."""
    rm = get_run_manager()
    return [_to_run_view(r) for r in rm.list_runs(limit=limit, status=status)]

@router.get("/runs/{run_id}", response_model=RunView)
def get_run_v2(run_id: str):
    """Get status of a specific run."""
    rm = get_run_manager()
    r = rm.get_run(run_id)
    if not r:
        raise HTTPException(status_code=404, detail="Run not found")
    return _to_run_view(r)

@router.get("/runs/{run_id}/events")
def get_run_events_v2(run_id: str):
    """Get event logs for a specific run."""
    rm = get_run_manager()
    if not rm.get_run(run_id):
        raise HTTPException(status_code=404, detail="Run not found")
    return db.get_run_events(run_id)

@router.get("/apply-previews")
def list_apply_previews_v2(limit: int = Query(10, le=30)):
    """Recent post-fill verification packs (review-first evidence).

    Each item mirrors what autofill_runner._write_fill_report saved:
    a full-page screenshot plus exactly which fields were filled.
    """
    try:
        from . import config as _config

        previews_dir = _config.OUTPUTS_DIR / "apply_previews"
        if not previews_dir.exists():
            return []
        items = []
        for path in sorted(previews_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            items.append({
                "file": path.stem,
                "generated_at": data.get("generated_at"),
                "apply_url": data.get("apply_url"),
                "job_title": data.get("job_title"),
                "job_company": data.get("job_company"),
                "fields_filled_count": len(data.get("fields_filled") or []),
                "has_screenshot": bool(data.get("screenshot")),
            })
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not list apply previews: {e}")


@router.get("/apply-previews/{name}")
def get_apply_preview_v2(name: str):
    """Full verification pack by file stem (no path traversal: stem only)."""
    import re as _re

    if not _re.fullmatch(r"[A-Za-z0-9_\-]+", name):
        raise HTTPException(status_code=400, detail="Invalid preview name")
    try:
        from . import config as _config

        path = (_config.OUTPUTS_DIR / "apply_previews" / f"{name}.json")
        if not path.exists():
            raise HTTPException(status_code=404, detail="Preview not found")
        return json.loads(path.read_text(encoding="utf-8"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read preview: {e}")


@router.get("/stealth-status")
def stealth_status_v2():
    """Live stealth-browser engine status for the Settings UI (never throws)."""
    try:
        from src.stealth_browser import status as _engine_status

        return _engine_status()
    except Exception as e:  # defensive: settings page must always render
        return {"error": str(e), "package_installed": False, "browser_fetched": False}


@router.get("/events")
async def stream_events_v2(request: Request, run_id: str | None = Query(None)):
    """Realtime SSE stream for run updates and progress."""
    rm = get_run_manager()

    async def event_generator():
        # Send an initial connection ping and current active runs summary
        active = rm.list_runs(limit=10, status="running")
        yield f"event: connected\ndata: {json.dumps({'status': 'ok', 'active_runs': len(active)})}\n\n"
        
        async for payload in rm.subscribe(run_id=run_id):
            if request.is_disconnected():
                break
            evt_name = payload.get("event", "message")
            data_str = json.dumps(payload.get("data", {}), ensure_ascii=False)
            yield f"event: {evt_name}\ndata: {data_str}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/jobs/{job_id}/ats_breakdown")
def get_job_ats_breakdown(job_id: int):
    """Run adversarial ATS simulation against candidate profile for a specific job."""
    from .ats_simulator import simulate_adversarial_ats
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job #{job_id} not found")

    profile = db.get_profile() or {}
    resume_text = profile.get("raw_text") or profile.get("summary") or ""
    if not resume_text and profile.get("skills"):
        resume_text = f"Skills: {', '.join(profile.get('skills', []))}. Experience in software engineering."

    jd_text = job.get("description") or job.get("title") or ""
    return simulate_adversarial_ats(job_description=jd_text, resume_text=resume_text)


@router.get("/jobs/{job_id}/salary_arbitrage")
def get_job_salary_arbitrage(job_id: int):
    """Calculate compa-ratio and salary negotiation leverage for a specific job."""
    from .salary_arbitrage import calculate_compa_ratio
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job #{job_id} not found")

    return calculate_compa_ratio(
        salary_min=job.get("salary_min"),
        salary_max=job.get("salary_max"),
        job_title=job.get("title", ""),
        location=job.get("location"),
        currency=job.get("currency") or "USD"
    )


# --- APEX CAREER AUTONOMOUS WARFARE ENGINE (v2 Extended) ---------------------

class SystemOneTriageRequest(BaseModel):
    query: str
    candidates: list[str]

class RadarScanRequest(BaseModel):
    company_name: str
    sec_form_d_filings: list[dict[str, Any]] = Field(default_factory=list)
    github_commit_signals: list[dict[str, Any]] = Field(default_factory=list)
    executive_hires: list[dict[str, Any]] = Field(default_factory=list)

class ForensicAuditRequest(BaseModel):
    title: str
    company: str
    description: str
    days_active: int = 0
    repost_count: int = 0

class TournamentSimulateRequest(BaseModel):
    job_description: str
    resume_text: str
    simulations: int = 50

class TrojanSynthesizeRequest(BaseModel):
    target_company: str
    target_repo_or_product: str
    candidate_skills: list[str]
    issue_description: str = ""

class ATSDecompileRequest(BaseModel):
    resume_text: str
    expected_keywords: list[str] = Field(default_factory=list)

class BackchannelRouteRequest(BaseModel):
    company_name: str
    target_role: str
    domain: str = ""
    candidate_profile: dict[str, Any] = Field(default_factory=dict)
    job_details: dict[str, Any] = Field(default_factory=dict)
    artefact_url: str | None = None

class SkillScaffoldRequest(BaseModel):
    candidate_skills: list[str] = Field(default_factory=list)
    target_jobs: list[dict[str, Any]] = Field(default_factory=list)
    scaffold_skill: str | None = None

class TelemetryEventRequest(BaseModel):
    job_id: int
    arm_id: str
    new_stage: str
    previous_stage: str = "DISCOVERED"
    days_elapsed: float = 0.0
    notes: str = ""

class PacingPlanRequest(BaseModel):
    packages: list[dict[str, Any]] = Field(default_factory=list)

class InterviewHUDRequest(BaseModel):
    transcript_snippet: str

class BrowserApplyRequest(BaseModel):
    job_url: str
    profile_data: dict[str, Any] = Field(default_factory=dict)
    resume_pdf_path: str | None = None
    job_id: int | None = None
    auto_submit: bool = False

class BrowserDiscoverRequest(BaseModel):
    board_url: str
    search_query: str
    max_jobs: int = 10

class PipelineRunRequest(BaseModel):
    jobs: list[dict[str, Any]] = Field(default_factory=list)
    profile_data: dict[str, Any] = Field(default_factory=dict)
    mode: str = "autonomous"  # "conservative" | "autonomous" | "full_auto"
    max_jobs_per_run: int = 5


@router.post("/system-one/triage")
def system_one_triage(req: SystemOneTriageRequest):
    """Sub-50ms parallel triage using Jev System-1 decision primitives."""
    from .system_one import get_system_one_engine
    engine = get_system_one_engine()
    choice = engine.choice(req.query, req.candidates)
    return {
        "selected": choice.selected,
        "index": choice.index,
        "calibrated_p": choice.calibrated_p,
        "latency_ms": choice.latency_ms,
        "mode": choice.mode
    }


@router.post("/radar/scan")
def radar_scan(req: RadarScanRequest):
    """Detect pre-market hiring requisition signals from SEC Form D, GitHub commits, and exec hires."""
    from .predictive_radar import PredictiveRadar
    radar = PredictiveRadar()
    signal = radar.analyze_premarket_signals(
        company_name=req.company_name,
        sec_filings=req.sec_form_d_filings,
        github_signals=req.github_commit_signals,
        exec_hires=req.executive_hires
    )
    return signal


@router.post("/forensics/audit")
def forensics_audit(req: ForensicAuditRequest):
    """Expose ghost jobs, compliance listings, and perpetual resume harvesters."""
    from .forensic_filter import ForensicFilter
    flt = ForensicFilter()
    verdict = flt.audit_posting(
        title=req.title,
        company=req.company,
        description=req.description,
        days_active=req.days_active,
        repost_count=req.repost_count
    )
    return verdict


@router.post("/tournament/simulate")
def tournament_simulate(req: TournamentSimulateRequest):
    """Run Monte Carlo shadow hiring tournament across ATS, Recruiter, and EM personas."""
    from .shadow_tournament import ShadowHiringTournament
    tournament = ShadowHiringTournament()
    result = tournament.simulate_tournament(
        job_description=req.job_description,
        resume_text=req.resume_text,
        simulations=req.simulations
    )
    return result


@router.post("/trojan/synthesize")
def trojan_synthesize(req: TrojanSynthesizeRequest):
    """Synthesize Proof-of-Value Trojan Horse PR / technical blueprint for target company."""
    from .trojan_horse import TrojanHorseEngine
    engine = TrojanHorseEngine()
    package = engine.synthesize_proof_of_value(
        target_company=req.target_company,
        target_repo_or_product=req.target_repo_or_product,
        candidate_skills=req.candidate_skills,
        known_issue=req.issue_description
    )
    return package


@router.post("/ats/decompile")
def ats_decompile(req: ATSDecompileRequest):
    """Decompile resume and verify Extraction Fidelity Index (EFI >= 0.98)."""
    from .ats_reverse_compiler import ATSReverseCompiler
    compiler = ATSReverseCompiler()
    score = compiler.audit_text_fidelity(
        extracted_text=req.resume_text,
        expected_keywords=req.expected_keywords
    )
    return score


@router.post("/backchannel/route")
def backchannel_route(req: BackchannelRouteRequest):
    """Discover engineering org hierarchy and draft Proof-of-Work backchannel memos."""
    from .backchannel_pathfinder import BackchannelPathfinder
    pathfinder = BackchannelPathfinder()
    route = pathfinder.route_backchannel(
        company_name=req.company_name,
        target_role=req.target_role,
        domain=req.domain,
        candidate_profile=req.candidate_profile,
        job_details=req.job_details,
        artefact_url=req.artefact_url
    )
    return route


@router.post("/skills/scaffold")
def skills_scaffold(req: SkillScaffoldRequest):
    """Detect high-ROI skill gaps and scaffold 48-hour proof-of-competency repo blueprints."""
    from .skill_scaffolder import SkillScaffolder
    scaffolder = SkillScaffolder()
    gaps = scaffolder.analyze_skill_gaps(
        candidate_skills=req.candidate_skills,
        target_jobs=req.target_jobs
    )
    blueprint = None
    if req.scaffold_skill:
        blueprint = scaffolder.scaffold_project(req.scaffold_skill)
    elif gaps:
        blueprint = scaffolder.scaffold_project(gaps[0].skill_name)

    return {
        "skill_gaps": gaps,
        "blueprint": blueprint
    }


@router.get("/telemetry/funnel")
def telemetry_funnel():
    """Retrieve application conversion funnels and Multi-Armed Bandit parameters."""
    from .telemetry_bandit import TelemetryEngine
    engine = TelemetryEngine()
    return engine.get_funnel_summary()


@router.post("/telemetry/event")
def telemetry_record_event(req: TelemetryEventRequest):
    """Record an application lifecycle state transition and update Thompson Sampling priors."""
    from .telemetry_bandit import TelemetryEngine
    engine = TelemetryEngine()
    event = engine.record_transition(
        job_id=req.job_id,
        arm_id=req.arm_id,
        new_stage=req.new_stage,
        previous_stage=req.previous_stage,
        days_elapsed=req.days_elapsed,
        notes=req.notes
    )
    return event


@router.get("/memory/graph")
def memory_get_graph(root_id: str = "Candidate"):
    """Query active bitemporal knowledge graph and connected entity context."""
    from .memory_graph import BitemporalMemoryGraph
    graph = BitemporalMemoryGraph()
    return graph.get_subgraph(root_id, max_depth=2)


@router.post("/pacing/plan")
def pacing_plan(req: PacingPlanRequest):
    """Calculate multi-pipeline pacing actions, exploding offer extensions, and counter-anchors."""
    from .offer_game_theory import OfferGameTheoryEngine, OfferPackage
    engine = OfferGameTheoryEngine()
    pkgs = [OfferPackage(**p) for p in req.packages]
    return engine.analyze_pipeline_pacing(pkgs)


@router.post("/interview/hud")
def interview_hud(req: InterviewHUDRequest):
    """Sub-50ms live interview whisper response with STAR story and architectural layout."""
    from .interview_hud import InterviewHUDEngine
    engine = InterviewHUDEngine()
    return engine.generate_hud_response(req.transcript_snippet)


@router.get("/evolution/status")
def evolution_status():
    """Get status of recursive codebase self-evolution, learned lessons, and synthesized tools."""
    from .self_evolution import SelfEvolutionEngine
    engine = SelfEvolutionEngine()
    return engine.get_evolution_summary()


@router.post("/browser/apply")
async def browser_apply(req: BrowserApplyRequest):
    """Executes autonomous multi-step navigation and form filling on target job posting."""
    from .browser_agent import AutonomousBrowserAgent
    agent = AutonomousBrowserAgent()
    result = await agent.navigate_and_apply(
        job_url=req.job_url,
        profile_data=req.profile_data,
        resume_pdf_path=req.resume_pdf_path,
        job_id=req.job_id,
        auto_submit=req.auto_submit
    )
    return result


@router.post("/browser/discover")
async def browser_discover(req: BrowserDiscoverRequest):
    """Navigates to a company career board and extracts active job requisitions."""
    from .browser_agent import AutonomousBrowserAgent
    agent = AutonomousBrowserAgent()
    jobs = await agent.discover_board_jobs(
        board_url=req.board_url,
        search_query=req.search_query,
        max_jobs=req.max_jobs
    )
    return {"board_url": req.board_url, "discovered_jobs": jobs, "total": len(jobs)}


@router.post("/pipeline/run")
async def pipeline_run(req: PipelineRunRequest):
    """Executes the master end-to-end career warfare pipeline across target jobs."""
    from .career_agent import CareerAgentOrchestrator, CareerPipelineConfig
    orchestrator = CareerAgentOrchestrator()
    cfg = CareerPipelineConfig(
        mode=req.mode,
        max_jobs_per_run=req.max_jobs_per_run
    )
    summary = await orchestrator.run_pipeline(
        jobs=req.jobs,
        profile_data=req.profile_data,
        config_override=cfg
    )
    return summary


