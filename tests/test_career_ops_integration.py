"""Comprehensive integration tests for CareerOps features and security hardening."""
import pytest
from src.legitimacy_filter import check_posting_legitimacy
from src.insights import evaluate_job_ag_blocks
from src.tailor import generate_strategic_cover_letter, COVER_LETTER_ANGLES
from src.persona_outreach import generate_persona_outreach
from src.story_bank import auto_extract_stories_from_profile, generate_reverse_interview_questions
from src.offer_analyzer import audit_offer_contract, analyze_salary_gap
from src.reply_classifier import classify_inbound_reply
from src.pdf_engine import render_html_resume


def test_block_g_scam_detection():
    """Verify Block G catches high-risk scam patterns."""
    scam_job = {
        "title": "Data Entry Specialist",
        "company": "FastTech",
        "description": "Urgent hire! No experience needed, earn $500/day for simple task. Contact our recruiter via Telegram @fasttech_recruiter to complete onboarding. We will send wire transfer for equipment."
    }
    res = check_posting_legitimacy(scam_job)
    assert res["is_scam"] is True
    assert res["risk_level"] == "HIGH"
    assert res["passed_prefilter"] is False
    assert res["legitimacy_score"] < 50


def test_block_g_work_auth_blocker():
    """Verify Block G flags strict citizenship / no-sponsorship requirements for candidates who need it."""
    cleared_job = {
        "title": "Defense Cloud Architect",
        "company": "AeroSpace Defense",
        "description": "Must be US Citizen with active Top Secret clearance. No C2C or visa sponsorship provided."
    }
    # Candidate who needs sponsorship
    res_need_visa = check_posting_legitimacy(cleared_job, candidate_prefs={"require_sponsorship": True})
    assert res_need_visa["work_auth_blocked"] is True
    assert res_need_visa["risk_level"] == "BLOCKED"
    assert res_need_visa["passed_prefilter"] is False

    # Candidate who does not need sponsorship
    res_citizen = check_posting_legitimacy(cleared_job, candidate_prefs={"require_sponsorship": False})
    assert res_citizen["work_auth_blocked"] is False
    assert res_citizen["risk_level"] in ("LOW", "MEDIUM")


def test_ag_blocks_structure():
    """Verify evaluate_job_ag_blocks returns all 7 blocks cleanly."""
    sample_job = {
        "id": 42,
        "title": "Senior Staff Platform Engineer",
        "company": "Stripe",
        "description": "Architect distributed transaction processing systems in Go and Python. High scale, 99.999% availability required. Kubernetes and AWS experience essential.",
        "salary_min": 180000,
        "salary_max": 240000,
        "currency": "USD"
    }
    sample_profile = {
        "name": "Jane Doe",
        "skills": ["Python", "Go", "Kubernetes", "AWS", "Distributed Systems", "PostgreSQL"],
        "experience": [
            {
                "title": "Senior Infrastructure Engineer",
                "company": "Fintech Corp",
                "bullets": ["Architected distributed ledger processing 10k ops/sec."]
            }
        ]
    }
    report = evaluate_job_ag_blocks(sample_job, sample_profile, prefs={})
    assert "block_a_role" in report
    assert "block_b_match" in report
    assert "block_c_level" in report
    assert "block_d_comp" in report
    assert "block_e_personalization" in report
    assert "block_f_interview_star" in report
    assert "block_g_legitimacy" in report
    assert report["block_g_legitimacy"]["passed_prefilter"] is True


def test_4_angle_cover_letters():
    """Verify all 4 strategic cover letter angles are defined and produce valid output."""
    assert len(COVER_LETTER_ANGLES) == 4
    for key in ("vision", "problem_solver", "methodology", "direct_executive"):
        assert key in COVER_LETTER_ANGLES
        assert "name" in COVER_LETTER_ANGLES[key]
        assert "instruction" in COVER_LETTER_ANGLES[key]


def test_persona_outreach_length_limit():
    """Verify LinkedIn messages respect the hard ≤300 characters rule."""
    sample_job = {
        "id": 10,
        "title": "Lead MLOps Engineer",
        "company": "Anthropic",
        "description": "Scale GPU inference clusters and manage PyTorch model serving pipelines."
    }
    sample_profile = {
        "name": "Alex Smith",
        "skills": ["Python", "PyTorch", "Kubernetes", "Ray", "Triton", "CUDA"]
    }
    outreach = generate_persona_outreach(sample_job, sample_profile, prefs={}, contact_name="Sarah")
    assert len(outreach["linkedin_hiring_manager"]) <= 300
    assert len(outreach["linkedin_recruiter"]) <= 300
    assert len(outreach["linkedin_peer"]) <= 300
    assert "email_application" in outreach
    assert "attachment_checklist" in outreach["email_application"]


def test_story_bank_and_reverse_interview():
    """Verify STAR+R story bank and reverse interview question generator."""
    sample_job = {"title": "Staff Backend Engineer", "company": "Airbnb", "description": "Microservices in Java and Python"}
    sample_profile = {"name": "Test User", "skills": ["Python", "Java", "Docker"]}
    
    stories = auto_extract_stories_from_profile(sample_profile, {})
    assert len(stories) >= 1
    assert "situation" in stories[0]
    assert "reflection" in stories[0]

    questions = generate_reverse_interview_questions(sample_job, {})
    assert len(questions) >= 1
    assert "question" in questions[0]
    assert "what_to_listen_for" in questions[0]


def test_offer_contract_auditor_and_salary_gap():
    """Verify offer contract clause auditor flags overreaching IP assignment and calculates gap."""
    contract = """
    EMPLOYMENT AGREEMENT
    All inventions, ideas, and intellectual property developed by Employee, whether or not during working hours
    and whether or not on Company premises, shall be the sole property of the Company.
    Employee agrees not to engage in any competitive business for a period of 12 months post-employment.
    """
    audit = audit_offer_contract(contract)
    assert len(audit["flagged_clauses"]) >= 2
    categories = [c["category"] for c in audit["flagged_clauses"]]
    assert "ip_assignment" in categories
    assert "non_compete" in categories

    salary_res = analyze_salary_gap(offered_base=150000, desired_base=175000, market_median=170000, currency="USD")
    assert salary_res["gap"] == 25000
    assert salary_res["gap_percent"] > 0
    assert "counter_email" in salary_res
    assert len(salary_res["alternative_levers"]) > 0


def test_reply_classifier():
    """Verify inbound recruiter email classifier correctly identifies status transitions."""
    rejection_email = "Thank you for your interest. Unfortunately, after careful consideration, we have decided to pursue other candidates whose qualifications more closely align with our current needs."
    r_res = classify_inbound_reply(rejection_email)
    assert r_res["category"] == "REJECTION"
    assert r_res["recommended_status"] == "Rejected"

    interview_email = "Hi! We were very impressed by your background and would like to invite you to schedule a 30-minute technical interview via Calendly: https://calendly.com/team/interview"
    i_res = classify_inbound_reply(interview_email)
    assert i_res["category"] == "INTERVIEW_INVITE"
    assert i_res["recommended_status"] == "Interview"
    assert i_res["action_required"] is True


def test_html_resume_template_rendering():
    """Verify semantic HTML5 template renders valid HTML with Space Grotesk and DM Sans."""
    sample_resume = {
        "name": "Jane Developer",
        "headline": "Staff AI Platform Engineer",
        "email": "jane@example.com",
        "phone": "+1 (555) 019-2834",
        "location": "San Francisco, CA",
        "summary": "Proven track record of scaling high-throughput distributed AI serving systems.",
        "skills": ["Python", "Rust", "PyTorch", "Kubernetes", "Redis", "Distributed Systems"],
        "experience": [
            {
                "title": "Principal Architect",
                "company": "CloudScale AI",
                "dates": "2023 - Present",
                "location": "San Francisco, CA",
                "bullets": [
                    "Engineered LLM inference gateway serving 50M daily tokens with 99.99% uptime.",
                    "Reduced GPU compute cost by $120k/month via dynamic batching."
                ]
            }
        ]
    }
    html = render_html_resume(sample_resume)
    assert "Jane Developer" in html
    assert "Space Grotesk" in html
    assert "DM Sans" in html
    assert "CloudScale AI" in html
    assert "Engineered LLM inference gateway" in html
