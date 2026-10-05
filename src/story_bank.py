"""Persistent STAR+R Behavioral Story Bank & Interview Intelligence Suite.

Implements:
1. Story Bank: Manages 5-10 master candidate STAR stories with Reflection lessons.
2. Reverse-Interview Generator: Generates sharp questions to ask the interviewer to expose red flags.
3. Post-Interview Debrief Assistant: Captures interview questions, responses, and key learnings.
"""
from __future__ import annotations

import json
from typing import Any
from . import config, llm
from .profile_parser import profile_context
from .anti_slop import audit_and_sanitize

STORY_BANK_FILE = config.DATA_DIR / "story_bank.json"


def load_story_bank() -> list[dict[str, Any]]:
    """Load persistent STAR+R story bank from disk."""
    if STORY_BANK_FILE.exists():
        try:
            return json.loads(STORY_BANK_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_story_bank(stories: list[dict[str, Any]]) -> None:
    """Persist STAR+R stories to disk."""
    STORY_BANK_FILE.parent.mkdir(parents=True, exist_ok=True)
    STORY_BANK_FILE.write_text(json.dumps(stories, indent=2, ensure_ascii=False), encoding="utf-8")


def auto_extract_stories_from_profile(profile: dict[str, Any], prefs: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate initial 5-8 master STAR+R stories based on candidate's real experience."""
    existing = load_story_bank()
    if existing:
        return existing

    prompt = (
        "You are an Elite Behavioral Interview Coach specializing in the Amazon/Google STAR+R framework.\n"
        "Analyze the candidate's resume and extract 5 to 7 high-impact master behavioral stories.\n"
        "Each story MUST follow:\n"
        "- Competency: (e.g. Technical Leadership, Ambiguity & Crisis, Conflict Resolution, Scaling & Performance, Customer Obsession)\n"
        "- Situation: (Context, company, and stakes)\n"
        "- Task: (Exact technical responsibility)\n"
        "- Action: (Specific steps taken and technologies architected)\n"
        "- Result: (Quantified metric, production outcome, or business impact)\n"
        "- Reflection: (The engineering lesson learned and what they would do differently today)\n\n"
        "CRITICAL ANTI-AI-SLOP RULES:\n"
        "- Never use em-dashes (—) or double hyphens (--).\n"
        "- Never use cliché buzzwords like delve/tapestry/spearheaded/fostered/robust/testament/journey.\n"
        "- Write with concrete engineering verbs and numbers only.\n\n"
        "ZERO-FABRICATION RULE: Ground every story strictly in the candidate's real profile.\n"
        "Return a JSON array of story objects with keys: id (int), competency (str), title (str), situation (str), task (str), action (str), result (str), reflection (str)."
    )

    data = []
    if llm.provider_ready():
        try:
            data = llm.generate_json(
                prompt,
                system=(
                    "You are an expert tech interview architect. "
                    "Never use em-dashes (—) or cliché AI buzzwords (delve, tapestry, spearheaded, fostered). "
                    "Return strictly valid JSON array."
                ),
                cached_context=profile_context(profile),
                model=prefs.get("writing_model"),
                max_tokens=2200
            )
        except Exception:
            data = []

    if not isinstance(data, list) or not data:
        data = [
            {
                "id": 1,
                "competency": "Technical Architecture & Scaling",
                "title": "Optimizing Core Service Throughput",
                "situation": "High query volume causing latency degradation on production endpoints.",
                "task": "Identify root causes and refactor database query execution paths.",
                "action": "Implemented indexing, cached expensive queries in Redis, and decoupled write queues.",
                "result": "Reduced p99 latency by 45% and eliminated timeouts during peak hours.",
                "reflection": "Always benchmark under realistic concurrency before shipping schema changes."
            }
        ]

    clean_stories = []
    for s in data:
        if isinstance(s, dict):
            clean_s = {
                "id": s.get("id", len(clean_stories) + 1),
                "competency": audit_and_sanitize(str(s.get("competency", ""))).cleaned_text,
                "title": audit_and_sanitize(str(s.get("title", ""))).cleaned_text,
                "situation": audit_and_sanitize(str(s.get("situation", ""))).cleaned_text,
                "task": audit_and_sanitize(str(s.get("task", ""))).cleaned_text,
                "action": audit_and_sanitize(str(s.get("action", ""))).cleaned_text,
                "result": audit_and_sanitize(str(s.get("result", ""))).cleaned_text,
                "reflection": audit_and_sanitize(str(s.get("reflection", ""))).cleaned_text,
            }
            clean_stories.append(clean_s)

    save_story_bank(clean_stories)
    return clean_stories


def generate_reverse_interview_questions(job: dict[str, Any], prefs: dict[str, Any]) -> list[dict[str, str]]:
    """Generate probing questions for the candidate to ask to detect red flags and culture issues."""
    prompt = (
        f"You are a Senior Principal Engineer advising a candidate interviewing for {job.get('title','')} at {job.get('company','')}.\n"
        f"Job Description snippet:\n{(job.get('description') or '')[:2500]}\n\n"
        "Generate 4 sharp, respectful, highly revealing reverse-interview questions the candidate should ask the team.\n"
        "Target:\n"
        "1. Real on-call load & technical debt burden\n"
        "2. How technical disagreements and roadmap priorities are resolved\n"
        "3. Engineering autonomy vs micromanagement\n"
        "4. Success metrics for this exact role in the first 90 days\n\n"
        "CRITICAL ANTI-AI-SLOP RULES:\n"
        "- Never use em-dashes (—) or double hyphens (--).\n"
        "- Never use cliché buzzwords like delve/tapestry/spearheaded/fostered/robust.\n"
        "- Write with crisp, authentic developer terminology.\n\n"
        "Return a JSON array of objects: [{\"category\": \"...\", \"question\": \"...\", \"what_to_listen_for\": \"...\"}]"
    )

    data = []
    if llm.provider_ready():
        try:
            data = llm.generate_json(
                prompt,
                system=(
                    "You are an expert engineering leader. "
                    "Never use em-dashes (—) or cliché AI buzzwords. Return valid JSON array."
                ),
                model=prefs.get("writing_model"),
                max_tokens=800
            )
        except Exception:
            data = []

    if not isinstance(data, list) or not data:
        data = [
            {
                "category": "Tech Debt & On-Call",
                "question": "What percentage of an average sprint is dedicated to addressing tech debt and operational health versus shipping new product features?",
                "what_to_listen_for": "If under 15% or dismissed, expect heavy unaddressed production fire-fighting."
            },
            {
                "category": "Decision Making",
                "question": "Can you share an example of a recent technical architectural disagreement on the team and how the final decision was reached?",
                "what_to_listen_for": "Look for consensus, data-driven decisions, and psychological safety rather than top-down executive mandates."
            }
        ]

    for q in data:
        if isinstance(q, dict):
            for k in ("category", "question", "what_to_listen_for"):
                if k in q and q[k]:
                    q[k] = audit_and_sanitize(str(q[k])).cleaned_text

    return data


def record_interview_debrief(
    job_id: int,
    round_name: str,
    questions_asked: list[str],
    candidate_notes: str,
    prefs: dict[str, Any]
) -> dict[str, Any]:
    """Analyze post-interview debrief notes and suggest actionable takeaways."""
    prompt = (
        f"Analyze this post-interview debrief for Round: '{round_name}'.\n"
        f"Questions asked by interviewer:\n{json.dumps(questions_asked, indent=2)}\n\n"
        f"Candidate Notes & Self-Assessment:\n{candidate_notes}\n\n"
        "Provide a structured critique with:\n"
        "1. Strong points demonstrated\n"
        "2. Vulnerabilities or weak answers detected\n"
        "3. Recommended follow-up thank you email talking point to reinforce fit\n\n"
        "CRITICAL ANTI-AI-SLOP RULES:\n"
        "- Never use em-dashes (—) or double hyphens (--).\n"
        "- Never use cliché buzzwords like delve/tapestry/spearheaded/fostered/robust.\n\n"
        "Return JSON: {\"strong_points\": [\"...\"], \"areas_to_improve\": [\"...\"], \"thank_you_talking_point\": \"...\"}"
    )

    data = {}
    if llm.provider_ready():
        try:
            data = llm.generate_json(
                prompt,
                system="You are an expert executive interview coach. Never use em-dashes (—) or AI clichés.",
                model=prefs.get("writing_model"),
                max_tokens=600
            )
        except Exception:
            data = {}

    critique_data = data or {
        "strong_points": ["Clear technical communication"],
        "areas_to_improve": ["Quantify architectural tradeoffs more explicitly"],
        "thank_you_talking_point": "Reiterate enthusiasm for scaling challenges discussed."
    }

    clean_critique = {
        "strong_points": [audit_and_sanitize(str(p)).cleaned_text for p in critique_data.get("strong_points", []) if p],
        "areas_to_improve": [audit_and_sanitize(str(p)).cleaned_text for p in critique_data.get("areas_to_improve", []) if p],
        "thank_you_talking_point": audit_and_sanitize(str(critique_data.get("thank_you_talking_point", ""))).cleaned_text
    }

    return {
        "job_id": job_id,
        "round_name": round_name,
        "critique": clean_critique
    }
