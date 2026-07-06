"""Spawn the review-first browser process and build a copy-paste answer sheet.

This module is imported by the Streamlit page. It does NOT import Playwright (that lives
in the separate ``autofill_runner`` process) so the UI stays light and thread-safe.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

from . import config

# Sites where automated filling/submission risks YOUR account — open only, never fill.
GATED_DOMAINS = ("linkedin.com", "indeed.com", "glassdoor.com", "ziprecruiter.com")


def is_gated(url: str) -> bool:
    return any(d in (url or "").lower() for d in GATED_DOMAINS)


def _split_name(full: str) -> tuple[str, str]:
    parts = (full or "").split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def answer_sheet(profile: dict, prefs: dict, cover_letter: str = "") -> dict[str, str]:
    """The values you'll commonly need, ready to copy if auto-fill misses a field."""
    ident = prefs.get("identity", {}) or {}
    links = (profile or {}).get("links", {}) or {}
    full = ident.get("full_name") or (profile or {}).get("name", "")
    first, last = _split_name(full)
    sheet = {
        "Full name": full,
        "First name": first,
        "Last name": last,
        "Email": ident.get("email") or (profile or {}).get("email", ""),
        "Phone": ident.get("phone") or (profile or {}).get("phone", ""),
        "Location": ident.get("location") or (profile or {}).get("location", "Remote"),
        "LinkedIn": ident.get("linkedin") or links.get("linkedin", ""),
        "GitHub": links.get("github", ""),
    }
    if cover_letter:
        sheet["Cover letter"] = cover_letter
    return {k: v for k, v in sheet.items() if v}


def launch_assisted_apply(job: dict, resume_path: str, cover_letter: str,
                          profile: dict, prefs: dict) -> str:
    """Open the apply page in a visible browser, pre-filled. Returns a status note."""
    ident = prefs.get("identity", {}) or {}
    links = (profile or {}).get("links", {}) or {}
    full = ident.get("full_name") or (profile or {}).get("name", "")
    first, last = _split_name(full)

    apply_url = job.get("apply_url") or job.get("url") or ""
    state_dir = config.DATA_DIR / "browser_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    custom_chrome_dir = prefs.get("chrome_user_data_dir", "").strip()
    browser_user_data_dir = custom_chrome_dir if custom_chrome_dir else str(state_dir)

    cfg = {
        "apply_url": apply_url,
        "gated": is_gated(apply_url),
        "user_data_dir": browser_user_data_dir,
        "resume_path": resume_path or "",
        "full_name": full,
        "first_name": first,
        "last_name": last,
        "email": ident.get("email") or (profile or {}).get("email", ""),
        "phone": ident.get("phone") or (profile or {}).get("phone", ""),
        "location": ident.get("location") or (profile or {}).get("location", ""),
        "linkedin": ident.get("linkedin") or links.get("linkedin", ""),
        "github": links.get("github", ""),
        "website": links.get("portfolio", ""),
        "cover_letter": cover_letter or "",
        # LLM Context for custom autofilling (model names only — NOT keys)
        "provider": config.provider(),
        "writing_model": prefs.get("writing_model", "claude-sonnet-4-6"),
        "gemini_model": prefs.get("gemini_model", "gemini-2.0-flash"),
        "job_title": job.get("title", ""),
        "job_company": job.get("company", ""),
        "job_description": job.get("description", ""),
        "profile": profile,
    }

    # Pass API keys via environment variables (inherited by subprocess) —
    # never via stdin where they'd sit in the JSON config payload.
    child_env = os.environ.copy()
    if config.anthropic_key():
        child_env["ANTHROPIC_API_KEY"] = config.anthropic_key()
    if config.gemini_key():
        child_env["GEMINI_API_KEY"] = config.gemini_key()

    # Use the same interpreter that's running Streamlit (the venv python).
    process = subprocess.Popen(
        [sys.executable, "-m", "src.autofill_runner"],
        stdin=subprocess.PIPE,
        cwd=str(config.ROOT),
        env=child_env,
    )
    if process.stdin:
        process.stdin.write(json.dumps(cfg).encode("utf-8"))
        process.stdin.close()

    if cfg["gated"]:
        return "Opening the page in your browser (login-gated site — not auto-filled)."
    return "Opening a browser and pre-filling the form. Review every field, then submit yourself."
