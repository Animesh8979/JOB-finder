"""
GitHub Evidence Ledger Engine (AOS v5.0 Aligned)
Inspired by open-source patterns from `lucidRESUME` & `Resume-github-job-analyzer`.

Extracts deep repository evidence from public GitHub REST APIs without authentication
or hallucinated metrics. Maps candidate skills directly to physical GitHub repository URLs.
"""

from __future__ import annotations
import json
import re
import urllib.request
import urllib.error
from typing import Any


def extract_github_handle(text_or_url: str) -> str:
    """Extracts a clean GitHub username from any link or text string."""
    if not text_or_url:
        return ""
    m = re.search(r"github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})", text_or_url, re.IGNORECASE)
    if m:
        return m.group(1)
    # Check if raw username passed
    if re.match(r"^[A-Za-z0-9][A-Za-z0-9-]{0,38}$", text_or_url.strip()):
        return text_or_url.strip()
    return ""


def build_github_evidence_ledger(github_handle: str, timeout: int = 4) -> dict[str, Any]:
    """
    Queries public GitHub REST endpoints to build an immutable 'Skill Ledger'
    mapping technical skills to concrete repository evidence.
    """
    handle = extract_github_handle(github_handle)
    if not handle:
        return {
            "verified": False,
            "handle": "",
            "evidence_ledger": {},
            "top_projects": [],
            "diagnostics": ["[GAP] No valid GitHub handle provided for evidence extraction."]
        }

    headers = {"User-Agent": "Antigravity-AI-Job-Finder-Evidence-Ledger/5.0"}
    repos_url = f"https://api.github.com/users/{handle}/repos?sort=updated&per_page=12"

    try:
        req = urllib.request.Request(repos_url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {
            "verified": False,
            "handle": handle,
            "evidence_ledger": {},
            "top_projects": [],
            "diagnostics": [f"[GAP] GitHub REST API query failed for @{handle}: {str(e)}"]
        }

    if not isinstance(data, list):
        return {
            "verified": False,
            "handle": handle,
            "evidence_ledger": {},
            "top_projects": [],
            "diagnostics": [f"[GAP] GitHub returned unexpected payload for @{handle}."]
        }

    evidence_ledger: dict[str, list[dict[str, str]]] = {}
    top_projects: list[dict[str, Any]] = []

    for repo in data:
        if not isinstance(repo, dict) or repo.get("fork"):
            continue

        name = repo.get("name", "")
        html_url = repo.get("html_url", "")
        desc = repo.get("description") or ""
        lang = repo.get("language") or "Unknown"
        stars = repo.get("stargazers_count", 0)
        topics = repo.get("topics", [])

        project_info = {
            "name": name,
            "url": html_url,
            "description": desc,
            "language": lang,
            "stars": stars,
            "topics": topics
        }
        top_projects.append(project_info)

        # Map primary language to ledger
        if lang and lang != "Unknown":
            evidence_ledger.setdefault(lang.lower(), []).append({
                "repo": name,
                "url": html_url,
                "stars": str(stars)
            })

        # Map topics to ledger
        for topic in topics:
            if isinstance(topic, str):
                evidence_ledger.setdefault(topic.lower(), []).append({
                    "repo": name,
                    "url": html_url,
                    "stars": str(stars)
                })

    # Sort projects by stars & recency
    top_projects.sort(key=lambda x: x["stars"], reverse=True)

    return {
        "verified": True,
        "handle": handle,
        "evidence_ledger": evidence_ledger,
        "top_projects": top_projects[:6],
        "diagnostics": [
            f"[VERIFIED] Extracted {len(top_projects)} original repositories for @{handle}.",
            f"[VERIFIED] Built evidence ledger across {len(evidence_ledger)} distinct skills/languages."
        ]
    }
