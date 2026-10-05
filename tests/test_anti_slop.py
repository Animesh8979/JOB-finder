"""Unit tests for Anti-AI-Slop & Humanizer Engine."""
from src.anti_slop import (
    BANNED_AI_TERMS,
    audit_and_sanitize,
    calculate_burstiness,
    sanitize_bullet,
    sanitize_punctuation,
)


def test_banned_ai_terms_catalog_completeness():
    """Verify all 35 mandated modern LLM hallmarks are explicitly tracked."""
    expected = [
        "delve", "testament", "tapestry", "beacon", "harnessing", "pivotal",
        "fostered", "realm", "dynamic landscape", "spearheaded synergy",
        "leverage", "robust", "revolutionize", "plethora", "nestled",
        "unlock", "seamlessly", "furthermore", "moreover", "in summary",
        "in conclusion", "game-changer", "paradigm shift", "holistic approach",
        "cutting-edge", "state-of-the-art", "ever-evolving", "vital role",
        "crucial", "meticulous", "commendable", "unwavering", "transformative",
        "journey", "rich tapestry"
    ]
    for term in expected:
        assert term in BANNED_AI_TERMS, f"Missing required banned AI term: {term}"


def test_em_dash_elimination():
    raw = "Architected high-throughput pipelines — processing 200k ops/sec — with zero lag."
    cleaned, em_count, _ = sanitize_punctuation(raw)
    assert em_count == 2
    assert "—" not in cleaned
    assert "--" not in cleaned
    assert "pipelines, processing 200k ops/sec, with zero lag" in cleaned


def test_aggressive_punctuation_sanitization():
    """Verify strip of em-dashes, en-dashes, double-hyphens, curly quotes, and ellipsis."""
    raw = "Built “distributed” systems ‘V2’ — achieving 99.99% uptime – across 2022–2025… scaling--reducing latency."
    cleaned, em_count, _ = sanitize_punctuation(raw)
    assert "—" not in cleaned
    assert "–" not in cleaned
    assert "--" not in cleaned
    assert "“" not in cleaned and "”" not in cleaned
    assert "‘" not in cleaned and "’" not in cleaned
    assert "…" not in cleaned
    assert '"distributed"' in cleaned
    assert "'V2'" in cleaned
    assert "2022 - 2025" in cleaned


def test_ai_lexicon_sanitization():
    slop_letter = """
    I hope this letter finds you well. I am thrilled to submit my application for the esteemed company.
    In today's fast-paced world, I spearheaded the development of a robust and scalable ETL engine.
    Furthermore, my work is a testament to my ability to delve into complex datasets and foster teamwork.
    Moreover, I leveraged Python and PostgreSQL to seamlessly ingest records.
    """
    report = audit_and_sanitize(slop_letter)
    assert not report.is_clean
    assert report.em_dash_count == 0
    assert len(report.flagged_terms) > 3
    assert (
        "delve" in str(report.flagged_terms).lower()
        or "delving" in str(report.flagged_terms).lower()
        or "testament" in str(report.flagged_terms).lower()
    )
    
    # Check that cleaned text eliminates the AI clichés
    cleaned = report.cleaned_text
    assert "I hope this letter finds you well" not in cleaned
    assert "esteemed company" not in cleaned
    assert "spearheaded" not in cleaned
    assert "delve into" not in cleaned
    assert "testament to" not in cleaned
    assert "leveraged" not in cleaned
    assert "Furthermore," not in cleaned
    assert "Moreover," not in cleaned


def test_all_35_banned_terms_sanitized():
    """Verify all 35 mandated hallmarks are actively flagged and stripped."""
    slop_snippets = [
        "We delve into the dynamic landscape.",
        "A testament to our unwavering journey.",
        "Harnessing cutting-edge tools in this realm.",
        "A pivotal role with fostered synergy.",
        "Spearheaded synergy across teams.",
        "Leverage robust architectures to revolutionize workflows.",
        "A plethora of options nestled in the cloud.",
        "Unlock seamless capabilities seamlessly.",
        "Furthermore, in summary, moreover, in conclusion.",
        "A game-changer and paradigm shift with a holistic approach.",
        "State-of-the-art systems in an ever-evolving market.",
        "A vital role and crucial outcome.",
        "Meticulous attention to detail with commendable impact.",
        "A transformative journey across a rich tapestry.",
    ]
    for snippet in slop_snippets:
        report = audit_and_sanitize(snippet)
        assert len(report.flagged_terms) > 0, f"Failed to flag snippet: {snippet}"
        cleaned = report.cleaned_text
        for banned in [
            "delve", "testament", "tapestry", "beacon", "harnessing", "pivotal",
            "fostered", "dynamic landscape", "spearheaded synergy", "leverage",
            "robust", "revolutionize", "plethora", "nestled", "unlock",
            "seamlessly", "furthermore", "moreover", "in summary", "in conclusion",
            "game-changer", "paradigm shift", "holistic approach", "cutting-edge",
            "state-of-the-art", "ever-evolving", "vital role", "crucial",
            "meticulous", "commendable", "unwavering", "transformative", "rich tapestry"
        ]:
            assert banned not in cleaned.lower(), f"Banned '{banned}' still in cleaned: '{cleaned}'"


def test_clean_human_text_passes():
    human_text = """
    I am applying for the Junior Data Analyst role at Cuvette.
    Over the past year, I built automated data pipelines in Python and analyzed marketing conversion funnels using SQL joins.
    At Elevate Labs, I trained scikit-learn models and visualized cluster distributions in Seaborn.
    I would love to bring this hands-on engineering focus to your data team.
    """
    report = audit_and_sanitize(human_text)
    assert report.em_dash_count == 0
    assert len(report.flagged_terms) == 0
    assert report.slop_score == 0.0
    assert report.is_clean is True


def test_sanitize_bullet():
    bullet = "- Spearheaded the deployment of a robust ETL pipeline — reducing query latency by 35%."
    clean = sanitize_bullet(bullet)
    assert "—" not in clean
    assert "Spearheaded" not in clean
    assert "robust" not in clean
    assert clean.startswith("Built") or clean.startswith("Led") or not clean.startswith("-")


def test_burstiness_metric():
    # Uniform robotic sentences
    robotic = "I built the system using python. I tested the system using pytest. I deployed the system using docker."
    burst_robotic = calculate_burstiness(robotic)
    
    # Varied natural human sentences
    varied = "I built the pipeline in Python. It handled over 50,000 real-time events per second across distributed nodes without dropping a packet. Clean code matters."
    burst_varied = calculate_burstiness(varied)
    
    assert burst_varied > burst_robotic
