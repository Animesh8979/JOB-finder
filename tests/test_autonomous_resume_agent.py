"""Tests for Autonomous Resume Agent (HackerRank ATS + GitHub API enrichment + Auto-fix)."""
import pytest
from src import autonomous_resume_agent


def test_autonomous_resume_agent_basic():
    profile = {
        "name": "Animesh Shukla",
        "headline": "Full-Stack AI Engineer",
        "summary": "Experienced engineer building AI pipelines.",
        "skills": ["Python", "FastAPI", "React", "Docker"],
        "links": {"github": "https://github.com/torvalds"},
        "experience": [
            {
                "title": "Software Engineer",
                "company": "Tech Corp",
                "bullets": [
                    "worked on API server for customers",
                    "made dashboard faster by 40%"
                ]
            }
        ],
        "raw_text": "Animesh Shukla\nFull-Stack AI Engineer\nSkills: Python, FastAPI, React, Docker\nWorked on API server for customers.\nMade dashboard faster by 40%."
    }
    prefs = {"writing_model": "test-model"}

    res = autonomous_resume_agent.audit_and_autofix_resume(profile, prefs)
    assert res["status"] == "success"
    assert "before_score" in res
    assert "after_score" in res
    assert res["ready_to_apply"] is True
    assert isinstance(res["diagnostics"], list)
