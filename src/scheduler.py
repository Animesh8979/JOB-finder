"""Command-line script for scheduled auto-fetching and scoring of remote jobs.

Designed to be run as a background cron or Windows Task Scheduler task.
Reads preferences, runs aggregate fetching, scores jobs with AI, and logs the execution.
"""
from __future__ import annotations

import datetime
from src import config, db, matcher
from src.sources import aggregate


def main() -> None:
    log_path = config.DATA_DIR / "scheduler_log.txt"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Ensure database is initialized
    db.init_db()

    # Verify setup readiness
    ready = config.readiness()
    if not ready["ai_key"] or not ready["resume"]:
        with open(log_path, "a", encoding="utf-8") as lf:
            lf.write(f"[{timestamp}] ERROR: Setup not complete. AI key or Resume missing in dashboard.\n")
        return

    prefs = config.load_prefs()
    profile = config.load_profile()

    # 1. Fetch fresh jobs
    with open(log_path, "a", encoding="utf-8") as lf:
        lf.write(f"[{timestamp}] Fetching fresh jobs...\n")

    try:
        jobs, errors = aggregate.fetch_all(prefs, per_source_limit=40)
        new_count = 0
        for job in jobs:
            # upsert returns new job id or existing one. We count how many jobs we upserted
            db.upsert_job(job)
            new_count += 1
    except Exception as e:
        with open(log_path, "a", encoding="utf-8") as lf:
            lf.write(f"[{timestamp}] ERROR during aggregation: {e}\n")
        return

    # 2. Score unscored jobs
    unscored = db.unscored_jobs(limit=150)
    scored_count = 0
    high_match_count = 0

    if unscored:
        try:
            scored = matcher.score_jobs(unscored, profile, prefs)
            for item in scored:
                db.set_job_score(item["job"]["id"], item["score"], item["reason"])
                scored_count += 1
                if item["score"] >= 8:
                    high_match_count += 1
        except Exception as e:
            with open(log_path, "a", encoding="utf-8") as lf:
                lf.write(f"[{timestamp}] ERROR during scoring: {e}\n")
            return

    # 3. Log results
    summary = (
        f"[{timestamp}] SUCCESS: Aggregated {new_count} jobs. "
        f"Scored {scored_count} new entries. "
        f"Found {high_match_count} high matches (score >= 8).\n"
    )
    if errors:
        summary += f"    Warnings: Sources with issues: {', '.join(errors.keys())}\n"

    with open(log_path, "a", encoding="utf-8") as lf:
        lf.write(summary)


if __name__ == "__main__":
    main()
