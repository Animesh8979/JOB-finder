"""FastAPI backend server for Job Application Copilot."""
from __future__ import annotations

import time
import json
import threading
from collections import defaultdict
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from urllib.parse import urlparse

from src import config, db, profile_parser, scraper, matcher, insights, tailor, contacts_enricher

# Initialize Database
db.init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle hook.

    On startup: eagerly load the SentenceTransformer embedding model in a background
    thread so the first job-scoring request isn't blocked for 5-10 seconds.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    # Run the heavy model load in a thread pool so we don't block server startup.
    loop.run_in_executor(None, matcher.preload_encoder)
    yield


class RateLimiter:
    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window
        self.history = defaultdict(list)
        self.lock = threading.Lock()
        self.last_cleanup = time.time()

    def _cleanup(self, now: float):
        if now - self.last_cleanup > self.window:
            cutoff = now - self.window
            for ip in list(self.history.keys()):
                self.history[ip] = [t for t in self.history[ip] if t > cutoff]
                if not self.history[ip]:
                    del self.history[ip]
            self.last_cleanup = now

    def __call__(self, request: Request):
        # Trust X-Forwarded-For if available (assuming behind a trusted proxy)
        forwarded = request.headers.get("x-forwarded-for")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "127.0.0.1")
        now = time.time()
        cutoff = now - self.window

        with self.lock:
            self._cleanup(now)
            self.history[client_ip] = [t for t in self.history[client_ip] if t > cutoff]

            if len(self.history[client_ip]) >= self.limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many requests. Limit is {self.limit} requests per {self.window} seconds."
                )
            self.history[client_ip].append(now)


ai_limiter = RateLimiter(limit=15, window=60)

app = FastAPI(title="Job Application Copilot API", version="1.0.0", lifespan=lifespan)

# Enable CORS for development hot reloading
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def strict_localhost_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    referer = request.headers.get("referer")
    
    # Require origin or referer for state mutating methods
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        if not origin and not referer:
            return JSONResponse(status_code=403, content={"detail": "Cross-Site Request Forbidden by Anti-CSRF policy: Missing Origin/Referer."})
            
    for val in filter(None, [origin, referer]):
        netloc = urlparse(val).netloc.lower()
        if netloc not in ("127.0.0.1:5173", "localhost:5173", "127.0.0.1:8000", "localhost:8000", "127.0.0.1", "localhost"):
            return JSONResponse(status_code=403, content={"detail": "Cross-Site Request Forbidden by Anti-CSRF policy."})
            
    return await call_next(request)

# --- Schemas ---
class PrefsPayload(BaseModel):
    prefs: dict
    secrets: dict

class ScrapePayload(BaseModel):
    url: str

class ApifyPayload(BaseModel):
    query: str
    location: str
    limit: int = 10

class AppUpdatePayload(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    applied_at: Optional[str] = None
    follow_up_at: Optional[str] = None

class TailorPayload(BaseModel):
    angle: str = "Balanced (Default)"
    tone: str = "Professional"
    extra_notes: str = ""

class EnrichPayload(BaseModel):
    company_name: str
    job_id: int

class ContactPayload(BaseModel):
    name: str
    email: str
    company: Optional[str] = None
    role: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    job_id: Optional[int] = None

class OutreachPayload(BaseModel):
    contact_id: Optional[int] = None
    job_id: Optional[int] = None
    subject: str
    body: str
    channel: Optional[str] = "gmail_draft"
    status: Optional[str] = "draft"
    sent_at: Optional[str] = None

class OutreachQueuePayload(BaseModel):
    contact_ids: list[int]
    job_ids: list[Optional[int]]
    tone: str = "Professional"
    extra_notes: str = ""

class JobScorePayload(BaseModel):
    job_ids: list[Optional[int]]
    tone: str = "Professional"
    extra_notes: str = ""

class DiscoverPayload(BaseModel):
    search_term: str
    location: str
    results_wanted: int = 20

# --- API Endpoints ---

@app.get("/health")
def health():
    """Liveness probe used by Docker HEALTHCHECK and k8s liveness."""
    return {"status": "ok"}

@app.get("/api/status")
def get_status():
    """Get candidate configuration readiness checks."""
    return config.readiness()

@app.get("/api/profile")
def get_profile():
    """Retrieve structured candidate resume profile."""
    prof = config.load_profile()
    return prof or {}

@app.post("/api/profile")
def save_profile(profile_data: dict):
    """Manually update candidate profile."""
    config.save_profile(profile_data)
    return {"status": "success", "profile": profile_data}

@app.post("/api/profile/upload")
async def upload_resume(file: UploadFile = File(...)):
    """Upload PDF/Word resume, parse it with LLM and update profile."""
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File size exceeds the 10MB limit.")
    try:
        text = profile_parser.extract_text(content, file.filename)
        parsed = profile_parser.parse_resume(text)
        config.save_profile(parsed)
        
        # Proactively populate Identity fields in preferences
        prefs = config.load_prefs()
        prefs["identity"]["full_name"] = parsed.get("name", "")
        prefs["identity"]["email"] = parsed.get("email", "")
        prefs["identity"]["phone"] = parsed.get("phone", "")
        links = parsed.get("links", {})
        if isinstance(links, dict) and links.get("linkedin"):
            prefs["identity"]["linkedin"] = links.get("linkedin", "")
        config.save_prefs(prefs)
        
        return {"status": "success", "profile": parsed}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/profiles")
def list_profiles():
    """List all available profile names."""
    return {"profiles": config.list_profiles()}

@app.post("/api/profiles/{name}")
def save_named_profile(name: str, profile_data: dict):
    """Create or update a specific profile."""
    config.save_profile(profile_data, name=name)
    return {"status": "success", "profile": profile_data}

@app.delete("/api/profiles/{name}")
def delete_profile(name: str):
    """Delete a specific profile."""
    path = config.PROFILES_DIR / f"{name}.json"
    if path.exists():
        path.unlink()
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Profile not found.")

@app.post("/api/profiles/{name}/activate")
def activate_profile(name: str):
    """Set a profile as active."""
    prefs = config.load_prefs()
    prefs["active_profile"] = name
    config.save_prefs(prefs)
    return {"status": "success", "active_profile": name}

@app.get("/api/preferences")
def get_preferences():
    """Get preferences list and secrets setup check."""
    prefs = config.load_prefs()
    
    # Do not return actual API keys, return boolean flags or obfuscated strings
    has_anthropic = bool(config.anthropic_key())
    has_gemini = bool(config.gemini_key())
    has_nvidia = bool(config.get_secret("nvidia_api_key", "NVIDIA_API_KEY"))
    has_apify = bool(config.get_secret("apify_api_token", "APIFY_API_TOKEN"))
    has_proxycurl = bool(config.get_secret("proxycurl_api_key", "PROXYCURL_API_KEY"))
    
    return {
        "prefs": prefs,
        "secrets": {
            "anthropic_api_key": "********" if has_anthropic else "",
            "gemini_api_key": "********" if has_gemini else "",
            "nvidia_api_key": "********" if has_nvidia else "",
            "apify_api_token": "********" if has_apify else "",
            "proxycurl_api_key": "********" if has_proxycurl else ""
        }
    }

@app.post("/api/preferences")
def save_preferences(payload: PrefsPayload):
    """Save preferences and keys."""
    # Update regular preferences
    config.save_prefs(payload.prefs)
    
    # Update secret keys
    secret_updates = {}
    for k, v in payload.secrets.items():
        if v and not v.startswith("***"):
            secret_updates[k] = v
    if secret_updates:
        config.set_secrets(secret_updates)
    return {"status": "success"}

@app.get("/api/jobs")
def get_jobs(only_scored: bool = False, min_score: int = 0, search: str = ""):
    """Retrieve filtered, searched, and sorted job entries."""
    return db.list_jobs(only_scored=only_scored, min_score=min_score, search=search)

@app.post("/api/jobs/scrape", dependencies=[Depends(ai_limiter)])
async def scrape_job(payload: ScrapePayload):
    """Scrape single job URL and extract details with LLM."""
    try:
        text = scraper.scrape_url_text(payload.url)
        job = scraper.parse_job_from_text(text, payload.url)
        job_id = db.upsert_job(job)
        
        if config.provider_ready():
            try:
                profile = config.load_profile() or {}
                prefs = config.load_prefs()
                scored = matcher.score_jobs([job], profile, prefs)
                if scored:
                    db.set_job_score(job_id, scored[0]["score"], scored[0]["reason"])
            except Exception:
                pass
                
        return {"status": "success", "job_id": job_id, "job": db.get_job(job_id)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/jobs/discover")
async def discover_jobs(payload: DiscoverPayload):
    """Headless bulk discovery via JobSpy."""
    try:
        from src import job_discovery
        count = job_discovery.discover_and_ingest(
            search_term=payload.search_term,
            location=payload.location,
            results_wanted=payload.results_wanted
        )
        return {"status": "success", "ingested": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/{job_id}/auto-apply")
async def auto_apply(job_id: int):
    """Queue the local Edge Playwright auto-apply bot in the background."""
    from src.tasks import run_auto_apply_task
    run_auto_apply_task(job_id)
    return {"status": "queued", "message": "Auto-apply process has been queued securely in the background."}

@app.post("/api/outreach/process")
def process_outreach():
    """Trigger the SMTP auto-networking engine to process the queue."""
    from src import auto_network
    count = auto_network.process_outreach_queue()
    return {"status": "success", "processed_count": count}

class ManualIngestPayload(BaseModel):
    url: str
    html: str

@app.post("/api/jobs/manual-ingest", dependencies=[Depends(ai_limiter)])
async def manual_ingest_job(payload: ManualIngestPayload):
    """Ingest job HTML directly from browser extension to bypass bot protections."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(payload.html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        job = scraper.parse_job_from_text(text, payload.url)
        job_id = db.upsert_job(job)
        
        if config.provider_ready():
            try:
                profile = config.load_profile() or {}
                prefs = config.load_prefs()
                scored = matcher.score_jobs([job], profile, prefs)
                if scored:
                    db.set_job_score(job_id, scored[0]["score"], scored[0]["reason"])
            except Exception:
                pass
                
        return {"status": "success", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/jobs/apify")
def trigger_apify_scrape(payload: ApifyPayload):
    """Schedule LinkedIn/Indeed search scraping via durable Huey queue."""
    token = config.get_secret("apify_api_token", "APIFY_API_TOKEN")
    if not token:
        raise HTTPException(status_code=400, detail="Apify API Token not configured. Please add it in settings.")
    from src.tasks import run_apify_scraping_task
    run_apify_scraping_task(payload.query, payload.location, payload.limit)
    return {"status": "success", "message": "Apify scraper queued in Huey."}

@app.post("/api/jobs/{id}/score", dependencies=[Depends(ai_limiter)])
async def score_single_job(id: int):
    """Request AI match scoring on a single job posting."""
    job = db.get_job(id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    profile = config.load_profile()
    if not profile:
        raise HTTPException(status_code=400, detail="Resume not parsed yet. Please upload it first.")
    prefs = config.load_prefs()
    try:
        scored = matcher.score_jobs([job], profile, prefs)
        if scored:
            db.set_job_score(id, scored[0]["score"], scored[0]["reason"])
            return {"status": "success", "score": scored[0]["score"], "reason": scored[0]["reason"]}
        raise HTTPException(status_code=500, detail="Match score calculation empty.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/score-all")
def score_all_jobs():
    """Batch-calculate matching scores via durable Huey queue."""
    if not config.provider_ready():
        raise HTTPException(status_code=400, detail="AI Key not set.")
    from src.tasks import run_score_all_task
    run_score_all_task()
    return {"status": "success", "message": "Background batch scoring queued in Huey."}

@app.get("/api/jobs/{id}/insights")
def get_job_insights(id: int):
    """Gather red flags, company culture signals, and salary estimates."""
    job = db.get_job(id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    red_flags = insights.detect_red_flags(job.get("description", ""))
    profile = config.load_profile() or {}
    prefs = config.load_prefs()
    
    fit = {}
    salary = {}
    if config.provider_ready():
        try:
            fit = insights.analyze_fit(job, profile, prefs)
        except Exception:
            pass
        try:
            salary = insights.estimate_salary(job, profile, prefs)
        except Exception:
            pass
            
    return {
        "red_flags": red_flags,
        "fit_analysis": fit,
        "salary_estimate": salary
    }

@app.get("/api/applications")
def get_applications():
    """List tracked applications joined with job meta."""
    return db.list_applications()

@app.get("/api/applications/{job_id}")
def get_single_application(job_id: int):
    """Get details of specific application status, notes, and cover letter."""
    app = db.get_application(job_id)
    if not app:
        return db.get_or_create_application(job_id)
    return app

@app.post("/api/applications/{job_id}")
def update_application_status(job_id: int, payload: AppUpdatePayload):
    """Modify application lifecycle status, notes, or timelines."""
    fields = {k: v for k, v in payload.dict().items() if v is not None}
    db.update_application(job_id, **fields)
    return {"status": "success"}

@app.post("/api/applications/{job_id}/tailor", dependencies=[Depends(ai_limiter)])
async def tailor_documents(job_id: int, payload: TailorPayload):
    """Run LLM cover letter and resume tailoring, saving files on disk."""
    job = db.get_job(job_id)
    profile = config.load_profile()
    if not profile:
        raise HTTPException(status_code=400, detail="Profile resume details missing.")
    prefs = config.load_prefs()
    
    try:
        tailored_res = tailor.tailor_resume(job, profile, prefs, angle=payload.angle)
        company_intel = scraper.get_company_intelligence(job.get("company", ""))
        cl_text = tailor.company_specific_cover_letter(job, profile, prefs, tone=payload.tone, extra_notes=payload.extra_notes, company_intel=company_intel)
        
        from src import documents
        doc_paths = documents.generate_documents(job, tailored_res, cl_text, style_config=prefs)
        flagged_skills = insights.flag_possible_fabrication(tailored_res, profile)
        
        # We store PDF version paths inside database columns
        db.update_application(
            job_id,
            status="Tailored",
            tailored_resume_text=documents.resume_to_text(tailored_res),
            cover_letter_text=cl_text,
            tailored_resume_path=doc_paths.get("resume_pdf"),
            cover_letter_path=doc_paths.get("cover_pdf")
        )
        
        return {
            "status": "success",
            "cover_letter_text": cl_text,
            "flagged_skills": flagged_skills,
            "files": {
                "resume_docx": f"/api/files/download?path={doc_paths.get('resume_docx')}",
                "resume_pdf": f"/api/files/download?path={doc_paths.get('resume_pdf')}",
                "cover_docx": f"/api/files/download?path={doc_paths.get('cover_docx')}",
                "cover_pdf": f"/api/files/download?path={doc_paths.get('cover_pdf')}"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/applications/{job_id}/ats-check", dependencies=[Depends(ai_limiter)])
async def run_ats_check(job_id: int):
    """Run simulated ATS check on current tailored resume or default profile vs job description."""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    app_record = db.get_application(job_id)
    resume_text = ""
    if app_record and app_record.get("tailored_resume_text"):
        resume_text = app_record.get("tailored_resume_text")
    else:
        profile = config.load_profile()
        if not profile:
            raise HTTPException(status_code=400, detail="Please upload a resume first.")
        resume_text = profile.get("raw_text") or json.dumps(profile)
        
    profile = config.load_profile() or {}
    prefs = config.load_prefs()
    try:
        report = insights.check_resume_ats(resume_text, job.get("description", ""), profile, prefs)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/applications/{job_id}/improve-bullets", dependencies=[Depends(ai_limiter)])
async def run_improve_bullets(job_id: int):
    """Suggest rephrasings for resume bullet points based on the job description."""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    profile = config.load_profile()
    if not profile:
        raise HTTPException(status_code=400, detail="Please upload a resume first.")
        
    prefs = config.load_prefs()
    try:
        suggestions = tailor.suggest_bullet_improvements(job, profile, prefs)
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/files/download")
async def download_file(path: str):
    """Secure local file downloading endpoint."""
    resolved_path = Path(path).resolve()
    resolved_outputs = Path(config.OUTPUTS_DIR).resolve()
    
    try:
        resolved_path = resolved_path.resolve(strict=False)
        resolved_outputs = resolved_outputs.resolve(strict=False)
        # Ensure the resolved path strictly sits under the outputs directory securely
        resolved_path.relative_to(resolved_outputs)
    except ValueError:
        raise HTTPException(status_code=403, detail="Unauthorized file access.")
        
    if not resolved_path.exists():
        raise HTTPException(status_code=404, detail="File does not exist.")
        
    return FileResponse(str(resolved_path), filename=resolved_path.name)

@app.post("/api/applications/{job_id}/apply")
async def trigger_playwright_apply(job_id: int):
    """Launch Playwright browser assistant for review-first pre-filling."""
    job = db.get_job(job_id)
    app = db.get_application(job_id)
    profile = config.load_profile()
    prefs = config.load_prefs()
    
    if not job or not app:
        raise HTTPException(status_code=404, detail="Application record not found.")
        
    try:
        from src import autofill
        resume_path = app.get("tailored_resume_path") or ""
        cl_text = app.get("cover_letter_text") or ""
        note = autofill.launch_assisted_apply(job, resume_path, cl_text, profile, prefs)
        return {"status": "success", "note": note}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/applications/{job_id}/interview-prep", dependencies=[Depends(ai_limiter)])
def get_interview_prep(job_id: int):
    """Retrieve mock behavioral questions and company dossiers."""
    job = db.get_job(job_id)
    profile = config.load_profile()
    prefs = config.load_prefs()
    
    if not job or not profile:
        raise HTTPException(status_code=404, detail="Job or profile missing.")
        
    try:
        dossier = insights.generate_company_dossier(job.get("company", ""), job.get("title", ""), job.get("description", ""), prefs)
        prep = insights.generate_interview_prep(job, profile, prefs)
        return {"dossier": dossier, "prep": prep}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/contacts")
def get_contacts():
    """List network contacts."""
    return db.list_contacts()

@app.post("/api/contacts")
def create_contact(contact: ContactPayload):
    """Create manual contact."""
    contact_id = db.add_contact(**contact.dict())
    return {"status": "success", "id": contact_id}

@app.post("/api/contacts/enrich", dependencies=[Depends(ai_limiter)])
def enrich_company_recruiters(payload: EnrichPayload):
    """Enrich recruiter contacts for a hiring company via Proxycurl API."""
    try:
        contacts = contacts_enricher.enrich_recruiter_contacts(payload.company_name, payload.job_id)
        return {"status": "success", "contacts": contacts}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/outreach")
def get_outreach_logs():
    """List outbox outreach drafts and sequences."""
    return db.list_outreach()

@app.post("/api/outreach")
def log_outreach_action(outreach_data: OutreachPayload):
    """Create or log an outreach event."""
    outreach_id = db.add_outreach(**outreach_data.dict())
    return {"status": "success", "id": outreach_id}

@app.post("/api/outreach/queue", dependencies=[Depends(ai_limiter)])
def queue_outreach_emails(payload: OutreachQueuePayload):
    """Queue cold outreach drafts via durable Huey queue."""
    if not config.provider_ready():
        raise HTTPException(status_code=400, detail="AI Key not set.")
    if len(payload.contact_ids) != len(payload.job_ids):
        raise HTTPException(status_code=400, detail="contact_ids and job_ids list lengths must match.")
        
    from src.tasks import process_outreach_queue_task
    process_outreach_queue_task(
        payload.contact_ids,
        payload.job_ids,
        payload.tone,
        payload.extra_notes
    )
    return {"status": "success", "message": f"Outreach queue scheduled in Huey for {len(payload.contact_ids)} contacts."}

@app.get("/api/outreach/{job_id}/generate")
def generate_sequence_email(job_id: int, followup_number: int = 1, days_since_apply: int = 7):
    """Generate smart follow-up templates matching days elapsed."""
    job = db.get_job(job_id)
    profile = config.load_profile()
    prefs = config.load_prefs()
    
    if not job or not profile:
        raise HTTPException(status_code=404, detail="Job context missing.")
    try:
        subject, body = insights.generate_followup_email(job, profile, prefs, followup_number, days_since_apply)
        return {"subject": subject, "body": body}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
def get_dashboard_stats():
    """Fetch Kanban funnel metrics."""
    return db.application_stats()

# --- Serve Frontend build ---
frontend_dist = Path(__file__).resolve().parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    
    @app.get("/{fallback_path:path}")
    def serve_frontend_page(fallback_path: str):
        if fallback_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not Found")
            
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
        return HTMLResponse(content="<h3>Frontend build folder is empty. Run build.bat to compile.</h3>")
else:
    @app.get("/{fallback_path:path}")
    def serve_dev_notice(fallback_path: str):
        if fallback_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not Found")
        return HTMLResponse(content="<h3>Production build not compiled yet. Run build.bat. During development, run 'npm run dev' inside the frontend folder.</h3>")

if __name__ == "__main__":
    import uvicorn
    import threading
    import webbrowser

    def open_browser():
        webbrowser.open("http://127.0.0.1:8000")

    # Open the browser in 1.5 seconds once server is ready
    threading.Timer(1.5, open_browser).start()

    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)
