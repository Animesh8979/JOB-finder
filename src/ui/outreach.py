"""Recruiter outreach page: draft a personalized, compliant email. Drafts only."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from .. import config, db, outreach


def render() -> None:
    st.title("✉️ Recruiter outreach")
    st.caption("Draft a tailored email to a recruiter **you** found. Nothing is ever sent "
               "automatically — you get a draft to review and send yourself.")

    ready = config.readiness()
    if not ready["ai_key"] or not ready["resume"]:
        st.warning("Finish **Home & Setup** first: connect the AI and upload your resume.")
        return

    profile = config.load_profile() or {}
    prefs = config.load_prefs()

    used, cap = outreach.usage_today(prefs)
    remaining = max(0, cap - used)
    st.progress(min(used / cap, 1.0), text=f"{used}/{cap} outreach emails logged today")
    if remaining == 0:
        st.warning("You've hit today's outreach limit. This keeps your outreach targeted, not "
                   "spammy. The limit resets tomorrow (adjust it on Home & Setup).")

    st.info("Only email recruiters whose address you obtained legitimately (job post, company "
            "site, mutual intro). No scraping or bought lists — that's spam and hurts you.")

    # Optional: tie the email to a saved job for richer context.
    apps = db.list_applications()
    job_choices = {0: "— none —"} | {a["job_id"]: f"{a['title']} — {a['company']}" for a in apps}
    sel_job = st.selectbox("Relate to a saved job (optional)", list(job_choices),
                           format_func=lambda i: job_choices[i])
    job = db.get_job(sel_job) if sel_job else None

    with st.form("contact_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Recruiter name", placeholder="Alex Morgan")
        email = c2.text_input("Recruiter email", placeholder="alex@company.com")
        company = c1.text_input("Company", value=(job or {}).get("company", ""))
        role = c2.text_input("Role / title", value=(job or {}).get("title", ""))
        tone = c1.selectbox("Tone", ["Professional", "Warm", "Concise", "Enthusiastic"])
        extra = c2.text_input("Anything to mention? (optional)")
        gen = st.form_submit_button("✍️ Generate draft", type="primary")

    if gen:
        if not email:
            st.error("Add the recruiter's email so we can prepare the draft.")
        else:
            contact = {"name": name, "email": email, "company": company, "role": role}
            try:
                with st.spinner("Writing a tailored draft…"):
                    subject, body = outreach.draft_email(contact, job, profile, prefs, tone, extra)
                st.session_state["outreach_draft"] = {
                    "contact": contact, "subject": subject, "body": body, "job_id": sel_job,
                }
            except Exception as e:
                st.error(str(e))

    draft = st.session_state.get("outreach_draft")
    if draft:
        st.divider()
        st.subheader("Your draft")
        subject = st.text_input("Subject", value=draft["subject"])
        body = st.text_area("Body", value=draft["body"], height=340)

        col1, col2, col3 = st.columns(3)
        save_disabled = remaining == 0
        if col1.button("💾 Save as .eml draft", disabled=save_disabled, use_container_width=True):
            job_obj = db.get_job(draft["job_id"]) if draft["job_id"] else None
            path = outreach.save_eml(draft["contact"], subject, body, prefs)
            outreach.record(draft["contact"], job_obj, subject, body, channel="eml", status="draft")
            st.session_state["outreach_eml"] = path
            st.success("Saved a .eml draft — download it below and open in your mail app to send.")
            st.rerun()

        if col2.button("✅ I sent this manually", disabled=save_disabled, use_container_width=True):
            job_obj = db.get_job(draft["job_id"]) if draft["job_id"] else None
            outreach.record(draft["contact"], job_obj, subject, body, channel="manual", status="sent_manually")
            st.success("Logged as sent. Nice work.")
            st.rerun()

        col3.caption("Tip: open the .eml in Outlook/Gmail to review once more before sending.")

        eml = st.session_state.get("outreach_eml")
        if eml and Path(eml).exists():
            with open(eml, "rb") as fh:
                st.download_button("⬇️ Download .eml draft", fh.read(),
                                   file_name=Path(eml).name, mime="message/rfc822")

    # Recent outreach log
    log = db.list_outreach()
    if log:
        with st.expander(f"Recent outreach ({len(log)})"):
            for row in log[:30]:
                st.write(f"**{row.get('contact_name') or row.get('contact_email','?')}** · "
                         f"{row['status']} · {row.get('created_at','')[:10]} — {row['subject']}")
