"""JobSpy Tier-1 Scraping Swarm Integration.

Integrates the powerful JobSpy library to extract jobs from gated Tier-1 domains
(LinkedIn, Indeed, Glassdoor, ZipRecruiter) without triggering captchas.
"""
from __future__ import annotations

import pandas as pd
from typing import Any

from . import base


def fetch(query: str, limit: int, prefs: dict[str, Any]) -> list[dict[str, Any]]:
    """Fetch jobs using JobSpy across multiple top-tier boards."""
    try:
        from jobspy import scrape_jobs
    except ImportError:
        return []

    if not query:
        return []

    # Map settings or defaults
    # LinkedIn excluded by default: ~10 pages/IP rate limit + ToS restriction.
    # Opt in via JOBSPY_LINKEDIN_ENABLED=1 (researched 2026-08).
    import os
    site_names = ["indeed", "glassdoor", "zip_recruiter"]
    if os.getenv("JOBSPY_LINKEDIN_ENABLED", "").lower() in ("1", "true", "yes"):
        site_names.insert(0, "linkedin")
    location = prefs.get("location") or "Remote"
    
    # Optional filtering parameters based on prefs
    remote_only = prefs.get("remote", True)
    is_remote = True if remote_only else False
    
    try:
        jobs_df = scrape_jobs(
            site_name=site_names,
            search_term=query,
            location=location,
            results_wanted=limit,
            is_remote=is_remote,
            country_dict={"indeed": "usa"} # Add specific locales if needed
        )
    except Exception as e:
        print(f"JobSpy error: {e}")
        return []

    if jobs_df.empty:
        return []
        
    # Convert DataFrame to list of dictionaries
    jobs_records = jobs_df.to_dict(orient="records")
    
    out = []
    for record in jobs_records:
        job = base.normalize(
            source=f"jobspy-{record.get('site', 'unknown')}",
            source_job_id=str(record.get('id', '')),
            title=str(record.get('title', '')),
            company=str(record.get('company', '')),
            location=str(record.get('location', 'Remote')),
            url=str(record.get('job_url', '')),
            apply_url=str(record.get('job_url_direct', '') or record.get('job_url', '')),
            description=str(record.get('description', '')),
            salary_min=int(record.get('min_amount')) if not pd.isna(record.get('min_amount')) else None,
            salary_max=int(record.get('max_amount')) if not pd.isna(record.get('max_amount')) else None,
            currency=str(record.get('currency', 'USD')),
            posted_at=str(record.get('date_posted', '')),
            remote=is_remote or ('remote' in str(record.get('location', '')).lower()),
            raw=record
        )
        if base.matches_filters(job, prefs):
            out.append(job)
            
    return out
