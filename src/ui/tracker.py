"""Tracker page: every saved job, its status, and follow-up reminders."""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from .. import db, config, insights


def render() -> None:
    st.title("📊 Tracker")

    apps = db.list_applications()
    if not apps:
        st.info("Nothing tracked yet. Save jobs on **🔎 Find jobs**, then tailor and apply.")
        return

    # --- Summary metrics ---
    stats = db.application_stats()
    
    st.subheader("📈 Application Funnel Analytics")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Saved", stats["total_saved"])
    c2.metric("Tailored", stats["total_tailored"])
    c3.metric("Applied", stats["total_applied"])
    c4.metric("Interview", stats["total_interview"])
    c5.metric("Offers", stats["total_offer"])
    c6.metric("Rejected", stats["total_rejected"])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Response Rate", f"{stats['response_rate']}%")
    c2.metric("Best Source", stats["best_source"])
    c3.metric("Avg Match Score", f"{stats['avg_score']}/10")

    # --- Follow-up reminders ---
    today = date.today().isoformat()
    due = [a for a in apps if (a.get("follow_up_at") or "") and a["follow_up_at"] <= today
           and a["status"] in ("Applied", "Followed-up")]
    if due:
        st.warning("⏰ **Follow-ups due:** " + "; ".join(f"{a['company']} ({a['title']})" for a in due))

    st.divider()

    # --- CareerOps Pipeline Automation Tools ---
    c_tools1, c_tools2 = st.columns(2)
    with c_tools1:
        with st.expander("📬 reply-watch: Classify Inbound Recruiter Email"):
            inbound_email_text = st.text_area("Paste recruiter email text", height=120, key="inbound_email_box")
            target_job_opts = {a["job_id"]: f"{a['title']} — {a['company']}" for a in apps}
            target_inbound_job = st.selectbox("Related Application", list(target_job_opts), format_func=lambda i: target_job_opts[i], key="inbound_job_sel")
            
            if st.button("🤖 Classify & Auto-Update Pipeline", key="classify_btn"):
                if not inbound_email_text.strip():
                    st.error("Please paste email text.")
                else:
                    with st.spinner("Classifying email..."):
                        from .. import reply_classifier
                        res = reply_classifier.process_reply_and_update_application(target_inbound_job, inbound_email_text, prefs={})
                        st.success(f"Category: {res.get('category')} → Status updated to: {res.get('recommended_status')}")
                        st.info(f"Summary: {res.get('summary')}")
                        if res.get("suggested_response"):
                            st.caption(f"Suggested Next Action: {res.get('suggested_response')}")
                        st.rerun()

    with c_tools2:
        with st.expander("💼 offer-prep: Offer Contract Auditor & Salary Negotiator"):
            offer_tab1, offer_tab2 = st.tabs(["Auditor", "Salary Gap"])
            with offer_tab1:
                contract_txt = st.text_area("Paste offer letter / agreement snippet", height=90, key="contract_box")
                if st.button("⚖️ Audit Contract Clauses", key="audit_contract_btn"):
                    if not contract_txt.strip():
                        st.error("Paste contract text.")
                    else:
                        with st.spinner("Auditing clauses..."):
                            from .. import offer_analyzer
                            audit_res = offer_analyzer.audit_offer_contract(contract_txt)
                            if audit_res["flagged_clauses"]:
                                for f in audit_res["flagged_clauses"]:
                                    st.warning(f"⚠️ **[{f['risk_level']}] {f['category']}**: {f['finding']}")
                            else:
                                st.success("No severe IP or non-compete clauses detected!")
                            with st.expander("Recommended Questions for Legal Counsel"):
                                for q in audit_res.get("lawyer_questions", []):
                                    st.write(f"- {q}")
            with offer_tab2:
                o_base = st.number_input("Offered Base Salary", value=150000, step=5000)
                d_base = st.number_input("Target / Desired Base", value=175000, step=5000)
                m_base = st.number_input("Market Median Benchmark", value=170000, step=5000)
                if st.button("📈 Generate Counter-Offer Script", key="salary_calc_btn"):
                    with st.spinner("Calculating negotiation levers..."):
                        from .. import offer_analyzer
                        sal_res = offer_analyzer.analyze_salary_gap(o_base, d_base, m_base)
                        st.metric("Salary Gap", f"+${sal_res['gap']:,} ({sal_res['gap_percent']}%)")
                        st.code(sal_res["counter_email"], language="text")
                        st.caption("Alternative levers to negotiate:")
                        for lever in sal_res["alternative_levers"]:
                            st.write(f"- {lever}")

    st.divider()

    # --- View Mode Toggle ---
    view_mode = st.radio(
        "View Mode",
        ["📋 Kanban Board", "📊 Spreadsheet Table"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if view_mode == "📋 Kanban Board":
        st.caption("Change status in the card dropdown to move cards between columns.")
        
        KANBAN_COLUMNS = {
            "Saved": ["Saved"],
            "Tailored": ["Tailored"],
            "Applied": ["Applied", "Followed-up"],
            "Interview": ["Interview"],
            "Offer": ["Offer"],
            "Archive": ["Closed", "Rejected"],
        }
        
        k_cols = st.columns(len(KANBAN_COLUMNS))
        for col_idx, (col_name, statuses) in enumerate(KANBAN_COLUMNS.items()):
            with k_cols[col_idx]:
                st.markdown(f"### {col_name} `{sum(1 for a in apps if a['status'] in statuses)}`")
                st.divider()
                for app in apps:
                    if app["status"] in statuses:
                        with st.container(border=True):
                            st.markdown(f"**{app['title']}**")
                            st.markdown(f"*{app['company']}*")
                            
                            score = app.get("match_score")
                            if score:
                                if score >= 8:
                                    st.markdown(f"🟢 **{score}/10**")
                                elif score >= 6:
                                    st.markdown(f"🟡 **{score}/10**")
                                else:
                                    st.markdown(f"🔴 **{score}/10**")
                            
                            if app.get("follow_up_at"):
                                st.caption(f"⏰ Follow-up: {app['follow_up_at']}")
                                
                            # Compact selectbox to change status
                            try:
                                status_idx = db.STATUSES.index(app["status"])
                            except ValueError:
                                status_idx = 0
                                
                            new_status = st.selectbox(
                                "Move to:",
                                db.STATUSES,
                                index=status_idx,
                                key=f"status_sel_{app['job_id']}",
                                label_visibility="collapsed"
                            )
                            if new_status != app["status"]:
                                db.update_application(app["job_id"], status=new_status)
                                st.rerun()
                            
                            # Action links
                            link = app.get("apply_url") or app.get("url") or ""
                            if link:
                                st.markdown(f"[🔗 Open Posting]({link})")
                                
                            if app["status"] == "Applied" and app.get("follow_up_at"):
                                if st.button("✍️ Draft follow-up", key=f"fup_{app['job_id']}"):
                                    with st.spinner("Drafting follow-up..."):
                                        prefs = config.load_prefs()
                                        profile = config.load_profile()
                                        # roughly calculate days since applied, assuming it's 7 for follow-up 1
                                        subj, body = insights.generate_followup_email(app, profile, prefs, 1, 7)
                                        st.session_state[f"draft_fup_{app['job_id']}"] = (subj, body)
                                    
                            if f"draft_fup_{app['job_id']}" in st.session_state:
                                subj, body = st.session_state[f"draft_fup_{app['job_id']}"]
                                st.text_input("Subject", value=subj, key=f"subj_{app['job_id']}")
                                st.text_area("Body", value=body, key=f"body_{app['job_id']}", height=150)
                                if st.button("📋 Copy & Mark as Followed-up", key=f"copy_{app['job_id']}"):
                                    db.update_application(app['job_id'], status="Followed-up")
                                    st.success("Please copy the text above. Marked as Followed-up!")

                            if app.get("notes"):
                                with st.expander("Notes"):
                                    st.caption(app["notes"])
    else:
        st.caption("Edit **Status**, **Follow-up** (YYYY-MM-DD), or **Notes** directly in the table.")
        original = {a["job_id"]: a for a in apps}
        df = pd.DataFrame([{
            "job_id": a["job_id"],
            "Company": a["company"],
            "Title": a["title"],
            "Status": a["status"],
            "Score": a.get("match_score"),
            "Applied": a.get("applied_at") or "",
            "Follow-up": a.get("follow_up_at") or "",
            "Notes": a.get("notes") or "",
            "Link": a.get("apply_url") or a.get("url") or "",
        } for a in apps])

        edited = st.data_editor(
            df,
            key="tracker_editor",
            hide_index=True,
            num_rows="fixed",
            use_container_width=True,
            column_config={
                "job_id": None,  # hidden
                "Company": st.column_config.TextColumn(disabled=True),
                "Title": st.column_config.TextColumn(disabled=True),
                "Status": st.column_config.SelectboxColumn(options=db.STATUSES, required=True),
                "Score": st.column_config.NumberColumn(disabled=True, format="%d/10"),
                "Applied": st.column_config.TextColumn(disabled=True),
                "Follow-up": st.column_config.TextColumn(help="YYYY-MM-DD, or clear it"),
                "Notes": st.column_config.TextColumn(width="large"),
                "Link": st.column_config.LinkColumn(disabled=True, display_text="open"),
            },
        )

        # Persist any edits back to the database.
        changes = 0
        for row in edited.to_dict("records"):
            jid = row["job_id"]
            orig = original.get(jid, {})
            updates = {}
            if row["Status"] != orig.get("status"):
                updates["status"] = row["Status"]
            if (row["Follow-up"] or "") != (orig.get("follow_up_at") or ""):
                updates["follow_up_at"] = row["Follow-up"] or None
            if (row["Notes"] or "") != (orig.get("notes") or ""):
                updates["notes"] = row["Notes"]
            if updates:
                db.update_application(jid, **updates)
                changes += 1
        if changes:
            st.toast(f"Saved {changes} update(s).")
            st.rerun()

