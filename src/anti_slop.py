"""Anti-AI-Slop & Humanizer Engine.

Eliminates AI hallmarks, em-dashes, robotic clichés, and sycophantic tropes
from generated resumes, cover letters, and outreach mssages.
Ensures application materials sound like a sharp, authentic, grounded human builder.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple


# Cliché AI buzzwords and phrases mapped to natural human alternatives
AI_SLOP_REPLACEMENTS: List[Tuple[str, str]] = [
    # Verbs and participles
    (r"\bdelve into\b", "explore"),
    (r"\bdelving into\b", "exploring"),
    (r"\bdelve\b", "dig into"),
    (r"\bspearheaded the development of\b", "built"),
    (r"\bspearheaded\b", "built"),
    (r"\bleveraging\b", "using"),
    (r"\bleveraged\b", "used"),
    (r"\bleverage\b", "use"),
    (r"\bfostering\b", "building"),
    (r"\bfostered\b", "built"),
    (r"\bfoster\b", "encourage"),
    (r"\brevolutionizing\b", "modernizing"),
    (r"\brevolutionized\b", "overhauled"),
    (r"\brevolutionize\b", "improve"),
    
    # Nouns & Clichés
    (r"\ba testament to\b", "proof of"),
    (r"\btestament\b", "evidence"),
    (r"\brich tapestry\b", "diverse range"),
    (r"\btapestry of\b", "collection of"),
    (r"\btapestry\b", "combination"),
    (r"\bbeacon of\b", "leader in"),
    (r"\bpivotal role\b", "key role"),
    (r"\bpivotal\b", "key"),
    (r"\bgame-changer\b", "major advantage"),
    (r"\bdeep dive\b", "detailed look"),
    
    # Adjectives & Adverbs
    (r"\bholistic approach\b", "thorough approach"),
    (r"\bholistically\b", "thoroughly"),
    (r"\bholistic\b", "comprehensive"),
    (r"\bseamlessly\b", "smoothly"),
    (r"\bseamless\b", "smooth"),
    (r"\brobust and scalable\b", "reliable"),
    (r"\brobust\b", "reliable"),
    (r"\btransformative\b", "high-impact"),
    (r"\bmeticulous\b", "thorough"),
    (r"\bmeticulously\b", "carefully"),
    (r"\bcutting-edge\b", "modern"),
    (r"\bdynamic and fast-paced\b", "fast-moving"),
    (r"\bin today's dynamic\b", "in today's"),
    (r"\bin today's fast-paced world\b", "today"),
    (r"\bin the ever-evolving realm of\b", "in"),
    (r"\bin the realm of\b", "in"),
    
    # Sycophantic cover letter tropes
    (r"\bI hope this letter finds you well[.,]?\b", ""),
    (r"\bI am thrilled to submit my application for\b", "I am applying for"),
    (r"\bI am ecstatic to apply for\b", "I am applying for"),
    (r"\bI am writing with great enthusiasm to apply for\b", "I am applying for"),
    (r"\besteemed company\b", "company"),
    (r"\besteemed organization\b", "organization"),
    (r"\besteemed team\b", "team"),
    (r"\bresonates deeply with me\b", "aligns with my work"),
    (r"\bI am confident that my unique blend of\b", "My"),
    
    # Robotic transitional deadwood
    (r"\bFurthermore\b,?\s*", "Also, "),
    (r"\bMoreover\b,?\s*", "In addition, "),
    (r"\bIn conclusion\b,?\s*", ""),
    (r"\bTo summarize\b,?\s*", ""),
]


@dataclass
class SlopAuditReport:
    """Audit outcome for AI linguistic markers and slop."""
    raw_text: str
    cleaned_text: str
    em_dash_count: int
    semicolon_count: int
    flagged_terms: List[str]
    burstiness_score: float
    is_clean: bool
    slop_score: float  # 0.0 (100% human) to 1.0 (obvious AI)


def sanitize_punctuation(text: str) -> Tuple[str, int, int]:
    """Eliminates em-dashes, en-dashes, and reduces semicolons.
    
    Returns (cleaned_text, em_dash_count, semicolon_count).
    """
    if not text:
        return "", 0, 0

    em_dash_count = len(re.findall(r"[—\u2014]", text)) + len(re.findall(r"\s--\s", text))
    semicolon_count = len(re.findall(r";", text))

    cleaned = text

    # 1. Replace em-dashes surrounded by words or spaces with natural punctuation
    # Example: "Python — specifically FastAPI — for backend" -> "Python, specifically FastAPI, for backend"
    # Example: "Led the team — achieving 20% gain" -> "Led the team, achieving 20% gain"
    cleaned = re.sub(r"\s*[—\u2014]\s*", ", ", cleaned)
    cleaned = re.sub(r"\s+--\s+", ", ", cleaned)
    
    # 2. Fix numeric ranges: ensure en-dash between numbers becomes a plain hyphen (2023 - 2026)
    cleaned = re.sub(r"(\d+)\s*[–\u2013]\s*(\d+)", r"\1 - \2", cleaned)
    # Standalone en-dash to hyphen or comma
    cleaned = re.sub(r"\s*[–\u2013]\s*", " - ", cleaned)

    # 3. Reduce semicolons: replace semicolon with period or comma
    # If followed by capital letter or transition word: period
    cleaned = re.sub(r";\s*(However|Therefore|Furthermore|Moreover|In addition)", r". \1", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r";\s*", ", ", cleaned)

    # Clean up double commas, double spaces, or comma-period anomalies
    cleaned = re.sub(r",\s*,+", ",", cleaned)
    cleaned = re.sub(r",\s*\.", ".", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\n\s{2,}", "\n", cleaned)

    return cleaned.strip(), em_dash_count, semicolon_count


def calculate_burstiness(text: str) -> float:
    """Calculate sentence length variation (burstiness).
    
    Human writing alternates between short punchy sentences and medium technical ones.
    LLMs write unnaturally uniform sentences (standard deviation close to zero).
    Returns ratio of std_dev / mean sentence length (higher = more human).
    """
    sentences = re.split(r"[.!?]+", text)
    word_counts = [len(s.split()) for s in sentences if s.strip()]
    if len(word_counts) < 2:
        return 1.0  # Cannot compute for single sentence
        
    mean_len = sum(word_counts) / len(word_counts)
    if mean_len == 0:
        return 1.0
        
    variance = sum((w - mean_len) ** 2 for w in word_counts) / len(word_counts)
    std_dev = variance ** 0.5
    return round(std_dev / mean_len, 3)


def audit_and_sanitize(text: str) -> SlopAuditReport:
    """Full-pass anti-AI-slop audit and sanitization."""
    if not text:
        return SlopAuditReport(
            raw_text="",
            cleaned_text="",
            em_dash_count=0,
            semicolon_count=0,
            flagged_terms=[],
            burstiness_score=1.0,
            is_clean=True,
            slop_score=0.0
        )

    # Step 1: Punctuation sanitization
    cleaned, em_dash_count, semi_count = sanitize_punctuation(text)

    # Step 2: Lexicon sanitization and term tracking
    flagged = []
    for pattern, replacement in AI_SLOP_REPLACEMENTS:
        matches = re.findall(pattern, cleaned, flags=re.IGNORECASE)
        if matches:
            flagged.extend(set(matches))
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    # Step 3: Polish grammar and formatting artifacts
    cleaned = re.sub(r"\b([Aa])\s+([aeiouAEIOU])", r"\1n \2", cleaned)  # "a explore" -> "an explore" fix if any
    cleaned = re.sub(r"\b([Aa])n\s+([bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ])", r"\1 \2", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)

    # Step 4: Metric scoring
    burstiness = calculate_burstiness(cleaned)
    
    # Calculate slop score
    penalty = 0.0
    penalty += em_dash_count * 0.25
    penalty += len(flagged) * 0.15
    penalty += semi_count * 0.05
    if burstiness < 0.20:  # Rigid uniform length
        penalty += 0.20

    slop_score = round(min(1.0, penalty), 2)
    is_clean = slop_score == 0.0 and len(flagged) == 0 and em_dash_count == 0

    return SlopAuditReport(
        raw_text=text,
        cleaned_text=cleaned.strip(),
        em_dash_count=em_dash_count,
        semicolon_count=semi_count,
        flagged_terms=flagged,
        burstiness_score=burstiness,
        is_clean=is_clean,
        slop_score=slop_score
    )


def sanitize_bullet(bullet: str) -> str:
    """Sanitize a single resume bullet point to ensure zero AI hallmarks."""
    audit = audit_and_sanitize(bullet)
    res = audit.cleaned_text
    # Ensure it starts with a clean capital letter and no bullet prefix
    res = re.sub(r"^[-*•\s]+", "", res)
    if res:
        res = res[0].upper() + res[1:]
    return res
