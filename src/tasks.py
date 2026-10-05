from huey import SqliteHuey
from src import config, db, scraper, matcher, outreach
from typing import Optional
import time
import random

# Use a purely local SQLite task queue with WAL mode to eliminate write-lock starvation.
huey = SqliteHuey(
    filename=str(config.DATA_DIR / 'huey.db'),
    pragmas={"journal_mode": "wal", "busy_timeout": 5000, "synchronous": "normal"}
)

@huey.task(retries=3, retry_delay=10)
def run_apify_scraping_task(query: str, location: str, limit: int, run_id: Optional[str] = None):
    """Event-driven choregraphy: scrapes jobs and implicitly chains scoring upon completion."""
    if run_id:
        db.update_run_status(run_id, "running")
    try:
        jobs = scraper.scrape_jobs_with_apify(query, location, limit)
        for job in jobs:
            db.upsert_job(job)
        if run_id:
            db.update_run_status(run_id, "completed")
        # Chain the scoring task directly rather than relying on arbitrary time.sleep()
        if config.provider_ready():
            run_score_all_task()
    except Exception as e:
        if run_id:
            db.update_run_status(run_id, "failed", str(e))
        print(f"Apify huey task error: {e}")
        raise

@huey.task(retries=3, retry_delay=10)
def run_score_all_task(run_id: Optional[str] = None):
    """Scores all unscored jobs in batch."""
    if run_id:
        db.update_run_status(run_id, "running")
    try:
        unscored = db.unscored_jobs(limit=100)
        if not unscored:
            if run_id:
                db.update_run_status(run_id, "completed")
            return
        profile = config.load_profile() or {}
        prefs = config.load_prefs()
        
        # Pre-filter to save LLM tokens
        filtered_jobs = matcher.pre_filter_jobs(unscored, profile, threshold=0.25)
        
        # Set score to 1 for jobs that failed the pre-filter so they don't get picked up again
        filtered_ids = {j["id"] for j in filtered_jobs}
        for job in unscored:
            if job["id"] not in filtered_ids:
                db.set_job_score(
                    job["id"],
                    0,
                    f"Failed pre-filter (sim: {job.get('_pre_score', 0)})",
                    score_breakdown={"skills": 0, "role": 0, "seniority": 0, "location": 0, "salary": 0, "freshness": 0},
                    red_flags=["Failed pre-filter similarity threshold"],
                )
                
        if not filtered_jobs:
            if run_id:
                db.update_run_status(run_id, "completed")
            return
            
        scored_results = matcher.score_jobs(filtered_jobs, profile, prefs)
        for item in scored_results:
            db.set_job_score(
                item["job"]["id"],
                item["score"],
                item["reason"],
                score_breakdown=item.get("breakdown"),
                red_flags=item.get("red_flags"),
            )
            
        if run_id:
            db.update_run_status(run_id, "completed")
    except Exception as e:
        if run_id:
            db.update_run_status(run_id, "failed", str(e))
        print(f"Match all huey task error: {e}")
        raise

@huey.task()
def process_outreach_queue_task(contact_ids: list[int], job_ids: list[Optional[int]], tone: str, extra_notes: str):
    """Processes outreach emails securely in background with random jitter."""
    prefs = config.load_prefs()
    profile = config.load_profile() or {}
    
    for idx, contact_id in enumerate(contact_ids):
        used, cap = outreach.usage_today(prefs)
        if used >= cap:
            print(f"[Outreach Queue] Daily cap of {cap} reached. Stopping queue processing.")
            break
            
        contact = db.get_contact(contact_id)
        if not contact:
            continue
            
        job_id = job_ids[idx] if idx < len(job_ids) else None
        job = db.get_job(job_id) if job_id else None
        
        try:
            subject, body = outreach.draft_email(contact, job, profile, prefs, tone=tone, extra=extra_notes)
            eml_path = outreach.save_eml(contact, subject, body, prefs)
            db.add_outreach(
                contact_id=contact_id,
                job_id=job_id,
                subject=subject,
                body=body,
                channel="eml",
                status="draft"
            )
            print(f"[Outreach Queue] Generated email draft for {contact.get('email')} -> {eml_path}")
        except Exception as e:
            print(f"[Outreach Queue] Error generating outreach for contact {contact_id}: {e}")
            
        # Stealth proxy / Organic jitter: avoid sending API rate limit spikes
        time.sleep(random.uniform(2.0, 5.0))

@huey.task(retries=1, retry_delay=10)
def run_auto_apply_task(job_id: int, run_id: Optional[str] = None):
    """
    Background worker task to run the Playwright auto-apply sequence.
    This prevents the FastAPI web server from blocking during execution.
    """
    if run_id:
        db.update_run_status(run_id, "running")
        
    job = db.get_job(job_id)
    if not job:
        print(f"[Auto-Apply Queue] Job {job_id} not found.")
        if run_id:
            db.update_run_status(run_id, "failed", "Job not found")
        return
        
    profile = config.load_profile()
    if not profile:
        print("[Auto-Apply Queue] Profile not configured. Cannot auto-apply.")
        if run_id:
            db.update_run_status(run_id, "failed", "Profile not configured")
        return
        
    from src import profile_parser
    profile_text = profile_parser.profile_context(profile)
    
    from src.auto_apply import connect_and_apply
    import asyncio
    
    # Run the async Playwright function inside the sync Huey worker
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(connect_and_apply(job["url"], profile_text))
        loop.close()
        
        if result.get("status") == "success":
            print(f"[Auto-Apply Queue] Successfully prefilled job {job_id}.")
            db.update_application(job_id, status="prefilled", notes="Processed via Auto-Apply Queue (Ready for Review).")
            if run_id:
                db.update_run_status(run_id, "completed")
        else:
            print(f"[Auto-Apply Queue] Failed to process job {job_id}: {result.get('message')}")
            if run_id:
                db.update_run_status(run_id, "failed", result.get("message"))
    except Exception as e:
        if run_id:
            db.update_run_status(run_id, "failed", str(e))
        print(f"[Auto-Apply Queue] Error: {e}")
        raise

