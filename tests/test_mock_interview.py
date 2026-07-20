"""Tests for offline AI Recruiter Simulation & Mock Interviewer Copilot."""
from __future__ import annotations

import pytest
from src import mock_interviewer


def test_generate_interview_questions_valid_list(monkeypatch: pytest.MonkeyPatch) -> None:
    from src import llm
    
    def fake_generate_json(*args, **kwargs):
        return [
            {"category": "Technical", "question": "How do you scale Docker?", "rationale": "JD requires scale"},
            {"category": "System Design", "question": "Design a rate limiter", "rationale": "High traffic API"}
        ]
        
    monkeypatch.setattr(llm, "generate_json", fake_generate_json)
    monkeypatch.setattr("src.config.load_prefs", lambda: {"writing_model": "test"})
    monkeypatch.setattr("src.mock_interviewer.profile_context", lambda p: "Profile info")
    
    res = mock_interviewer.generate_interview_questions({"title": "DevOps", "company": "Acme", "description": "Docker scale"}, {})
    assert len(res) == 2
    assert res[0]["question"] == "How do you scale Docker?"
    assert res[1]["category"] == "System Design"


def test_generate_interview_questions_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    from src import llm
    
    def fake_generate_json(*args, **kwargs):
        return "not a json list or dict"
        
    monkeypatch.setattr(llm, "generate_json", fake_generate_json)
    monkeypatch.setattr("src.config.load_prefs", lambda: {"writing_model": "test"})
    monkeypatch.setattr("src.mock_interviewer.profile_context", lambda p: "Profile info")
    
    res = mock_interviewer.generate_interview_questions({"title": "Backend", "company": "Corp"}, {})
    assert len(res) == 1
    assert res[0]["category"] == "General"
    assert "Backend at Corp" in res[0]["question"]
