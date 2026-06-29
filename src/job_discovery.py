"""Headless Job Discovery Engine — combines python-jobspy with custom API sources.

Tier 1: python-jobspy (LinkedIn, Indeed, Glassdoor, Google Jobs, ZipRecruiter, Bayt, Naukri, BDJobs)
Tier 2: Custom API scrapers via src/sources/aggregate.py
        (RemoteOK, Remotive, Arbeitnow, Himalayas, Jobicy, WeWorkRemotely,
         HackerNews Who Is Hiring, Builtin, Greenhouse, Lever, Ashby, Adzuna)
"""
import logging
from typing import List, Dict, Any
import pandas as pd
from src import db

logger = logging.getLogger(__name__)


def run_jobspy_discovery(search_term: str, location: str, results_wanted: int = 50) -> List[Dict[str, Any]]:
    """
    Tier 1: Hits LinkedIn, Indeed, Glassdoor, Google Jobs, ZipRecruiter,
    Bayt, Naukri, and BDJobs headlessly via python-jobspy.
    """
    logger.info(f"[Tier 1] Running JobSpy for '{search_term}' in '{location}'")
    try:
        from jobspy import scrape_jobs
        from src import config

        proxy_url = config.get_secret("proxycurl_api_key", "PROXY_URL")
        proxy_dict = {"http": proxy_url, "https": proxy_url} if (proxy_url and proxy_url.startswith("http")) else None
        
        jobs_df: pd.DataFrame = scrape_jobs(
            site_name=["linkedin", "indeed", "glassdoor", "google", "zip_recruiter"],
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=72,  # Last 3 days
            proxies=proxy_dict
        )
        
        scraped_jobs = []
        for _, row in jobs_df.iterrows():
            job_dict = {
                "dedupe_key": f"{row.get('site', 'unknown')}_{row.get('id', '')}",
                "source": row.get('site', 'jobspy'),
                "source_job_id": str(row.get('id', '')),
                "title": row.get('title', 'Unknown Title'),
                "company": row.get('company', 'Unknown Company'),
                "location": row.get('location', 'Remote'),
                "url": row.get('job_url', ''),
                "description": row.get('description', ''),
                "salary_range": f"{row.get('min_amount', '')} - {row.get('max_amount', '')}",
                "requirements": "",
                "benefits": str(row.get('emails', '')),
                "raw": {k: str(v) for k, v in row.to_dict().items()}
            }
            scraped_jobs.append(job_dict)
            
        return scraped_jobs
    except Exception as e:
        logger.error(f"JobSpy scrape failed: {e}")
        return []


def run_api_discovery(search_term: str, per_source_limit: int = 30) -> List[Dict[str, Any]]:
    """
    Tier 2: Hits all custom API sources (RemoteOK, Remotive, Arbeitnow,
    Himalayas, Jobicy, WeWorkRemotely, HackerNews, Builtin,
    Greenhouse, Lever, Ashby, Adzuna) via src/sources/aggregate.py.
    """
    logger.info(f"[Tier 2] Running API discovery for '{search_term}'")
    try:
        from src.sources.aggregate import fetch_all
        
        prefs = {
            "titles": [search_term] if search_term else [],
            "keywords": search_term.split() if search_term else [],
            "exclude": [],
        }
        
        jobs, errors = fetch_all(prefs, per_source_limit=per_source_limit)
        
        if errors:
            for source, err in errors.items():
                logger.warning(f"[Tier 2] Source '{source}' failed: {err}")
        
        logger.info(f"[Tier 2] Fetched {len(jobs)} jobs from API sources ({len(errors)} errors)")
        return jobs
        
    except Exception as e:
        logger.error(f"API discovery failed: {e}")
        return []


def discover_and_ingest(search_term: str, location: str, results_wanted: int = 20) -> int:
    """Runs both Tier 1 (JobSpy) and Tier 2 (APIs) discovery, deduplicates, and upserts into local DB."""
    
    # Tier 1: Major job boards via JobSpy
    tier1_jobs = run_jobspy_discovery(search_term, location, results_wanted)
    logger.info(f"[Tier 1] Found {len(tier1_jobs)} jobs via JobSpy")
    
    # Tier 2: Remote boards, ATS APIs, HackerNews
    tier2_jobs = run_api_discovery(search_term, per_source_limit=results_wanted)
    logger.info(f"[Tier 2] Found {len(tier2_jobs)} jobs via API sources")
    
    # Combine and deduplicate by URL
    all_jobs = tier1_jobs + tier2_jobs
    seen_urls: set = set()
    unique_jobs = []
    for job in all_jobs:
        url = job.get("url", "")
        if url and url in seen_urls:
            continue
        seen_urls.add(url)
        unique_jobs.append(job)
    
    logger.info(f"[Discovery] {len(unique_jobs)} unique jobs after dedup (from {len(all_jobs)} total)")
    
    ingested_count = 0
    for job in unique_jobs:
        try:
            job_id = db.upsert_job(job)
            ingested_count += 1
        except Exception as e:
            logger.error(f"Failed to ingest job {job.get('title')}: {e}")
            
    return ingested_count
