import pytest
from src.recruiter_score import score_job
from src.matcher import score_jobs

def test_score_job_rubric_breakdown():
    job = {
        "title": "Senior Python Backend Engineer",
        "description": "We are looking for a senior engineer skilled in Python, FastAPI, and Docker. Must have strong backend architecture experience. Remote opportunity.",
        "remote": 1,
        "salary_min": 150000,
        "salary_max": 180000,
        "tags": ["python", "fastapi", "docker"]
    }
    profile = {
        "skills": ["python", "fastapi", "docker", "postgres"],
        "years_experience": 6,
        "experience": [{"title": "Senior Python Developer"}]
    }
    prefs = {
        "titles": ["Python Backend Engineer"],
        "seniority": "senior",
        "min_salary": 140000
    }

    report = score_job(job, profile, prefs)
    assert report.total <= 100
    assert report.total >= 0
    assert report.breakdown["skills"] <= 30
    assert report.breakdown["role"] <= 20
    assert report.breakdown["seniority"] <= 20
    assert report.breakdown["location"] <= 15
    assert report.breakdown["salary"] <= 10
    assert report.breakdown["freshness"] <= 5
    # High match expectations
    assert report.breakdown["skills"] > 15
    assert report.breakdown["role"] == 20
    assert report.breakdown["seniority"] == 20
    assert report.breakdown["location"] == 15
    assert report.breakdown["salary"] == 10

def test_score_job_red_flags():
    job = {
        "title": "Principal Architect",
        "description": "Looking for 15+ years experience.",
        "remote": 0,
        "location": "New York, NY",
        "salary_max": 90000
    }
    profile = {
        "skills": ["html"],
        "years_experience": 1
    }
    prefs = {
        "remote_only": True,
        "min_salary": 120000
    }
    report = score_job(job, profile, prefs)
    assert len(report.red_flags) >= 2
    assert any("Salary maximum" in f for f in report.red_flags)
    assert any("Requires on-site/hybrid" in f for f in report.red_flags)
