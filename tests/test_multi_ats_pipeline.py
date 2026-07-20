"""Tests for Multi-ATS Cross-Parser Pipeline."""
from src.multi_ats_pipeline import simulate_enterprise_ats_parsers, stage_instant_auto_apply


def test_simulate_enterprise_ats_parsers():
    sample_profile = {
        "name": "Animesh Shukla",
        "email": "animesh@example.com",
        "raw_text": "Experience Skills Education Projects Python AI LLM API GitHub: https://github.com/animesh8979",
        "skills": ["Python", "AI", "LLM", "API"],
        "links": {"github": "https://github.com/animesh8979"}
    }
    res = simulate_enterprise_ats_parsers(sample_profile)
    assert res["verified"] is True
    assert "parsers" in res
    assert "Greenhouse" in res["parsers"]
    assert "Workday" in res["parsers"]


def test_stage_instant_auto_apply():
    sample_profile = {
        "name": "Animesh Shukla",
        "email": "animesh@example.com",
        "raw_text": "Experience Skills Education Projects Python AI LLM API https://github.com/animesh8979",
        "skills": ["Python", "AI", "LLM"],
        "links": {"github": "https://github.com/animesh8979"}
    }
    staged = stage_instant_auto_apply(sample_profile)
    assert staged["staged"] is True
    assert staged["application_payload"]["status"] == "STAGED_READY_FOR_USER_REVIEW"
