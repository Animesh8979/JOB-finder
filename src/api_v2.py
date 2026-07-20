"""api_v2: Versioned API contract (/api/v2) with strict Pydantic views and SSE stream.

Supports unified Command Center operations with durable run tracking.
"""
from __future__ import annotations

import asyncio
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
    match_breakdown: dict[str, int] | None = None
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
        from . import jobs as jobs_module
        # Perform multi-source search via existing jobs module
        found_jobs = jobs_module.fetch_all_jobs(query=intent.query)
        rm.update_progress(run_id, phase="scoring", message=f"Scored {len(found_jobs)} jobs", current=80, total=100)
        
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
            match_breakdown=j.get("match_breakdown"),
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
        match_breakdown=j.get("match_breakdown"),
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
