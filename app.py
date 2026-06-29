"""Remote Job Application Copilot — local dashboard.

Run it with:  run.bat   (or:  streamlit run app.py)
Everything happens locally on your machine. Nothing is submitted or emailed without
your explicit click.
"""
from __future__ import annotations

import streamlit as st

from pathlib import Path

from src import config, db
from src.ui import apply as apply_page
from src.ui import find, outreach, setup, tailor, tracker

st.set_page_config(page_title="Job Application Copilot", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

# Load custom CSS
css_path = Path(__file__).parent / "src" / "ui" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# Create the local database on first run
db.init_db()

def _check_setup_status():
    r = config.readiness()
    if not all(r.values()):
        with st.sidebar.expander("⚠️ Setup Required", expanded=True):
            st.write(("✅" if r["ai_key"] else "❌") + " AI key connected")
            st.write(("✅" if r["resume"] else "❌") + " Resume added")
            st.write(("✅" if r["identity"] else "❌") + " Your details filled in")
            st.info("Finish these on the **Setup** page.")

def main() -> None:
    st.sidebar.title("🚀 Job Copilot")
    st.sidebar.caption("Your premium career operations center")
    
    _check_setup_status()
    
    st.sidebar.divider()
    st.sidebar.caption(
        "🔒 **Review-first**: Nothing is submitted or emailed without your click."
    )

    pages = {
        "Configuration": [
            st.Page(setup.render, title="Home & Setup", icon="🏠", url_path="setup")
        ],
        "Job Hunt": [
            st.Page(find.render, title="Find jobs", icon="🔎", url_path="find"),
            st.Page(tailor.render, title="Tailor resume & cover", icon="✍️", url_path="tailor"),
            st.Page(apply_page.render, title="Apply (review-first)", icon="📤", url_path="apply")
        ],
        "Tracking & Outreach": [
            st.Page(tracker.render, title="Tracker Dashboard", icon="📊", url_path="tracker"),
            st.Page(outreach.render, title="Recruiter outreach", icon="✉️", url_path="outreach")
        ]
    }

    pg = st.navigation(pages)
    pg.run()

if __name__ == "__main__":
    main()
