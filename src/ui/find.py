"""Find jobs page: pull remote jobs from free APIs and AI-rank them against your resume."""
from __future__ import annotations

import streamlit as st

import urllib.parse
from datetime import datetime, timezone
from .. import config, db, matcher, scraper, insights
from ..sources import aggregate


def _score_badge(score: int | None) -> str:
    if not score:
        return "⬜ —"
    if score >= 80 or (score <= 10 and score >= 8):
        return f"🟢 {score}{'/100' if score > 10 else '/10'}"
    if score >= 60 or (score <= 10 and score >= 6):
        return f"🟡 {score}{'/100' if score > 10 else '/10'}"
    return f"🔴 {score}{'/100' if score > 10 else '/10'}"


def _fetch_and_score(prefs: dict, per_source_limit: int) -> None:
    with st.spinner("Searching job boards…"):
        jobs, errors = aggregate.fetch_all(prefs, per_source_limit=per_source_limit)
        for job in jobs:
            db.upsert_job(job)

    if errors:
        st.warning("Some sources had trouble: " + "; ".join(f"{k} ({v[:60]})" for k, v in errors.items()))
    st.success(f"Fetched {len(jobs)} matching jobs. Scoring the new ones…")

    profile = config.load_profile()
    unscored = db.unscored_jobs(limit=250)
    if unscored:
        bar = st.progress(0.0, text="Scoring jobs with AI…")
        scored = matcher.score_jobs(
            unscored, profile, prefs,
            progress=lambda done, total: bar.progress(done / total, text=f"Scoring {done}/{total}…"),
        )
        for item in scored:
            db.set_job_score(
                item["job"]["id"],
                item["score"],
                item["reason"],
                score_breakdown=item.get("breakdown"),
                red_flags=item.get("red_flags"),
            )
        bar.empty()
    st.rerun()


def _parse_and_score_custom_url(url: str, prefs: dict) -> None:
    with st.spinner("Scraping job page..."):
        try:
            text = scraper.scrape_url_text(url)
        except Exception as e:
            st.error(f"Failed to scrape: {e}")
            return

    if not text or len(text.strip()) < 100:
        st.error("Could not retrieve enough text content from the URL.")
        return

    with st.spinner("Parsing job details with AI..."):
        try:
            job = scraper.parse_job_from_text(text, url)
        except Exception as e:
            st.error(f"Failed to parse job with AI: {e}")
            return

    with st.spinner("Scoring job..."):
        profile = config.load_profile()
        try:
            results = matcher.score_jobs([job], profile, prefs)
            if results:
                job_id = db.upsert_job(job)
                res = results[0]
                db.set_job_score(
                    job_id,
                    res["score"],
                    res["reason"],
                    score_breakdown=res.get("breakdown"),
                    red_flags=res.get("red_flags"),
                )
                db.get_or_create_application(job_id) # Save to tracker
                st.success(f"Job parsed, saved, and scored as {res['score']}/100!")
                st.toast("Job saved to your tracker!")
                st.rerun()
            else:
                st.error("Failed to score the job.")
        except Exception as e:
            st.error(f"Failed to score: {e}")



def render() -> None:
    st.title("🔎 Find jobs")

    prefs = config.load_prefs()
    ready = config.readiness()
    if not ready["ai_key"] or not ready["resume"]:
        st.warning("Finish **Home & Setup** first: connect the AI and upload your resume.")
        return

    tab_boards, tab_url = st.tabs(["🔎 Fetch from job boards", "🔗 Paste custom job URL"])

    with tab_boards:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.caption(
                    "Pulls from your selected free sources (no scraping), then the AI ranks each "
                    "job 1–10 against your resume."
                )
                limit = st.slider("Max jobs to pull per source", 10, 100, 50, step=10)
            with c2:
                st.write("")
                st.write("")
                if st.button("🔎 Find fresh jobs", type="primary", use_container_width=True):
                    _fetch_and_score(prefs, limit)

    with tab_url:
        with st.container(border=True):
            with st.form("custom_url_form", clear_on_submit=True):
                custom_url = st.text_input("Job posting URL", placeholder="e.g. https://www.linkedin.com/jobs/view/123456")
                submit_custom = st.form_submit_button("✨ Parse, Score & Save Job", type="primary")
                if submit_custom:
                    if not custom_url.strip():
                        st.error("Please enter a valid URL.")
                    else:
                        _parse_and_score_custom_url(custom_url, prefs)

    # --- Filters over what's already in the database ---
    st.divider()
    f1, f2, f3 = st.columns([1, 1, 2])
    min_score = f1.slider("Minimum match score", 1, 10, 6)
    only_unsaved = f2.toggle("Hide already-saved", value=False)
    search = f3.text_input("Search title / company / text", "")

    jobs = db.list_jobs(only_scored=True, min_score=min_score, search=search, limit=300)
    st.caption(f"{len(jobs)} jobs at score ≥ {min_score}.")

    for job in jobs:
        app = db.get_application(job["id"])
        if only_unsaved and app:
            continue
        with st.container(border=True):
            top = st.columns([6, 2, 2])
            top[0].markdown(f"**{job['title']}** — {job['company']}")
            
            # Freshness Radar
            fresh_badge = ""
            if job.get('fetched_at'):
                try:
                    # ISO format parsing handle
                    fetched_dt = datetime.fromisoformat(job['fetched_at'].replace('Z', '+00:00'))
                    days_old = (datetime.now(timezone.utc) - fetched_dt).days
                    if days_old <= 2:
                        fresh_badge = " 🔥 **Fresh (<48h)**"
                    elif days_old <= 7:
                        fresh_badge = " ⚡ **Recent (<7d)**"
                except Exception:
                    pass

            top[0].caption(f"📍 {job['location']}  ·  source: {job['source']}{fresh_badge}")
            top[1].markdown(_score_badge(job.get("match_score")))
            if app:
                top[2].success(f"✓ {app['status']}")
            else:
                if top[2].button("⭐ Save", key=f"save_{job['id']}", use_container_width=True):
                    db.get_or_create_application(job["id"])
                    st.rerun()

            if job.get("match_reason"):
                st.caption(f"💡 {job['match_reason']}")
            if job.get("salary_min") or job.get("salary_max"):
                st.caption(f"💰 {job.get('salary_min') or '?'}–{job.get('salary_max') or '?'} {job.get('currency','')}")

            flags = insights.detect_red_flags(job.get("description", ""))
            if flags:
                with st.expander("🚩 Red Flags Detected"):
                    for category, phrases in flags.items():
                        st.write(f"**{category}**: {', '.join(phrases)}")

            with st.expander("Description & link"):
                c_links = st.columns(2)
                if job.get("apply_url"):
                    c_links[0].markdown(f"[🔗 Open the job posting]({job['apply_url']})")
                
                # Warm Intro Finder (LinkedIn X-Ray)
                company_enc = urllib.parse.quote(f'"{job["company"]}" (recruiter OR talent OR hiring)')
                xray_url = f"https://www.google.com/search?q=site:linkedin.com/in+{company_enc}"
                c_links[1].markdown(f"[🤝 Find Recruiters on LinkedIn]({xray_url})")
                
                if st.button("💰 Estimate Salary", key=f"salary_{job['id']}"):
                    with st.spinner("Analyzing salary data..."):
                        est = insights.estimate_salary(job, config.load_profile(), prefs)
                        if est:
                            st.success(f"**Estimate:** {est.get('low_range', '?')} - {est.get('high_range', '?')} {est.get('currency', '')} (Median: {est.get('median', '?')})")
                            st.caption(f"*Note:* {est.get('confidence_note', '')}")
                            st.info(f"**Negotiation tip:** {est.get('negotiation_tip', '')}")
                        else:
                            st.error("Could not estimate salary.")

                st.write((job.get("description") or "")[:4000])
