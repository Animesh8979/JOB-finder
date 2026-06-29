import os
import sys
import time
import requests
import sqlite3
import random

API_BASE = "http://127.0.0.1:8000/api"

def get_db_connection():
    return sqlite3.connect("data/jobfinder.db")

def start_mining():
    print("[SYSTEM] Initiating autonomous mining cycle...")
    
    # 1. Trigger Apify Scrape
    try:
        res = requests.post(f"{API_BASE}/jobs/apify", json={
            "query": "Software Engineer",
            "location": "Remote",
            "limit": 10
        }, timeout=10)
        print("[APIFY] Trigger response:", res.status_code, res.json())
    except Exception as e:
        print("[APIFY] Background fetch initiation failed:", e)

    # 2. Wait for jobs to settle in DB (Simulation or actual wait)
    print("[SYSTEM] Waiting for scraping ingestion...")
    time.sleep(15)

    # 3. Batch Score All Jobs
    try:
        res = requests.post(f"{API_BASE}/jobs/score-all", timeout=10)
        print("[AI] Batch scoring triggered:", res.status_code, res.json())
    except Exception as e:
        print("[AI] Batch scoring trigger failed:", e)
        
    time.sleep(10)

    # 4. Enrich Contacts for New Top Jobs
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, company FROM jobs WHERE match_score >= 6 ORDER BY match_score DESC LIMIT 5")
    top_jobs = c.fetchall()
    conn.close()

    if not top_jobs:
        print("[ENRICH] No high-scoring jobs found to enrich yet.")
        return

    for job_id, company in top_jobs:
        print(f"[ENRICH] Hunting recruiter contacts for {company} (Job ID {job_id})...")
        try:
            res = requests.post(f"{API_BASE}/contacts/enrich", json={
                "company_name": company,
                "job_id": job_id
            }, timeout=45)
            print(f"[ENRICH] Results for {company}:", res.json())
        except Exception as e:
            print(f"[ENRICH] Proxycurl failed for {company}:", e)
        time.sleep(random.uniform(3.0, 7.0)) # Stagger requests

    # 5. Generate Outreach Drafts
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, job_id, email FROM contacts WHERE job_id IS NOT NULL LIMIT 5")
    contacts = c.fetchall()
    conn.close()

    if contacts:
        contact_ids = [c[0] for c in contacts]
        job_ids = [c[1] for c in contacts]
        print(f"[OUTREACH] Queueing automated emails for {len(contacts)} leads...")
        try:
            res = requests.post(f"{API_BASE}/outreach/queue", json={
                "contact_ids": contact_ids,
                "job_ids": job_ids,
                "tone": "Enthusiastic and concise",
                "extra_notes": "Mention open source contributions"
            }, timeout=10)
            print("[OUTREACH] Queue response:", res.status_code, res.json())
        except Exception as e:
            print("[OUTREACH] Queue trigger failed:", e)

if __name__ == "__main__":
    while True:
        try:
            start_mining()
            print("[SYSTEM] Sleeping for 4 hours before next cycle...")
            time.sleep(4 * 3600)
        except KeyboardInterrupt:
            print("[SYSTEM] Autonomous miner terminated.")
            break
        except Exception as e:
            print("[SYSTEM] Unhandled exception:", e)
            time.sleep(60)
