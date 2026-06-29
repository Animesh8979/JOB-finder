"""Home & Setup page: connect the AI, enter your details, set search preferences.

(The resume upload + parsing section is added in Phase 1.)
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from .. import config, profile_parser



def _to_list(text: str) -> list[str]:
    return [x.strip() for x in (text or "").replace("\n", ",").split(",") if x.strip()]


def _from_list(items: list[str]) -> str:
    return ", ".join(items or [])


def render() -> None:
    st.title("🏠 Home & Setup")
    st.write(
        "Welcome! Set these once and you're ready. Everything is stored **locally** on "
        "your computer. You can change any of it later."
    )

    prefs = config.load_prefs()

    # ---- 1. AI connection ----------------------------------------------------
    st.header("1 · Connect the AI")
    st.caption(
        "The AI scores jobs, tailors your resume, and drafts cover letters & emails. "
        "Claude is the default; Gemini's free tier is an option."
    )
    with st.form("ai_form"):
        provider = st.radio(
            "Provider",
            ["claude", "gemini"],
            index=0 if prefs.get("provider", "claude") == "claude" else 1,
            format_func=lambda p: "Claude (Anthropic) — recommended" if p == "claude"
            else "Google Gemini (free tier)",
            horizontal=True,
        )
        if provider == "claude":
            key = st.text_input(
                "Anthropic API key", value=config.anthropic_key(), type="password",
                help="Get one at https://console.anthropic.com/settings/keys",
            )
        else:
            key = st.text_input(
                "Gemini API key", value=config.gemini_key(), type="password",
                help="Get one at https://aistudio.google.com/apikey — also run: pip install google-generativeai",
            )
        if st.form_submit_button("💾 Save AI settings", type="primary"):
            prefs["provider"] = provider
            config.save_prefs(prefs)
            config.set_secrets(
                {"anthropic_api_key": key} if provider == "claude" else {"gemini_api_key": key}
            )
            st.success("Saved.")
            st.rerun()

    if st.button("🧪 Test AI connection"):
        from .. import llm
        try:
            with st.spinner("Saying hello to the AI…"):
                reply = llm.generate("Reply with exactly: OK", max_tokens=10, temperature=0)
            st.success(f"Working! The AI replied: {reply!r}")
        except Exception as e:  # llm.LLMError or transport
            st.error(str(e))

    st.divider()

    # ---- 2. Resume -----------------------------------------------------------
    _resume_section(prefs)

    st.divider()

    # ---- 3. Your details -----------------------------------------------------
    st.header("3 · Your details")
    st.caption("Used in cover letters and the recruiter-email footer (legally required).")
    ident = prefs["identity"]
    with st.form("identity_form"):
        c1, c2 = st.columns(2)
        ident["full_name"] = c1.text_input("Full name", value=ident.get("full_name", ""))
        ident["email"] = c2.text_input("Email", value=ident.get("email", ""))
        ident["phone"] = c1.text_input("Phone (optional)", value=ident.get("phone", ""))
        ident["location"] = c2.text_input("Location", value=ident.get("location", "Remote"))
        ident["linkedin"] = st.text_input("LinkedIn URL (optional)", value=ident.get("linkedin", ""))
        if st.form_submit_button("💾 Save my details", type="primary"):
            prefs["identity"] = ident
            config.save_prefs(prefs)
            st.success("Saved.")
            st.rerun()

    st.divider()

    # ---- 4. Job search preferences ------------------------------------------
    st.header("4 · What jobs do you want?")
    with st.form("prefs_form"):
        titles = st.text_input(
            "Target job titles (comma-separated)", value=_from_list(prefs.get("titles")),
            placeholder="Backend Engineer, Python Developer, Data Analyst",
        )
        keywords = st.text_input(
            "Must-have skills / keywords (comma-separated)", value=_from_list(prefs.get("keywords")),
            placeholder="python, sql, fastapi, aws",
        )
        c1, c2 = st.columns(2)
        seniority = c1.selectbox(
            "Seniority", ["", "Intern", "Junior", "Mid", "Senior", "Lead"],
            index=["", "Intern", "Junior", "Mid", "Senior", "Lead"].index(prefs.get("seniority", "") or ""),
        )
        min_salary = c2.number_input(
            "Minimum salary (0 = any)", min_value=0, step=5000, value=int(prefs.get("min_salary", 0) or 0)
        )
        exclude = st.text_input(
            "Exclude postings containing (comma-separated)", value=_from_list(prefs.get("exclude")),
            placeholder="senior, clearance, on-site",
        )
        all_sources = ["remotive", "remoteok", "arbeitnow", "himalayas", "jobicy", "adzuna"]
        sources = st.multiselect(
            "Job sources (all free APIs — no scraping)", all_sources,
            default=prefs.get("sources") or all_sources[:5],
            help="Adzuna needs a free key (set it below).",
        )
        if st.form_submit_button("💾 Save preferences", type="primary"):
            prefs.update({
                "titles": _to_list(titles),
                "keywords": _to_list(keywords),
                "seniority": seniority,
                "min_salary": int(min_salary),
                "exclude": _to_list(exclude),
                "sources": sources,
            })
            config.save_prefs(prefs)
            st.success("Saved.")
            st.rerun()

    st.divider()

    # ---- 4. Optional extras --------------------------------------------------
    with st.expander("Optional: Adzuna key (more job listings) & outreach limit"):
        with st.form("extras_form"):
            app_id, app_key = config.adzuna_creds()
            new_id = st.text_input("Adzuna App ID", value=app_id)
            new_key = st.text_input("Adzuna App Key", value=app_key, type="password")
            cap = st.number_input(
                "Max recruiter emails to draft per day", min_value=1, max_value=100,
                value=int(prefs.get("outreach_daily_cap", 15)),
                help="A safety limit so outreach stays targeted, not spammy.",
            )
            chrome_dir = st.text_input(
                "Local Chrome/Edge User Data Directory (Bypass Login Gates)",
                value=prefs.get("chrome_user_data_dir", ""),
                help=r"e.g. C:\Users\YourName\AppData\Local\Google\Chrome\User Data. If provided, the app will use your active session to bypass logins on LinkedIn/Glassdoor.",
            )
            if st.form_submit_button("💾 Save extras"):
                config.set_secrets({"adzuna_app_id": new_id, "adzuna_app_key": new_key})
                prefs["outreach_daily_cap"] = int(cap)
                prefs["chrome_user_data_dir"] = chrome_dir
                config.save_prefs(prefs)
                st.success("Saved.")
                st.rerun()

    with st.expander("Optional: Enable daily background auto-fetch (Windows)"):
        st.write(
            "You can run the job copilot automatically every morning to fetch, score, and rank jobs "
            "so that fresh matches are ready in your tracker when you start your day."
        )
        st.markdown(
            "To enable this, double-click **`schedule_task.bat`** in your project folder. "
            "It will register a background Windows Task Scheduler task that runs daily at 9:00 AM."
        )
        
        # Check if the scheduler log file exists, and display the last few lines
        log_file = config.DATA_DIR / "scheduler_log.txt"
        if log_file.exists():
            st.markdown("**Scheduler log history:**")
            try:
                log_lines = log_file.read_text(encoding="utf-8").strip().split("\n")
                st.code("\n".join(log_lines[-8:]))
            except Exception:
                pass



def _resume_section(prefs: dict) -> None:
    st.header("2 · Your resume")
    st.caption("The AI reads this once to build your profile. It never invents anything.")

    profile = config.load_profile()
    if profile:
        st.success(
            f"Loaded: **{profile.get('name') or 'your resume'}** — "
            f"{len(profile.get('skills') or [])} skills, "
            f"{len(profile.get('experience') or [])} roles."
        )
        with st.expander("View parsed profile"):
            if profile.get("headline"):
                st.write(f"**Headline:** {profile['headline']}")
            if profile.get("summary"):
                st.write(f"**Summary:** {profile['summary']}")
            if profile.get("skills"):
                st.write("**Skills:** " + ", ".join(map(str, profile["skills"])))
            if profile.get("target_titles"):
                st.caption("Suggested titles: " + ", ".join(profile["target_titles"]))

        with st.expander("✏️ Edit parsed profile"):
            with st.form("edit_profile_form"):
                # Basic info
                c1, c2 = st.columns(2)
                p_name = c1.text_input("Name", value=profile.get("name", ""))
                p_email = c2.text_input("Email", value=profile.get("email", ""))
                p_phone = c1.text_input("Phone", value=profile.get("phone", ""))
                p_loc = c2.text_input("Location", value=profile.get("location", ""))
                p_head = st.text_input("Headline", value=profile.get("headline", ""))
                p_sum = st.text_area("Summary", value=profile.get("summary", ""), height=100)

                # Skills, Target Titles, Certifications (comma separated)
                p_skills = st.text_area("Skills (comma-separated)", value=_from_list(profile.get("skills", [])))
                p_titles = st.text_input("Suggested target titles (comma-separated)", value=_from_list(profile.get("target_titles", [])))
                p_certs = st.text_input("Certifications (comma-separated)", value=_from_list(profile.get("certifications", [])))

                # Links
                st.markdown("**Links**")
                links = profile.get("links", {}) or {}
                link_linkedin = st.text_input("LinkedIn URL", value=links.get("linkedin", ""))
                link_github = st.text_input("GitHub URL", value=links.get("github", ""))
                link_portfolio = st.text_input("Portfolio/Website URL", value=links.get("portfolio", ""))

                # Nested list editor
                st.markdown("**Nested Lists (Experience, Education, Projects)**")
                st.caption("Edit the JSON structure directly to update these lists.")

                exp_json = st.text_area(
                    "Work Experience (JSON format)",
                    value=json.dumps(profile.get("experience", []), indent=2),
                    height=250
                )
                edu_json = st.text_area(
                    "Education (JSON format)",
                    value=json.dumps(profile.get("education", []), indent=2),
                    height=150
                )
                proj_json = st.text_area(
                    "Projects (JSON format)",
                    value=json.dumps(profile.get("projects", []), indent=2),
                    height=150
                )

                if st.form_submit_button("💾 Save Profile Edits"):
                    try:
                        new_exp = json.loads(exp_json)
                        new_edu = json.loads(edu_json)
                        new_proj = json.loads(proj_json)

                        profile.update({
                            "name": p_name,
                            "email": p_email,
                            "phone": p_phone,
                            "location": p_loc,
                            "headline": p_head,
                            "summary": p_sum,
                            "skills": _to_list(p_skills),
                            "target_titles": _to_list(p_titles),
                            "certifications": _to_list(p_certs),
                            "links": {
                                "linkedin": link_linkedin,
                                "github": link_github,
                                "portfolio": link_portfolio,
                            },
                            "experience": new_exp,
                            "education": new_edu,
                            "projects": new_proj,
                        })
                        config.save_profile(profile)
                        st.success("Profile updated successfully!")
                        st.rerun()
                    except json.JSONDecodeError as je:
                        st.error(f"Failed to save: Invalid JSON structure in experience, education, or projects: {je}")
                    except Exception as ex:
                        st.error(f"Failed to save: {ex}")

    uploaded = st.file_uploader("Upload your resume (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"])
    if uploaded is not None and st.button("📄 Read & parse resume", type="primary"):
        if not config.provider_ready():
            st.error("Connect the AI first (section 1 above).")
            return
        try:
            data = uploaded.read()
            ext = Path(uploaded.name).suffix.lower()
            (config.DATA_DIR / f"resume_source{ext}").write_bytes(data)
            with st.spinner("Reading your resume with AI…"):
                text = profile_parser.extract_text(data, uploaded.name)
                parsed = profile_parser.parse_resume(text)
            config.save_profile(parsed)

            # Helpfully pre-fill identity + target titles if still empty.
            ident = prefs["identity"]
            changed = False
            for src_key, id_key in (("name", "full_name"), ("email", "email"),
                                    ("phone", "phone"), ("location", "location")):
                if parsed.get(src_key) and not ident.get(id_key):
                    ident[id_key] = parsed[src_key]
                    changed = True
            if not prefs.get("titles") and parsed.get("target_titles"):
                prefs["titles"] = parsed["target_titles"]
                changed = True
            if changed:
                prefs["identity"] = ident
                config.save_prefs(prefs)

            st.success("Resume parsed and saved!")
            st.rerun()
        except Exception as e:
            st.error(f"Couldn't parse that file: {e}")
