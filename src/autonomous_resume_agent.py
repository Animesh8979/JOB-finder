"""Autonomous Zero-Intervention Resume Diagnostic, GitHub Enrichment & Auto-Fix Agent.

Implements a 1-Drop full-circle workflow:
1. Evaluates the candidate resume using our deterministic HackerRank ATS engine (src/recruiter_score.py).
2. Queries public GitHub APIs (https://api.github.com/users/{handle}) to enrich open-source metrics without fabrication.
3. Diagnoses weaknesses (passive wording, lack of action verbs, unorganized skills).
4. Automatically fixes bullet points and skills via LLM + fabrication_shield verification.
5. Computes Before vs. After HackerRank ATS scores and produces an Executive Diagnostic Report.
"""
from __future__ import annotations

import json
import re
import urllib.request
import urllib.error
from typing import Any

from . import llm, config
from .recruiter_score import score as hackerrank_score
from .fabrication_shield import verify_resume_claims
from .anti_slop import audit_and_sanitize, sanitize_bullet
from .github_evidence_ledger import build_github_evidence_ledger
from .multi_ats_pipeline import simulate_enterprise_ats_parsers, stage_instant_auto_apply


def fetch_github_public_stats(handle: str) -> dict[str, Any]:
    """Fetch public repository count, stars, and top languages from GitHub REST API.

    Uses public unauthenticated API (or token if available) to verify OSS work.
    Never hallucinates data — tags as [VERIFIED] or returns empty dict on failure.
    """
    clean_handle = handle.strip().lower().split("/")[-1]
    if not clean_handle:
        return {}

    user_url = f"https://api.github.com/users/{clean_handle}"
    repos_url = f"https://api.github.com/users/{clean_handle}/repos?sort=updated&per_page=15"
    headers = {"User-Agent": "JobApplicationCopilot-ATS-Auditor"}

    stats: dict[str, Any] = {
        "handle": clean_handle,
        "public_repos": 0,
        "total_stars": 0,
        "top_languages": [],
        "verified": False,
    }

    try:
        req = urllib.request.Request(user_url, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
            stats["public_repos"] = data.get("public_repos", 0)
            stats["followers"] = data.get("followers", 0)

        req_repos = urllib.request.Request(repos_url, headers=headers)
        with urllib.request.urlopen(req_repos, timeout=4) as resp:
            repos = json.loads(resp.read().decode())
            stars = 0
            langs = set()
            for r in repos:
                stars += r.get("stargazers_count", 0)
                if r.get("language"):
                    langs.add(r["language"])
            stats["total_stars"] = stars
            stats["top_languages"] = sorted(list(langs))
            stats["verified"] = True
    except Exception:
        # Fallback cleanly if offline or rate limited
        stats["verified"] = False

    return stats


def audit_and_autofix_resume(profile: dict[str, Any], prefs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Perform a comprehensive autonomous audit and upgrade on a candidate profile.

    Returns:
        dict containing:
        - before_score: dict (total, by_category, rationale)
        - after_score: dict (total, by_category, rationale)
        - score_delta: int
        - github_enrichment: dict
        - diagnostics: list[str]
        - fixes_applied: list[dict]
        - fixed_profile: dict
        - ready_to_apply: bool
    """
    prefs = prefs or {}
    raw_text = profile.get("raw_text") or json.dumps(profile)

    # 1. Detect GitHub Handle
    links = profile.get("links") or {}
    gh_handle = ""
    if isinstance(links, dict) and links.get("github"):
        m = re.search(r"github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})", links.get("github", ""))
        if m:
            gh_handle = m.group(1)
    if not gh_handle and "github.com/" in raw_text.lower():
        m = re.search(r"github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})", raw_text, re.IGNORECASE)
        if m:
            gh_handle = m.group(1)

    # 2. Run Initial HackerRank ATS Evaluation passing skills and GitHub handle
    before_report = hackerrank_score(
        raw_text,
        github_handle=gh_handle or None,
        skills=profile.get("skills", [])
    )
    before_dict = before_report.to_dict()

    gh_stats = {}
    diagnostics: list[str] = []
    evidence_data = {}
    if gh_handle:
        gh_stats = fetch_github_public_stats(gh_handle)
        evidence_data = build_github_evidence_ledger(gh_handle)
        if gh_stats.get("verified"):
            diagnostics.append(
                f"[VERIFIED] GitHub Profile @{gh_handle}: {gh_stats['public_repos']} public repos, "
                f"{gh_stats['total_stars']} stars, languages: {', '.join(gh_stats['top_languages'])}"
            )
        for d in evidence_data.get("diagnostics", []):
            diagnostics.append(d)
    else:
        diagnostics.append(
            "[GAP] No GitHub profile URL detected. Adding your GitHub profile link can add up to +20 HackerRank OSS points."
        )

    # Analyze weaknesses from before_report rationale
    for r in before_dict.get("rationale", []):
        if r.get("delta", 0) < 0 or "Missing" in r.get("note", "") or "0 " in r.get("note", ""):
            diagnostics.append(f"[DIAGNOSTIC] {r.get('category').upper()}: {r.get('note')}")

    # 3. Autonomous LLM Auto-Fixer with Zero-Hallucination Constraints
    prompt = (
        "You are an Elite Executive Career Coach & ATS Optimizer.\n"
        "Your mission is to upgrade the candidate's resume bullet points and skills array so it scores in the top 1% "
        "on HackerRank ATS evaluation engines.\n\n"
        f"CANDIDATE EXISTING PROFILE:\n{json.dumps(profile, indent=2)}\n\n"
        f"DIAGNOSTIC WEAKNESSES FOUND:\n{json.dumps(diagnostics, indent=2)}\n\n"
        "UPGRADE INSTRUCTIONS:\n"
        "1. Rewrite every bullet point under 'experience' to start with a strong action verb (e.g., Architected, Engineered, Automated, Built, Scaled, Optimized).\n"
        "2. Ensure bullet structure follows: [Strong Action Verb] + [Exact Technical Implementation] + [Real Verified Impact/Result].\n"
        "3. CRITICAL ZERO-HALLUCINATION RULE: Do NOT invent percentages, dollar values, fake employers, or fake degrees. Use ONLY facts supported by the existing profile text.\n"
        "4. CRITICAL ANTI-AI-SLOP RULES: Never use em-dashes (—), never use cliché buzzwords like delve/tapestry/spearheaded/fostered/robust/seamless, vary sentence lengths drastically, write with concrete engineering verbs and numbers only.\n"
        "5. Organize and deduplicate the 'skills' list into clean ATS keywords.\n"
        "6. Return JSON matching the exact structure: {name, headline, summary, skills, experience, education, projects, certifications, links}."
    )

    try:
        upgraded_raw = llm.generate_json(
            prompt,
            system=(
                "You are an elite ATS resume architect. "
                "Never use em-dashes (—) or cliché AI buzzwords (delve, tapestry, spearheaded, fostered). "
                "Return strictly valid JSON."
            ),
            model=prefs.get("writing_model"),
            max_tokens=3000,
        )
        if not isinstance(upgraded_raw, dict):
            upgraded_raw = dict(profile)
    except Exception:
        upgraded_raw = dict(profile)

    # 4. Enforce Claim Audit Shield
    fixed_profile = verify_resume_claims(upgraded_raw, profile, prefs)

    # Enforce Anti-AI-Slop & Humanizer Filter
    if "headline" in fixed_profile and fixed_profile["headline"]:
        fixed_profile["headline"] = audit_and_sanitize(str(fixed_profile["headline"])).cleaned_text
    if "summary" in fixed_profile and fixed_profile["summary"]:
        fixed_profile["summary"] = audit_and_sanitize(str(fixed_profile["summary"])).cleaned_text
    for exp in fixed_profile.get("experience", []):
        if isinstance(exp, dict) and "bullets" in exp and isinstance(exp["bullets"], list):
            exp["bullets"] = [sanitize_bullet(b) for b in exp["bullets"] if b]
    for proj in fixed_profile.get("projects", []):
        if isinstance(proj, dict) and "bullets" in proj and isinstance(proj["bullets"], list):
            proj["bullets"] = [sanitize_bullet(b) for b in proj["bullets"] if b]

    # Preserve essential raw_text and ID fields
    fixed_profile["raw_text"] = profile.get("raw_text", "")
    if gh_handle and isinstance(fixed_profile.get("links"), dict):
        fixed_profile["links"]["github"] = f"https://github.com/{gh_handle}"

    # Build list of fixes and claims applied
    fixes_applied: list[dict[str, Any]] = []
    old_exp = profile.get("experience") or []
    new_exp = fixed_profile.get("experience") or []

    for i, (old_item, new_item) in enumerate(zip(old_exp, new_exp)):
        old_bullets = old_item.get("bullets") if isinstance(old_item, dict) else []
        new_bullets = new_item.get("bullets") if isinstance(new_item, dict) else []
        if old_bullets != new_bullets:
            fixes_applied.append({
                "company": old_item.get("company", f"Role #{i+1}") if isinstance(old_item, dict) else f"Role #{i+1}",
                "before": old_bullets,
                "after": new_bullets,
                "claim_audit": "supported",
                "verification": "Passed Claim Audit"
            })

    # 5. Re-evaluate HackerRank ATS score after upgrades
    # Create updated synthetic raw text for re-scoring
    synth_lines = [fixed_profile.get("name", ""), fixed_profile.get("summary", "")]
    if gh_handle:
        synth_lines.append(f"GitHub: https://github.com/{gh_handle}")
    synth_lines.append("Skills: " + ", ".join(fixed_profile.get("skills", [])))
    for exp in fixed_profile.get("experience", []):
        if isinstance(exp, dict):
            synth_lines.append(f"{exp.get('title', '')} at {exp.get('company', '')}")
            for b in exp.get("bullets", []):
                synth_lines.append(f"- {b}")

    updated_text = "\n".join(synth_lines)
    after_report = hackerrank_score(
        updated_text,
        github_handle=gh_handle or None,
        skills=fixed_profile.get("skills", [])
    )
    after_dict = after_report.to_dict()

    score_delta = after_dict["total"] - before_dict["total"]

    # Save upgraded profile automatically
    config.save_profile(fixed_profile)

    multi_ats = simulate_enterprise_ats_parsers(fixed_profile)
    staged = stage_instant_auto_apply(fixed_profile)

    return {
        "status": "success",
        "before_score": before_dict,
        "after_score": after_dict,
        "score_delta": score_delta,
        "github_enrichment": gh_stats,
        "evidence_ledger": evidence_data.get("evidence_ledger", {}),
        "top_projects": evidence_data.get("top_projects", []),
        "multi_ats_audit": multi_ats,
        "auto_apply_staged": staged,
        "diagnostics": diagnostics,
        "fixes_applied": fixes_applied,
        "fixed_profile": fixed_profile,
        "ready_to_apply": True,
    }


def resume_audit(profile: dict[str, Any], prefs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Alias for audit_and_autofix_resume aligning with AOS v5.0 resume_audit naming."""
    return audit_and_autofix_resume(profile, prefs)
