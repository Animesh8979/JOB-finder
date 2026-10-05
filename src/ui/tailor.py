"""Tailor page: generate a tailored resume + cover letter for a chosen job."""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from .. import config, db, documents, tailor, insights


def _job_options() -> list[dict]:
    """Saved jobs first, then any other scored jobs."""
    saved = {a["job_id"]: a for a in db.list_applications()}
    jobs = db.list_jobs(only_scored=False, limit=300)
    jobs.sort(key=lambda j: (j["id"] not in saved, -(j.get("match_score") or 0)))
    return jobs


def _download_row(paths: dict) -> None:
    cols = st.columns(4)
    specs = [
        ("resume_docx", "⬇️ Resume (Word)", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("resume_pdf", "⬇️ Resume (PDF)", "application/pdf"),
        ("cover_docx", "⬇️ Cover letter (Word)", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("cover_pdf", "⬇️ Cover letter (PDF)", "application/pdf"),
    ]
    for col, (key, label, mime) in zip(cols, specs):
        p = paths.get(key)
        if p and Path(p).exists():
            with open(p, "rb") as fh:
                col.download_button(label, fh.read(), file_name=Path(p).name, mime=mime,
                                    key=f"dl_{key}_{Path(p).stem}", use_container_width=True)


def render() -> None:
    st.title("✍️ Tailor resume + cover letter")

    ready = config.readiness()
    if not ready["ai_key"] or not ready["resume"]:
        st.warning("Finish **Home & Setup** first: connect the AI and upload your resume.")
        return

    jobs = _job_options()
    if not jobs:
        st.info("No jobs yet. Go to **🔎 Find jobs** to pull and save some first.")
        return

    profile = config.load_profile()
    prefs = config.load_prefs()

    # Sidebar design configuration
    st.sidebar.markdown("🎨 **Resume & Cover Letter Design**")
    template = st.sidebar.selectbox("Template Style", ["Corporate", "Minimalist", "Modern"])
    font = st.sidebar.selectbox("Font Face", ["Calibri", "Arial", "Georgia", "Times New Roman"])
    accent_color = st.sidebar.color_picker("Accent Color", value="#1F4E79")
    margin = st.sidebar.slider("Page Margin (mm)", 10, 30, 18)

    style_config = {
        "template": template,
        "font": font,
        "accent_color": accent_color,
        "margin": margin,
    }


    labels = {
        j["id"]: f"{'⭐ ' if db.get_application(j['id']) else ''}"
                 f"[{j.get('match_score') or '–'}/10] {j['title']} — {j['company']}"
        for j in jobs
    }
    job_id = st.selectbox("Choose a job", list(labels), format_func=lambda i: labels[i])
    job = db.get_job(job_id)
    app = db.get_application(job_id)

    with st.expander("Job description"):
        if job.get("apply_url"):
            st.markdown(f"[🔗 Open posting]({job['apply_url']})")
        st.write((job.get("description") or "")[:5000])

    st.divider()
    tab_resume, tab_cover, tab_ats, tab_prep = st.tabs(["📄 Tailored resume", "✉️ Cover letter", "🤖 ATS Optimizer", "🎤 Interview Prep"])

    # ---- Resume ----
    with tab_resume:
        c1, c2 = st.columns([2, 1])
        angle = c1.selectbox("Resume Angle / Focus (A/B Testing)", ["Balanced (Default)", "Leadership & Management", "Technical Depth & Architecture", "Product & Business Impact"])
        
        if st.button("✨ Generate tailored resume", type="primary"):
            try:
                with st.spinner("Tailoring your resume to this job…"):
                    resume = tailor.tailor_resume(job, profile, prefs, angle=angle)
                    cover_existing = (app or {}).get("cover_letter_text") or ""
                    paths = documents.generate_documents(job, resume, cover_existing, style_config=style_config)
                db.update_application(
                    job_id,
                    tailored_resume_text=json.dumps(resume),
                    tailored_resume_path=paths["resume_pdf"],
                    status="Tailored",
                )
                st.session_state[f"docs_{job_id}"] = paths
                st.success("Done! Preview below, then download.")
            except Exception as e:
                st.error(str(e))

        stored = (app or {}).get("tailored_resume_text")
        if stored:
            try:
                resume = json.loads(stored)
            except Exception:
                resume = None
            if resume:
                st.markdown(f"### {resume.get('name','')}")
                st.caption(resume.get("contact", ""))
                if resume.get("summary"):
                    st.write(resume["summary"])
                if resume.get("skills"):
                    st.markdown("**Skills:** " + ", ".join(map(str, resume["skills"])))
                for exp in resume.get("experience", []):
                    st.markdown(f"**{exp.get('title','')}** — {exp.get('company','')}  "
                                f"·  _{exp.get('dates','')}_")
                    for b in exp.get("bullets", []):
                        st.markdown(f"- {b}")
                if f"docs_{job_id}" in st.session_state:
                    _download_row(st.session_state[f"docs_{job_id}"])
        else:
            st.caption("No tailored resume yet — click the button above.")

    # ---- Cover letter ----
    with tab_cover:
        c1, c2, c3 = st.columns([1, 1, 2])
        angle_choice = c1.selectbox("Strategic Angle", [
            "Vision (Company Mission & Trajectory)",
            "Problem-Solver (JD Technical Bottlenecks)",
            "Methodology (Engineering Rigor & CI/CD)",
            "Direct / Executive (Metric-Dense & Concise)"
        ])
        angle_key_map = {
            "Vision (Company Mission & Trajectory)": "vision",
            "Problem-Solver (JD Technical Bottlenecks)": "problem_solver",
            "Methodology (Engineering Rigor & CI/CD)": "methodology",
            "Direct / Executive (Metric-Dense & Concise)": "direct_executive"
        }
        tone = c2.selectbox("Tone", ["Professional", "Warm", "Enthusiastic", "Concise"])
        extra = c3.text_input("Anything specific to mention? (optional)",
                              placeholder="e.g. I'm relocating, available immediately, referral from…")
        if st.button("✨ Generate Strategic Cover Letter", type="primary"):
            try:
                with st.spinner("Writing your strategic cover letter…"):
                    letter = tailor.generate_strategic_cover_letter(
                        job, profile, prefs, angle_key=angle_key_map[angle_choice], tone=tone, extra_notes=extra
                    )
                db.update_application(job_id, cover_letter_text=letter, status="Tailored")
                st.session_state[f"cover_{job_id}"] = letter
                st.success(f"Strategic draft ready ({angle_choice}) — edit it below if you like.")
            except Exception as e:
                st.error(str(e))

        current = st.session_state.get(f"cover_{job_id}") or (app or {}).get("cover_letter_text") or ""
        edited = st.text_area("Cover letter", value=current, height=320)
        if edited and st.button("💾 Save & export cover letter"):
            try:
                resume_stored = (db.get_application(job_id) or {}).get("tailored_resume_text")
                resume = json.loads(resume_stored) if resume_stored else {"name": prefs["identity"].get("full_name", "")}
                paths = documents.generate_documents(job, resume, edited, style_config=style_config)
                
                # Modern Playwright PDF rendering
                from .. import pdf_engine
                modern_pdf_path = config.OUTPUTS_DIR / f"modern_{job_id}_{job.get('company','').replace(' ','_')}.pdf"
                pdf_engine.generate_modern_pdf(resume, modern_pdf_path)
                paths["modern_pdf"] = str(modern_pdf_path)

                db.update_application(job_id, cover_letter_text=edited, cover_letter_path=paths["cover_pdf"])
                st.session_state[f"docs_{job_id}"] = paths
                st.success("Saved and exported. Includes Modern Space Grotesk / DM Sans PDF!")
                _download_row(paths)
            except Exception as e:
                st.error(str(e))

    # ---- ATS Optimizer ----
    with tab_ats:
        st.subheader("🤖 ATS Keyword Optimizer")
        stored_resume_text = (app or {}).get("tailored_resume_text")
        if not stored_resume_text:
            st.info("Generate a tailored resume first to run the ATS optimizer.")
        else:
            if st.button("🔍 Run ATS Keyword Audit", type="primary"):
                with st.spinner("Analyzing ATS coverage..."):
                    resume_json = json.loads(stored_resume_text)
                    resume_raw_text = json.dumps(resume_json) # simple text rep
                    
                    ats_res = insights.ats_coverage(resume_raw_text, job.get("description", ""))
                    st.metric("ATS Match", f"{ats_res['coverage']}%")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.success("✅ **Keywords Found**")
                        for w in ats_res["present"]:
                            st.write(f"- {w}")
                    with c2:
                        st.error("❌ **Missing Keywords**")
                        for w in ats_res["missing"]:
                            st.write(f"- {w}")
                    
                    st.divider()
                    st.subheader("🛡️ Fabrication Check")
                    flags = insights.flag_possible_fabrication(resume_json, profile)
                    if flags:
                        st.warning("⚠️ **Potential Fabrications Detected**")
                        st.caption("The AI may have hallucinated these skills since they don't appear in your original profile.")
                        for f in flags:
                            st.write(f"- {f}")
                    else:
                        st.success("No fabricated skills detected! The resume looks grounded in your original profile.")

    # ---- Interview Prep ----
    with tab_prep:
        st.subheader("🏢 Company Dossier & 🎤 Interview Prep")
        if st.button("✨ Generate Interview Intelligence", type="primary"):
            c1, c2 = st.columns(2)
            with c1:
                with st.spinner("Compiling company dossier..."):
                    dossier = insights.generate_company_dossier(job.get("company", ""), job.get("title", ""), job.get("description", ""), prefs)
                    if dossier:
                        st.markdown("### 🏢 Company Overview")
                        st.write(dossier.get("overview", ""))
                        st.markdown("**Likely Tech Stack:** " + ", ".join(dossier.get("likely_tech_stack", [])))
                        st.markdown("**Culture Signals:** " + dossier.get("culture_signals", ""))
                        st.markdown("**Why Join:**")
                        for w in dossier.get("why_join_angles", []):
                            st.write(f"- {w}")
            with c2:
                with st.spinner("Generating mock interview..."):
                    prep = insights.generate_interview_prep(job, profile, prefs)
                    if prep:
                        st.markdown("### 🗣️ Behavioral Questions")
                        for i, q in enumerate(prep.get("behavioral_questions", [])):
                            with st.expander(f"Q{i+1}: {q.get('question', '')}"):
                                st.markdown("**Sample Answer Points:**")
                                for b in q.get("sample_answer_bullet_points", []):
                                    st.write(f"- {b}")
                        
                        st.markdown("### 💻 Technical Questions")
                        for i, q in enumerate(prep.get("technical_questions", [])):
                            with st.expander(f"Q{i+1}: {q.get('question', '')}"):
                                st.markdown("**Key Talking Points:**")
                                for b in q.get("key_talking_points", []):
                                    st.write(f"- {b}")

                        st.markdown("### 🙋 Questions to Ask Them")
                        for q in prep.get("questions_to_ask_them", []):
                            st.write(f"- {q}")
