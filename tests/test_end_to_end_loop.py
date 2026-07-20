"""End-to-End Autonomous Audit -> GitHub Evidence Ledger -> Multi-ATS -> Auto-Apply Staging Loop Test."""
import json
from src.autonomous_resume_agent import audit_and_autofix_resume


def test_full_autonomous_loop_end_to_end():
    sample_profile = {
        "name": "Animesh Shukla",
        "email": "animesh@example.com",
        "summary": "AI Engineer building autonomous LLM agents and multi-agent systems.",
        "skills": ["Python", "AI", "LLM", "API", "System Design"],
        "links": {"github": "https://github.com/animesh8979"},
        "experience": [
            {
                "company": "AI Labs",
                "title": "Senior Engineer",
                "bullets": [
                    "worked on llm pipelines and improved accuracy",
                    "handled backend server deployments"
                ]
            }
        ],
        "projects": [
            {
                "name": "AI Job Finder",
                "description": "Full-stack AI job finder with autonomous resume audit and apply."
            }
        ]
    }

    result = audit_and_autofix_resume(sample_profile)

    # 1. Verify Status & Score Calculation
    assert result["status"] == "success"
    assert "before_score" in result
    assert "after_score" in result
    assert "score_delta" in result

    # 2. Verify GitHub Evidence Ledger Integration
    assert "evidence_ledger" in result
    assert "top_projects" in result

    # 3. Verify Multi-ATS Cross-Parser Audit
    assert "multi_ats_audit" in result
    multi_ats = result["multi_ats_audit"]
    assert "parsers" in multi_ats
    assert "HackerRank" in multi_ats["parsers"]
    assert "Greenhouse" in multi_ats["parsers"]
    assert "Workday" in multi_ats["parsers"]
    assert "Lever" in multi_ats["parsers"]

    # 4. Verify Auto-Apply Staged Payload
    assert "auto_apply_staged" in result
    staged = result["auto_apply_staged"]
    assert staged["staged"] is True
    assert staged["application_payload"]["status"] == "STAGED_READY_FOR_USER_REVIEW"

    # 5. Verify Ready to Apply Flag
    assert result["ready_to_apply"] is True
