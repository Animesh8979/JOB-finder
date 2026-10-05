"""
skills_catalog.py
High-performance catalog and search for Antigravity skills in D:\skills-library.
Provides memory-cached indexing, auto-categorization, and markdown reader.
"""

import os
import re
import time
from typing import Dict, List, Optional, Any

SKILLS_DIR = r"D:\skills-library"
_CACHE: Optional[List[Dict[str, Any]]] = None
_CACHE_TIMESTAMP: float = 0.0
CACHE_TTL = 300.0  # 5 minutes


def _categorize(name: str, desc: str) -> str:
    text = f"{name} {desc}".lower()
    if any(k in text for k in ["resume", "job", "interview", "career", "recruiter", "hire", "hiring", "ats"]):
        return "Career & Resume"
    if any(k in text for k in ["scrape", "crawl", "browser", "playwright", "spider", "fetch", "extract", "stealth"]):
        return "Scraping & Automation"
    if any(k in text for k in ["test", "tdd", "review", "audit", "quality", "lint", "refactor", "verify", "verification"]):
        return "Code Quality & Testing"
    if any(k in text for k in ["security", "vulnerability", "penetration", "semgrep", "exploit", "owasp", "secret"]):
        return "Security & Audit"
    if any(k in text for k in ["video", "audio", "image", "tts", "animation", "remotion", "media", "draw", "speech"]):
        return "Media & Creative"
    if any(k in text for k in ["think", "reason", "swarm", "brain", "logic", "critic", "agent", "decision", "first_principle"]):
        return "AI & Reasoning"
    if any(k in text for k in ["docker", "k8s", "cloud", "aws", "azure", "git", "deploy", "terraform", "infra"]):
        return "Cloud & DevOps"
    return "Core Engineering"


def build_catalog(force: bool = False) -> List[Dict[str, Any]]:
    global _CACHE, _CACHE_TIMESTAMP
    now = time.time()
    if not force and _CACHE is not None and (now - _CACHE_TIMESTAMP) < CACHE_TTL:
        return _CACHE

    if not os.path.exists(SKILLS_DIR):
        return []

    skills = []
    try:
        entries = sorted(os.scandir(SKILLS_DIR), key=lambda e: e.name.lower())
    except Exception:
        return []

    for entry in entries:
        if not entry.is_dir() or entry.name.startswith("_") or entry.name.startswith("."):
            continue
        skill_md = os.path.join(entry.path, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue

        name = entry.name
        desc = ""
        lines_count = 0
        try:
            with open(skill_md, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(2048)
                lines_count = content.count("\n")

            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    fm = parts[1]
                    m_name = re.search(r"name:\s*(.+)", fm)
                    if m_name:
                        name = m_name.group(1).strip().strip("'\"")
                    m_desc = re.search(r"description:\s*([>|-]?\s*[\s\S]+?)(?=\n\w+:|$)", fm)
                    if m_desc:
                        desc = m_desc.group(1).strip().replace("\n", " ")
                        if desc.startswith(">"):
                            desc = desc[1:].strip()
            if not desc:
                # Grab first non-header line
                for line in content.split("\n"):
                    clean = line.strip().lstrip("#").strip()
                    if clean and not clean.startswith("---"):
                        desc = clean
                        break
        except Exception:
            pass

        cat = _categorize(name, desc)
        skills.append({
            "id": entry.name,
            "name": name,
            "description": desc[:280] if desc else "Custom Antigravity Agent Skill.",
            "category": cat,
            "path": skill_md,
            "has_scripts": os.path.isdir(os.path.join(entry.path, "scripts")),
            "has_references": os.path.isdir(os.path.join(entry.path, "references")),
        })

    _CACHE = skills
    _CACHE_TIMESTAMP = now
    return skills


def get_skills(search: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
    all_skills = build_catalog()
    filtered = all_skills

    if category and category != "All":
        filtered = [s for s in filtered if s["category"].lower() == category.lower()]

    if search and search.strip():
        q = search.strip().lower()
        filtered = [
            s for s in filtered
            if q in s["name"].lower() or q in s["id"].lower() or q in s["description"].lower()
        ]

    # Compute category distributions
    cat_counts: Dict[str, int] = {}
    for s in all_skills:
        c = s["category"]
        cat_counts[c] = cat_counts.get(c, 0) + 1

    return {
        "skills": filtered,
        "total": len(all_skills),
        "filtered_count": len(filtered),
        "categories": cat_counts,
    }


def get_skill_detail(skill_id: str) -> Optional[Dict[str, Any]]:
    # Prevent directory traversal
    safe_id = os.path.basename(skill_id)
    skill_md = os.path.join(SKILLS_DIR, safe_id, "SKILL.md")
    if not os.path.isfile(skill_md):
        return None

    try:
        with open(skill_md, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        name = safe_id
        desc = ""
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm = parts[1]
                m_name = re.search(r"name:\s*(.+)", fm)
                if m_name:
                    name = m_name.group(1).strip().strip("'\"")
                m_desc = re.search(r"description:\s*([>|-]?\s*[\s\S]+?)(?=\n\w+:|$)", fm)
                if m_desc:
                    desc = m_desc.group(1).strip().replace("\n", " ")
                    if desc.startswith(">"):
                        desc = desc[1:].strip()

        return {
            "id": safe_id,
            "name": name,
            "description": desc,
            "category": _categorize(name, desc),
            "content": content,
            "path": skill_md,
        }
    except Exception as e:
        return {"id": safe_id, "error": str(e)}
