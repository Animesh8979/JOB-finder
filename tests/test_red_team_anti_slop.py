"""SWAT Red-Team Lead 2: Brutal Anti-Slop Adversarial Stress Test Suite.

Exhaustive stress tests verifying zero AI slop, zero em-dashes, burstiness boost >= 0.20,
ATS vector Typst CV compilation purity, outreach humanization, and idempotence invariants.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from src import cv_builder, persona_outreach, tailor
from src.anti_slop import (
    audit_and_sanitize,
    calculate_burstiness,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def animesh_profile() -> dict[str, Any]:
    """Load Animesh Shukla's canonical verified profile."""
    default_json = PROJECT_ROOT / "data" / "profiles" / "default.json"
    if default_json.exists():
        return json.loads(default_json.read_text(encoding="utf-8"))
    return {
        "name": "Animesh Shukla",
        "email": "ani.shukla2003@gmail.com",
        "phone": "+91 89794 72393",
        "location": "Agra, Uttar Pradesh / Remote",
        "headline": "Business Analyst · Data & Analytics · AI Automation",
        "summary": (
            "Bachelor of Business Administration (BBA) graduate specialising in Artificial Intelligence "
            "(AI) & Machine Learning (ML), IILM University, May 2026, with two internships, three independently "
            "built AI automation systems, and a HackerRank SQL (Advanced) certification. Combines Python data science, "
            "multi-agent AI architecture, and digital marketing analytics with a business degree."
        ),
        "skills": [
            "Python", "pandas", "NumPy", "Matplotlib", "Seaborn", "SQL",
            "EDA", "Multi Agent Systems", "Generative AI", "Workflow Automation"
        ],
        "years_experience": 1,
        "experience": [
            {
                "title": "Machine Learning Intern",
                "company": "Elevate Labs",
                "location": "Remote, India",
                "start": "Jun 2025",
                "end": "Jul 2025",
                "bullets": [
                    "Designed and delivered an end-to-end ML project with regression and classification models in Python.",
                    "Authored data science benchmarking report reviewed and approved by senior mentors.",
                    "Presented EDA visualisations in weekly mentor reviews.",
                    "Best Performer Award for project quality and self-direction."
                ]
            }
        ],
        "education": [
            {
                "degree": "B.B.A.",
                "field": "Artificial Intelligence & Machine Learning",
                "school": "IILM University",
                "year": "2023 - 2026"
            }
        ],
        "links": {
            "linkedin": "https://linkedin.com/in/animesh-shukla",
            "github": "https://github.com/animesh8979"
        }
    }


@pytest.fixture
def target_job() -> dict[str, Any]:
    """Realistic job posting for tailoring and outreach."""
    return {
        "id": 9901,
        "job_id": "9901",
        "company": "Kinetix Analytics & AI",
        "title": "Data Analyst / AI Automation Specialist",
        "location": "Remote",
        "description": (
            "Seeking an AI Automation Specialist and Data Analyst skilled in Python, SQL, "
            "EDA, regression/classification models, and KPI dashboards. Responsible for "
            "building multi-agent pipelines and automating business reports."
        )
    }


# =============================================================================
# 1. ADVERSARIAL SLOP INJECTION ATTACKS (20+ Worst-Case Paragraphs)
# =============================================================================

ADVERSARIAL_PARAGRAPHS = [
    # 1. Delve + dynamic landscape + testament + em-dashes + beacon
    (
        "In today's fast-paced world, we must delve into the dynamic landscape of modern engineering. "
        "Our work serves as a testament to our relentless pursuit of excellence. "
        "We spearheaded the development of a robust and scalable architecture — delivering 99.9% uptime. "
        "Furthermore, our rich tapestry of tools allows us to seamlessly orchestrate microservices. "
        "We stand as a beacon of innovation across the entire organization."
    ),
    # 2. Sycophantic tropes + delve + foster synergy + em-dash
    (
        "I am thrilled to submit my application for the esteemed company. "
        "Delving into complex datasets has always been my core passion. "
        "My experience is a testament to my ability to foster synergy across cross-functional teams — achieving record results. "
        "Moreover, I leveraged cutting-edge machine learning models to revolutionize data ingestion. "
        "In conclusion, I hope this letter finds you well."
    ),
    # 3. Monotonic zero-variance sentence lengths (6 words each)
    (
        "We built the system for you. We built the engine for you. "
        "We built the network for you. We built the service for you."
    ),
    # 4. Em-dashes + double hyphens + pivotal role + semicolons
    (
        "I engineered pipelines — specifically distributed Kafka clusters — with zero downtime. "
        "My work played a pivotal role in unlocking the potential of our telemetry stack. "
        "We harnessed the power of cloud computing to seamlessly scale operations. "
        "Semicolons are also present; however, the pipeline never dropped a single packet."
    ),
    # 5. State-of-the-art + holistic + game-changer + tapestry
    (
        "In the ever-evolving realm of artificial intelligence, state-of-the-art architectures are paramount. "
        "Our holistic approach to data modeling was a game-changer for enterprise analytics. "
        "We meticulously architected each ETL pipeline — reducing latency by 45% — while maintaining data integrity. "
        "It represents a rich tapestry of deep technical capabilities."
    ),
    # 6. Dynamic landscape + plethora + beacon + spearheaded synergy
    (
        "Navigating today's dynamic landscape requires a plethora of adaptable skills and tools. "
        "As a beacon of technical leadership, I spearheaded synergy across distributed teams. "
        "Delving into production telemetry revealed critical bottlenecks that we resolved seamlessly. "
        "This stands as a testament to our engineering discipline."
    ),
    # 7. Unwavering + professional journey + pivotal role in revolutionizing
    (
        "The candidate demonstrated unwavering commitment throughout their entire professional journey. "
        "They played a pivotal role in revolutionizing our core backend services. "
        "Leveraging Python and SQL, they tackled data problems holistically. "
        "Each milestone was a testament to their meticulous execution — ensuring zero regressions."
    ),
    # 8. Monotonic zero-variance sentence lengths (5 words each)
    (
        "Our team created the platform. Our team tested the platform. "
        "Our team deployed the platform. Our team verified the platform."
    ),
    # 9. Transformative journey + nestled in + tapestry + beacon
    (
        "We embarked on a transformative journey nestled in the heart of modern Silicon Valley. "
        "Delving into uncharted technical territories was our daily mission. "
        "The rich tapestry of our codebase seamlessly supported millions of queries — operating without friction. "
        "Furthermore, our solutions served as a beacon in the industry."
    ),
    # 10. Dynamic market + cutting-edge + holistic + commendable
    (
        "In today's dynamic market, companies must unlock the potential of data. "
        "We spearheaded the adoption of cutting-edge streaming frameworks. "
        "Our holistic approach ensured that databases scaled robustly and securely. "
        "The results were a testament to our team's commendable efforts."
    ),
    # 11. Monotonic zero-variance sentence lengths (9 words each)
    (
        "The quick brown fox jumps over the lazy dog. "
        "The quick brown fox jumps over the lazy dog. "
        "The quick brown fox jumps over the lazy dog."
    ),
    # 12. Unicode punctuation tricks: curly quotes, curly apostrophes, ellipsis, en-dash range
    (
        '“We must delve into the data,” said the lead engineer — pausing thoughtfully… '
        'The team’s ‘state-of-the-art’ models functioned seamlessly across distributed nodes – handling 2023–2026 workloads.'
    ),
    # 13. Ecstatic to apply + pivotal role + esteemed organization + In summary
    (
        "I am ecstatic to apply for this pivotal role within your esteemed organization. "
        "Delving into analytics has allowed me to foster teamwork across remote groups. "
        "My past achievements serve as a testament to my dedication. "
        "In summary, I look forward to contributing seamlessly."
    ),
    # 14. Preserve end-to-end and multi-agent while purging delve, beacon, tapestry
    (
        "Engineered end-to-end data processing pipelines using multi-agent architectures. "
        "We must delve into edge cases to guarantee high availability. "
        "Our system stands as a beacon of reliability — processing 500,000 transactions daily. "
        "The rich tapestry of services operates with precision."
    ),
    # 15. Spearheading synergy + game-changing + ever-changing landscape
    (
        "Spearheading synergy between data science and product was a game-changing endeavor. "
        "We leveraged neural search to delve into millions of unindexed documents. "
        "Our platform seamlessly surfaced insights across the ever-changing landscape of customer demands. "
        "This is a testament to our technical rigor."
    ),
    # 16. Monotonic zero-variance sentence lengths (5 words each)
    (
        "Data models must perform reliably. Cloud systems must scale smoothly. "
        "Server nodes must respond quickly. Test suites must pass cleanly."
    ),
    # 17. Paradigm shift + robust and scalable + unwavering
    (
        "In today's fast-paced world, embracing a paradigm shift is essential. "
        "We fostered innovation by unlocking the potential of distributed computing. "
        "The architecture proved to be robust and scalable — weathering peak loads seamlessly. "
        "It remains a testament to our unwavering focus."
    ),
    # 18. Meticulous attention to detail + delve + beacon
    (
        "I spearheaded the initiative with meticulous attention to detail and care. "
        "Delving into legacy codebases allowed us to modernize antiquated workflows. "
        "The resulting microservices communicate seamlessly — achieving sub-millisecond latencies. "
        "Our journey stands as a beacon for other engineering pods."
    ),
    # 19. Multi-agent + state-of-the-art + plethora of
    (
        "We built multi-agent frameworks — deploying state-of-the-art algorithms — across 10 distributed clusters. "
        "Our holistic telemetry provided real-time observability into latency spikes. "
        "Furthermore, we eliminated a plethora of redundant queries to bolster throughput."
    ),
    # 20. Tapestry + pivotal role + dynamic landscape
    (
        "This project is a testament to our ability to navigate the dynamic landscape of AI. "
        "We delve into cutting-edge research to build transformative products. "
        "Each component integrates seamlessly — creating a rich tapestry of functionality. "
        "The team played a pivotal role in every release."
    ),
    # 21. Monotonic zero-variance sentence lengths (6 words each)
    (
        "The models predict customer behavior accurately. "
        "The dashboards render monthly analytics clearly. "
        "The services process background jobs efficiently."
    ),
    # 22. Unique blend of + revolutionize + delve + scikit-learn
    (
        "I am confident that my unique blend of skills will revolutionize your systems. "
        "Delving into data pipelines is a testament to my technical enthusiasm. "
        "I leveraged scikit-learn and PyTorch to seamlessly train classifiers — boosting accuracy by 18%."
    ),
]


def test_adversarial_slop_injection_attacks_22_paragraphs():
    """Attack vector: Feed 22 worst-case slop paragraphs. Assert 100% em-dash purge, banned terms purge, and burstiness >= 0.20."""
    banned_targets = [
        "delve",
        "tapestry",
        "testament",
        "beacon",
        "seamlessly",
        "pivotal",
        "dynamic landscape",
        "state-of-the-art",
        "spearhead",
    ]

    assert len(ADVERSARIAL_PARAGRAPHS) >= 20

    for idx, raw_paragraph in enumerate(ADVERSARIAL_PARAGRAPHS, start=1):
        report = audit_and_sanitize(raw_paragraph)

        # 1. Assert 100% em-dashes and parenthetical double hyphens purged
        assert "—" not in report.cleaned_text, f"Paragraph {idx} contained em-dash: {report.cleaned_text}"
        assert "\u2014" not in report.cleaned_text, f"Paragraph {idx} contained unicode em-dash: {report.cleaned_text}"
        assert " -- " not in report.cleaned_text, f"Paragraph {idx} contained double hyphen: {report.cleaned_text}"

        # 2. Assert all banned terms purged from cleaned output
        lower_cleaned = report.cleaned_text.lower()
        for term in banned_targets:
            assert term not in lower_cleaned, f"Paragraph {idx} contained banned term '{term}': {report.cleaned_text}"

        # 3. Assert burstiness score is boosted to >= 0.20
        assert report.burstiness_score >= 0.20, f"Paragraph {idx} burstiness_score {report.burstiness_score} < 0.20"
        computed_burst = calculate_burstiness(report.cleaned_text)
        assert computed_burst >= 0.20, f"Paragraph {idx} computed burstiness {computed_burst} < 0.20"

        # 4. Assert re-audited cleaned text passes cleanly
        re_audit = audit_and_sanitize(report.cleaned_text)
        assert re_audit.is_clean is True, f"Paragraph {idx} re-audit not clean: {re_audit}"
        assert re_audit.em_dash_count == 0, f"Paragraph {idx} re-audit has em_dash_count > 0"
        assert re_audit.slop_score == 0.0, f"Paragraph {idx} re-audit has slop_score > 0"
        assert len(re_audit.flagged_terms) == 0, f"Paragraph {idx} re-audit flagged: {re_audit.flagged_terms}"


# =============================================================================
# 2. REAL TAILORING PIPELINE END-TO-END STRESS TEST
# =============================================================================

def test_real_tailoring_pipeline_end_to_end_stress_test(animesh_profile, target_job):
    """Stress test tailor.tailor_resume() and tailor.cover_letter() with Animesh Shukla's profile."""
    prefs: dict[str, Any] = {}

    # 1. Test resume tailoring
    tailored = tailor.tailor_resume(target_job, animesh_profile, prefs)
    assert isinstance(tailored, dict)
    assert tailored.get("name") == "Animesh Shukla"

    # Check summary
    summary = tailored.get("summary", "")
    assert len(summary) > 0
    assert "—" not in summary and "--" not in summary
    sum_audit = audit_and_sanitize(summary)
    assert sum_audit.is_clean is True, f"Tailored summary not clean: {sum_audit}"
    assert sum_audit.em_dash_count == 0
    assert len(sum_audit.flagged_terms) == 0

    # Check experience bullets
    experience = tailored.get("experience", [])
    assert len(experience) > 0
    for exp in experience:
        for b in exp.get("bullets", []):
            assert "—" not in b and "--" not in b
            b_audit = audit_and_sanitize(b)
            assert b_audit.is_clean is True, f"Bullet not clean: '{b}' -> {b_audit}"
            assert b_audit.em_dash_count == 0
            assert len(b_audit.flagged_terms) == 0

    # Check project bullets
    for proj in tailored.get("projects", []):
        for b in proj.get("bullets", []):
            assert "—" not in b and "--" not in b
            b_audit = audit_and_sanitize(b)
            assert b_audit.is_clean is True
            assert b_audit.em_dash_count == 0

    # 2. Test cover letter generation
    cl_text = tailor.cover_letter(target_job, animesh_profile, prefs)
    assert isinstance(cl_text, str)
    assert len(cl_text) > 100
    assert "—" not in cl_text and "--" not in cl_text

    cl_audit = audit_and_sanitize(cl_text)
    assert cl_audit.is_clean is True, f"Cover letter not clean: {cl_audit}"
    assert cl_audit.em_dash_count == 0
    assert len(cl_audit.flagged_terms) == 0
    assert cl_audit.slop_score == 0.0


# =============================================================================
# 3. TYPST CV VECTOR COMPILATION PURITY
# =============================================================================

def test_typst_cv_vector_compilation_purity(animesh_profile, tmp_path):
    """Verify build_typst_resume() output has 0 em-dashes, 0 math crashes, 0 label collisions, and compiles to PDF."""
    # Inject adversarial slop and syntax triggers into profile copy
    adv_profile = json.loads(json.dumps(animesh_profile))
    adv_profile["headline"] = "Business Analyst — Data & Analytics — AI Automation"
    adv_profile["experience"][0]["dates"] = "2023 — 2026"
    adv_profile["experience"][0]["bullets"].extend([
        "Managed $150,000 project budget and saved $35,000 in cloud computing costs.",
        "Collaborated with @recruiter on GitHub and reached out via ani@test.com.",
        "Engineered low-latency streaming pipeline — processing 250k events/sec — with zero lag.",
    ])
    adv_profile["certifications"] = [
        "HackerRank SQL (Advanced) — Certified 2025",
        "AWS Cloud Practitioner ($100 examination voucher)"
    ]

    typst_source = cv_builder.build_typst_resume(adv_profile)

    # 1. Assert 0 em-dashes in Typst markup
    assert "—" not in typst_source, "Typst markup contains em-dash"
    assert " -- " not in typst_source, "Typst markup contains unescaped double hyphen"

    # 2. Assert 0 math mode crashes: every $ must be escaped as \$
    unescaped_dollars = re.findall(r"(?<!\\)\$", typst_source)
    assert len(unescaped_dollars) == 0, f"Typst markup contains unescaped $: {unescaped_dollars}"

    # 3. Assert 0 label collisions: every @ must be escaped as \@
    unescaped_ats = re.findall(r"(?<!\\)@", typst_source)
    assert len(unescaped_ats) == 0, f"Typst markup contains unescaped @: {unescaped_ats}"

    # 4. Compile vector PDF directly using Typst compiler
    output_pdf = tmp_path / "animesh_typst_red_team.pdf"
    rendered_path = cv_builder.render_typst_direct(typst_source, output_pdf)

    assert rendered_path is not None, "Typst compilation returned None"
    assert output_pdf.exists(), "Compiled Typst PDF file does not exist"
    assert output_pdf.stat().st_size > 2000, f"PDF file size suspiciously small: {output_pdf.stat().st_size} bytes"


# =============================================================================
# 4. OUTREACH & COLD EMAIL STRESS TEST
# =============================================================================

def test_outreach_and_cold_email_stress_test(animesh_profile, target_job):
    """Call persona_outreach generator and assert 0 AI hallmarks, 0 em-dashes, and length <= 300."""
    prefs: dict[str, Any] = {}
    outreach = persona_outreach.generate_persona_outreach(
        target_job, animesh_profile, prefs, contact_name="Sarah Connor"
    )

    assert isinstance(outreach, dict)

    # 1. LinkedIn Hiring Manager
    hm = outreach.get("linkedin_hiring_manager", "")
    assert len(hm) > 0
    assert len(hm) <= 300, f"Hiring Manager note exceeded 300 chars: {len(hm)}"
    assert "—" not in hm and "--" not in hm
    hm_audit = audit_and_sanitize(hm)
    assert hm_audit.is_clean is True, f"HM outreach not clean: {hm_audit}"
    assert hm_audit.em_dash_count == 0

    # 2. LinkedIn Recruiter
    rec = outreach.get("linkedin_recruiter", "")
    assert len(rec) > 0
    assert len(rec) <= 300, f"Recruiter note exceeded 300 chars: {len(rec)}"
    assert "—" not in rec and "--" not in rec
    rec_audit = audit_and_sanitize(rec)
    assert rec_audit.is_clean is True, f"Recruiter outreach not clean: {rec_audit}"
    assert rec_audit.em_dash_count == 0

    # 3. LinkedIn Peer
    peer = outreach.get("linkedin_peer", "")
    assert len(peer) > 0
    assert len(peer) <= 300, f"Peer note exceeded 300 chars: {len(peer)}"
    assert "—" not in peer and "--" not in peer
    peer_audit = audit_and_sanitize(peer)
    assert peer_audit.is_clean is True, f"Peer outreach not clean: {peer_audit}"
    assert peer_audit.em_dash_count == 0

    # 4. Formal Email Application
    email_app = outreach.get("email_application", {})
    sub = email_app.get("subject", "")
    body = email_app.get("body", "")
    assert len(sub) > 0 and len(body) > 0
    assert "—" not in sub and "--" not in sub
    assert "—" not in body and "--" not in body

    sub_audit = audit_and_sanitize(sub)
    body_audit = audit_and_sanitize(body)
    assert sub_audit.is_clean is True
    assert body_audit.is_clean is True
    assert sub_audit.em_dash_count == 0
    assert body_audit.em_dash_count == 0


# =============================================================================
# 5. IDEMPOTENCE & CADENCE INVARIANTS
# =============================================================================

def test_idempotence_and_cadence_invariants():
    """Verify that running sanitation twice produces identical results and preserves legitimate terms."""
    samples = [
        "Architected multi-agent pipelines and end-to-end data systems using scikit-learn and Python.",
        "Built state-of-the-art predictive models — achieving 94.5% precision on customer churn prediction.",
        "Spearheaded synergy between data science and product teams across the dynamic landscape.",
        "Delving into 2023 - 2026 metrics revealed $50,000 savings and 15% latency reduction.",
        "We built the system for you. We built the engine for you. We built the network for you."
    ]

    for sample in samples:
        pass1 = audit_and_sanitize(sample).cleaned_text
        pass2 = audit_and_sanitize(pass1).cleaned_text
        # Idempotence: sanitation applied twice must equal sanitation applied once
        assert pass1 == pass2, f"Idempotence violated: '{pass1}' != '{pass2}'"

    # Invariant: 'state-of-the-art' is purged/cleaned to 'modern'
    sota_text = "Deployed state-of-the-art architectures across all nodes."
    sota_cleaned = audit_and_sanitize(sota_text).cleaned_text
    assert "state-of-the-art" not in sota_cleaned.lower()
    assert "modern" in sota_cleaned.lower()

    # Invariant: legitimate technical hyphenated terms are preserved
    tech_text = "Built multi-agent pipelines with end-to-end scikit-learn models and cross-validation."
    tech_cleaned = audit_and_sanitize(tech_text).cleaned_text
    assert "multi-agent" in tech_cleaned
    assert "end-to-end" in tech_cleaned
    assert "scikit-learn" in tech_cleaned
    assert "cross-validation" in tech_cleaned

    # Invariant: valid numbers, percentages, and currencies are preserved
    metrics_text = "Handled 250,000 daily events with 99.9% uptime, saving $50,000 across 2023 - 2026."
    metrics_cleaned = audit_and_sanitize(metrics_text).cleaned_text
    assert "250,000" in metrics_cleaned
    assert "99.9%" in metrics_cleaned
    assert "$50,000" in metrics_cleaned
    assert "2023 - 2026" in metrics_cleaned
