"""Anti-AI-Slop & Humanizer Engine.

Eliminates AI hallmarks, em-dashes, robotic clichés, and sycophantic tropes
from generated resumes, cover letters, and outreach messages.
Ensures application materials sound like a sharp, authentic, grounded human builder.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple

__all__ = [
    "BANNED_AI_TERMS",
    "AI_SLOP_REPLACEMENTS",
    "SlopAuditReport",
    "sanitize_punctuation",
    "calculate_burstiness",
    "boost_cadence",
    "audit_and_sanitize",
    "sanitize_bullet",
]

# Explicit catalog of modern LLM hallmarks and banned cliché buzzwords
BANNED_AI_TERMS: List[str] = [
    "delve",
    "testament",
    "tapestry",
    "beacon",
    "harnessing",
    "pivotal",
    "fostered",
    "realm",
    "dynamic landscape",
    "spearheaded synergy",
    "leverage",
    "robust",
    "revolutionize",
    "plethora",
    "nestled",
    "unlock",
    "seamlessly",
    "furthermore",
    "moreover",
    "in summary",
    "in conclusion",
    "game-changer",
    "paradigm shift",
    "holistic approach",
    "cutting-edge",
    "state-of-the-art",
    "ever-evolving",
    "vital role",
    "crucial",
    "meticulous",
    "commendable",
    "unwavering",
    "transformative",
    "journey",
    "rich tapestry",
]

# Cliché AI buzzwords and phrases mapped to natural human alternatives
AI_SLOP_REPLACEMENTS: List[Tuple[str, str]] = [
    # Multi-word phrases and compound clichés (must come first)
    (r"\bspearheaded synergy\b", "led collaboration"),
    (r"\bspearheaded the development of\b", "built"),
    (r"\bspearheaded\b", "built"),
    (r"\bspearheading\b", "leading"),
    (r"\bspearhead\b", "lead"),
    
    (r"\bdelve into\b", "explore"),
    (r"\bdelving into\b", "exploring"),
    (r"\bdelves into\b", "explores"),
    (r"\bdelved into\b", "explored"),
    (r"\bdelve\b", "explore"),
    (r"\bdelving\b", "exploring"),
    (r"\bdelved\b", "explored"),

    (r"\brich tapestry of\b", "broad range of"),
    (r"\brich tapestry\b", "broad range"),
    (r"\btapestry of\b", "range of"),
    (r"\btapestry\b", "range"),

    (r"\ba testament to\b", "proof of"),
    (r"\btestament to\b", "evidence of"),
    (r"\btestament\b", "evidence"),

    (r"\bbeacon of\b", "model for"),
    (r"\bbeacon\b", "leader"),

    (r"\bharnessing the power of\b", "using"),
    (r"\bharnessing\b", "using"),
    (r"\bharnessed\b", "used"),
    (r"\bharness\b", "use"),

    (r"\bpivotal role in\b", "key role in"),
    (r"\bpivotal role\b", "key role"),
    (r"\bpivotal\b", "key"),

    (r"\bfostered synergy\b", "built collaboration"),
    (r"\bfostering\b", "building"),
    (r"\bfostered\b", "built"),
    (r"\bfoster\b", "encourage"),

    (r"\bin the ever-evolving realm of\b", "in"),
    (r"\bin the realm of\b", "in"),
    (r"\brealm of\b", "field of"),
    (r"\brealm\b", "field"),

    (r"\bin today's dynamic landscape\b", "today"),
    (r"\bdynamic landscape\b", "market"),
    (r"\bdynamic and fast-paced\b", "fast-moving"),
    (r"\bin today's dynamic\b", "in today's"),
    (r"\bin today's fast-paced world\b", "today"),

    (r"\bleveraging\b", "using"),
    (r"\bleveraged\b", "used"),
    (r"\bleverage\b", "use"),

    (r"\brobust and scalable\b", "reliable"),
    (r"\brobust\b", "reliable"),

    (r"\brevolutionizing\b", "modernizing"),
    (r"\brevolutionized\b", "overhauled"),
    (r"\brevolutionize\b", "improve"),

    (r"\bplethora of\b", "wide range of"),
    (r"\bplethora\b", "many"),

    (r"\bnestled in\b", "located in"),
    (r"\bnestled\b", "based in"),

    (r"\bunlock the potential of\b", "enable"),
    (r"\bunlocking\b", "enabling"),
    (r"\bunlocked\b", "enabled"),
    (r"\bunlock\b", "enable"),

    (r"\bseamlessly integrated\b", "integrated"),
    (r"\bseamlessly\b", "smoothly"),
    (r"\bseamless\b", "smooth"),

    (r"\bgame-changer\b", "major advantage"),
    (r"\bgame changer\b", "major advantage"),
    (r"\bgame-changing\b", "significant"),
    (r"\bgame changing\b", "significant"),

    (r"\bparadigm shift\b", "fundamental shift"),

    (r"\bholistic approach\b", "thorough approach"),
    (r"\bholistically\b", "thoroughly"),
    (r"\bholistic\b", "comprehensive"),

    (r"\bcutting-edge\b", "modern"),
    (r"\bcutting edge\b", "modern"),

    (r"\bstate-of-the-art\b", "modern"),
    (r"\bstate of the art\b", "modern"),

    (r"\bever-evolving\b", "evolving"),
    (r"\bever evolving\b", "evolving"),

    (r"\bplayed a vital role in\b", "helped"),
    (r"\bvital role\b", "key role"),

    (r"\bcrucial role\b", "key role"),
    (r"\bcrucial\b", "essential"),

    (r"\bmeticulous attention to detail\b", "careful execution"),
    (r"\bmeticulously\b", "carefully"),
    (r"\bmeticulous\b", "thorough"),

    (r"\bcommendable\b", "notable"),

    (r"\bunwavering commitment\b", "commitment"),
    (r"\bunwavering dedication\b", "dedication"),
    (r"\bunwavering\b", "steady"),

    (r"\btransformative impact\b", "major impact"),
    (r"\btransformative\b", "high-impact"),

    (r"\bprofessional journey\b", "career"),
    (r"\bcareer journey\b", "career"),
    (r"\bmy journey\b", "my experience"),
    (r"\bjourney\b", "experience"),

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
    (r"\bdeep dive\b", "detailed analysis"),

    # Robotic transitional deadwood
    (r"\bFurthermore\b,?\s*", "Also, "),
    (r"\bMoreover\b,?\s*", "In addition, "),
    (r"\bIn conclusion\b,?\s*", ""),
    (r"\bTo summarize\b,?\s*", ""),
    (r"\bIn summary\b,?\s*", ""),
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


def _replace_preserve_case(pattern: str, replacement: str, text: str) -> str:
    """Replace pattern in text while preserving leading capitalization."""
    def repl_func(match: re.Match) -> str:
        matched_str = match.group(0)
        if not replacement:
            return ""
        if matched_str and matched_str[0].isupper():
            return replacement[0].upper() + replacement[1:]
        return replacement[0].lower() + replacement[1:]

    return re.sub(pattern, repl_func, text, flags=re.IGNORECASE)


def sanitize_punctuation(text: str) -> Tuple[str, int, int]:
    """Eliminates em-dashes, en-dashes, parenthetical double-hyphens, curly quotes, and ellipsis.
    
    Replaces them with crisp natural punctuation (commas, periods, colons, or straight quotes).
    Returns (cleaned_text, em_dash_count, semicolon_count).
    """
    if not text:
        return "", 0, 0

    # Count em-dashes and parenthetical double hyphens
    em_dash_count = len(re.findall(r"[—\u2014]", text)) + len(re.findall(r"(?:\s+--\s+|\b--\b)", text))
    semicolon_count = len(re.findall(r";", text))

    cleaned = text

    # 1. Curly single and double quotes to straight quotes
    cleaned = re.sub(r"[“”\u201c\u201d]", '"', cleaned)
    cleaned = re.sub(r"[‘’\u2018\u2019]", "'", cleaned)

    # 2. Ellipsis to crisp period or comma
    # Trailing ellipsis at end of sentence or line -> period
    cleaned = re.sub(r"\s*(?:…|\u2026|\.{3,})\s*(?=$|[.!?\n])", ".", cleaned)
    # Ellipsis used as internal pause -> comma
    cleaned = re.sub(r"\s*(?:…|\u2026|\.{3,})\s*", ", ", cleaned)

    # 3. Em-dashes and parenthetical double-hyphens to natural commas
    # Example: "Python — specifically FastAPI — for backend" -> "Python, specifically FastAPI, for backend"
    # Example: "Led the team — achieving 20% gain" -> "Led the team, achieving 20% gain"
    cleaned = re.sub(r"\s*[—\u2014]\s*", ", ", cleaned)
    cleaned = re.sub(r"\s+--\s+", ", ", cleaned)
    cleaned = re.sub(r"\b--\b", ", ", cleaned)

    # 4. En-dashes: numeric ranges become plain hyphen (2023 - 2026), word ranges become comma or hyphen
    cleaned = re.sub(r"(\d+)\s*[–\u2013]\s*(\d+)", r"\1 - \2", cleaned)
    cleaned = re.sub(r"\s+[–\u2013]\s+", " - ", cleaned)
    cleaned = re.sub(r"[–\u2013]", ", ", cleaned)

    # 5. Semicolons: replace with period or comma
    cleaned = re.sub(r";\s*(However|Therefore|Furthermore|Moreover|In addition)", r". \1", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r";\s*", ", ", cleaned)

    # 6. Polish punctuation anomalies (double commas, comma-period, double spaces)
    cleaned = re.sub(r",\s*,+", ", ", cleaned)
    cleaned = re.sub(r",\s*\.", ".", cleaned)
    cleaned = re.sub(r"\.\s*,", ".", cleaned)
    cleaned = re.sub(r":\s*,", ": ", cleaned)
    cleaned = re.sub(r",\s*:", ": ", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n\s{2,}", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

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


def boost_cadence(text: str) -> str:
    """Enhance sentence rhythm to eliminate monotonic robotic cadences.
    
    If burstiness is below 0.20, introduces natural sentence length variance
    by splitting compound clauses or connecting adjacent short clauses.
    """
    if not text or calculate_burstiness(text) >= 0.20:
        return text

    sentence_tokens = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if len(sentence_tokens) < 2:
        return text

    # Strategy 1: If any sentence has an internal comma clause, split it into two sentences
    new_sentences = []
    split_done = False
    for s in sentence_tokens:
        if not split_done and "," in s:
            parts = s.split(",", 1)
            left = parts[0].strip()
            right = parts[1].strip()
            if len(left.split()) >= 3 and len(right.split()) >= 3:
                left = left.rstrip(".!?")
                right_cap = right[0].upper() + right[1:] if right else ""
                new_sentences.append(left + ".")
                new_sentences.append(right_cap)
                split_done = True
                continue
        new_sentences.append(s)

    candidate = " ".join(new_sentences)
    if calculate_burstiness(candidate) >= 0.20:
        return candidate

    # Strategy 2: Merge first two sentences with ", and "
    if len(sentence_tokens) >= 2:
        first = sentence_tokens[0].rstrip(".!?")
        second = sentence_tokens[1]
        second_conn = second if second.startswith("I ") else (second[0].lower() + second[1:] if second else "")
        merged = f"{first}, and {second_conn}"
        candidate_list = [merged] + sentence_tokens[2:]
        candidate = " ".join(candidate_list)
        if calculate_burstiness(candidate) >= 0.20:
            return candidate

    return candidate


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

    # Step 2: Track flagged terms against BANNED_AI_TERMS and AI_SLOP_REPLACEMENTS
    flagged: List[str] = []
    
    # Check explicit BANNED_AI_TERMS first against raw text
    for term in BANNED_AI_TERMS:
        term_escaped = re.escape(term).replace(r"\-", r"[- ]")
        pattern = rf"\b{term_escaped}\b"
        if re.search(pattern, text, flags=re.IGNORECASE):
            if term not in flagged:
                flagged.append(term)

    # Apply replacements and track matches
    for pattern, replacement in AI_SLOP_REPLACEMENTS:
        matches = re.findall(pattern, cleaned, flags=re.IGNORECASE)
        if matches:
            for m in set(matches):
                m_str = str(m).strip()
                if m_str and m_str.lower() not in [f.lower() for f in flagged]:
                    flagged.append(m_str)
            cleaned = _replace_preserve_case(pattern, replacement, cleaned)

    # Step 3: Polish grammar and formatting artifacts
    cleaned = re.sub(r"\b([Aa])\s+([aeiouAEIOU])", r"\1n \2", cleaned)
    cleaned = re.sub(r"\b([Aa])n\s+([bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ])", r"\1 \2", cleaned)
    cleaned = re.sub(r",\s*,+", ", ", cleaned)
    cleaned = re.sub(r",\s*\.", ".", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)

    # Step 4: Cadence enhancement (boost burstiness if monotonic)
    cleaned = boost_cadence(cleaned.strip())
    burstiness = calculate_burstiness(cleaned)
    
    penalty = 0.0
    penalty += em_dash_count * 0.25
    penalty += len(flagged) * 0.15
    penalty += semi_count * 0.05
    if burstiness < 0.20:
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
    if not bullet:
        return ""
    audit = audit_and_sanitize(bullet)
    res = audit.cleaned_text
    # Ensure it starts with a clean capital letter and no bullet prefix
    res = re.sub(r"^[-*•\s]+", "", res)
    # Strip any trailing comma or colon resulting from edge replacements
    res = re.sub(r"[,;:\s]+$", "", res)
    if res:
        res = res[0].upper() + res[1:]
    return res
