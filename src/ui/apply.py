"""Apply page (review-first): open the form pre-filled; you review and submit."""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import streamlit as st

from .. import autofill, config, db


def render() -> None:
    st.title("📤 Apply (review-first)")
    st.caption("The tool fills what it can and opens the form. **You** review every field and "
               "click Submit. It never submits for you.")

    apps = db.list_applications()
    if not apps:
        st.info("Nothing saved yet. Save jobs on **🔎 Find jobs**, then tailor and apply.")
        return

    profile = config.load_profile() or {}
    prefs = config.load_prefs()

    labels = {a["job_id"]: f"[{a['status']}] {a['title']} — {a['company']}" for a in apps}
    job_id = st.selectbox("Choose a saved job", list(labels), format_func=lambda i: labels[i])
    job = db.get_job(job_id)
    app = db.get_application(job_id)

    apply_url = job.get("apply_url") or job.get("url") or ""
    gated = autofill.is_gated(apply_url)

    c1, c2 = st.columns([3, 2])
    with c1:
        if apply_url:
            st.markdown(f"**Posting:** [{apply_url[:70]}…]({apply_url})")
        resume_path = (app or {}).get("tailored_resume_path")
        if resume_path and Path(resume_path).exists():
            st.success("Tailored resume is ready to upload.")
        else:
            st.warning("No tailored resume yet — go to **✍️ Tailor** first so it can be attached.")
        if gated:
            st.info("🔒 Login-gated site (e.g. LinkedIn). It will open in your own browser session "
                    "and **not** auto-fill — paste from the answer sheet below.")

    with c2:
        if st.button("🖥️ Open & pre-fill in browser", type="primary", use_container_width=True,
                     disabled=not apply_url):
            note = autofill.launch_assisted_apply(
                job, resume_path or "", (app or {}).get("cover_letter_text") or "", profile, prefs
            )
            st.success(note)
            st.caption("If no window appears, run setup.bat again to finish the browser install.")

        if st.button("✅ Mark as applied", use_container_width=True):
            db.update_application(
                job_id, status="Applied",
                applied_at=date.today().isoformat(),
                follow_up_at=(date.today() + timedelta(days=7)).isoformat(),
            )
            st.success("Marked as applied. A 7-day follow-up reminder is set (see Tracker).")
            st.rerun()

    st.divider()
    st.subheader("📋 Answer sheet")
    st.caption("Copy any value the form didn't auto-fill.")
    sheet = autofill.answer_sheet(profile, prefs, (app or {}).get("cover_letter_text") or "")
    if not sheet:
        st.info("Fill in your details on **Home & Setup** to populate this.")
    for label, value in sheet.items():
        if label == "Cover letter":
            with st.expander("Cover letter (click to copy)"):
                st.code(value, language=None)
        else:
            st.text_input(label, value=value, key=f"sheet_{job_id}_{label}")
