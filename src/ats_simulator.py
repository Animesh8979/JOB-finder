"""Adversarial ATS Simulator & N-Gram Gap Analysis Engine.

Emulates the filtering and scoring mechanics of enterprise Applicant Tracking Systems
(Taleo, Greenhouse, Workday, Lever) to calculate calibrated survival probabilities,
extract missing N-Gram keywords, and detect hard knockout disqualifiers.
"""
from __future__ import annotations

import re
from typing import Any
from collections import Counter


_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can",
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him",
    "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't",
    "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
    "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some",
    "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to",
    "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's",
    "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've",
    "your", "yours", "yourself", "yourselves", "will", "shall", "work", "role", "team", "company", "candidate",
    "experience", "years", "year", "looking", "seeking", "ability", "responsibilities", "requirements", "skills"
}

# Technical single-token acronyms that should never be filtered
_PRESERVED_TECH_TOKENS = {
    "go", "c", "r", "ai", "ml", "ci", "cd", "qa", "ui", "ux", "db", "ip", "os", "k8s",
    "aws", "gcp", "sql", "api", "git", "etl", "sdk", "cli", "css", "vue", "npm", "dns"
}

# Strong executive action verbs
_STRONG_ACTION_VERBS = {
    "spearheaded", "orchestrated", "architected", "engineered", "pioneered", "scaled",
    "accelerated", "optimized", "developed", "deployed", "designed", "streamlined",
    "automated", "transformed", "championed", "delivered", "executed", "formulated",
    "integrated", "maximized", "minimized", "overhauled", "restructured", "reduced"
}

# Weak passive verbs that ATS systems downgrade
_WEAK_PASSIVE_VERBS = {
    "assisted", "helped", "worked on", "participated in", "contributed to",
    "supported", "handled", "was responsible for", "duties included", "attempted"
}

# Patterns for hard disqualifiers
_DISQUALIFIER_PATTERNS = [
    (re.compile(r"\b(?:active\s+security\s+clearance|ts/sci|secret\s+clearance|polygraph)\b", re.IGNORECASE),
     "Active Security Clearance Required"),
    (re.compile(r"\b(?:u\.?s\.?\s+citizen\s+only|us\s+citizenship\s+required|must\s+be\s+a\s+u\.?s\.?\s+citizen)\b", re.IGNORECASE),
     "US Citizenship Mandatory (No Visa Sponsorship)"),
    (re.compile(r"\b(?:ph\.?d\.?\s+(?:required|mandatory)|doctorate\s+(?:required|mandatory))\b", re.IGNORECASE),
     "PhD / Doctorate Degree Mandatory"),
    (re.compile(r"\b(?:1[2-9]|20)\+?\s+years(?:\s+of)?\s+experience\b", re.IGNORECASE),
     "Executive Seniority Filter (12+ Years Experience Demanded)"),
]


def _clean_text(text: str) -> str:
    """Normalize whitespace and strip HTML."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def _extract_ngrams(text: str) -> list[str]:
    """Extract filtered unigrams, bigrams, and technical phrases."""
    if not text:
        return []
    
    # Extract technical title-case phrases before lowercasing
    phrases = [
        p.lower() for p in re.findall(r"\b([A-Z][a-zA-Z+#.]+(?:\s[A-Z][a-zA-Z+#.]+){1,2})\b", text)
        if len(p) > 3
    ]
    
    text_lower = text.lower()
    raw_tokens = re.findall(r"[a-z0-9][a-z0-9+#./-]{0,30}", text_lower)
    tokens = [t.strip(".,;:!?\"'()") for t in raw_tokens if len(t.strip(".,;:!?\"'()")) > 0]
    valid_unigrams = [
        t for t in tokens
        if (t not in _STOPWORDS and len(t) > 2) or t in _PRESERVED_TECH_TOKENS
    ]
    
    # Bigrams
    bigrams = []
    for i in range(len(tokens) - 1):
        w1, w2 = tokens[i], tokens[i+1]
        if (w1 not in _STOPWORDS or w1 in _PRESERVED_TECH_TOKENS) and \
           (w2 not in _STOPWORDS or w2 in _PRESERVED_TECH_TOKENS):
            bigrams.append(f"{w1} {w2}")
            
    return valid_unigrams + bigrams + phrases


def simulate_adversarial_ats(
    job_description: str,
    resume_text: str
) -> dict[str, Any]:
    """Run an adversarial ATS emulation of candidate resume vs job description.
    
    Returns:
        survival_score (int): Calibrated 0-100% pass probability
        hard_disqualifiers (list[str]): Critical knockout rules detected
        matched_ngrams (list[str]): Successfully verified keywords
        missing_ngrams (list[str]): Critical keywords absent from resume
        action_verb_score (int): Assessment of impact verbs
        metric_quantifier_count (int): Count of quantified accomplishments
        recommendations (list[str]): Specific drop-in edits to maximize pass rate
    """
    if not job_description or not resume_text:
        return {
            "survival_score": 0,
            "hard_disqualifiers": [],
            "matched_ngrams": [],
            "missing_ngrams": [],
            "action_verb_score": 0,
            "metric_quantifier_count": 0,
            "recommendations": ["Provide both resume text and job description to run simulation."],
        }

    clean_jd = _clean_text(job_description)
    clean_resume = _clean_text(resume_text)

    # 1. Hard Disqualifier Check
    disqualifiers = []
    for pattern, label in _DISQUALIFIER_PATTERNS:
        if pattern.search(clean_jd) and not pattern.search(clean_resume):
            disqualifiers.append(label)

    # 2. N-Gram Extraction & Frequency Ranking
    jd_ngrams = _extract_ngrams(job_description)
    ngram_counts = Counter(jd_ngrams)
    
    # Take top 35 distinct terms sorted by relevance/frequency
    top_ngrams = [term for term, _ in ngram_counts.most_common(35)]
    
    matched = []
    missing = []
    for term in top_ngrams:
        # Check boundary match or substring for compound phrases
        if re.search(r"\b" + re.escape(term) + r"\b", clean_resume):
            matched.append(term)
        else:
            missing.append(term)

    # Keyword Coverage Score (0-100)
    keyword_coverage = int((len(matched) / max(len(top_ngrams), 1)) * 100)

    # 3. Action Verb & Impact Metric Quantification
    found_strong_verbs = [v for v in _STRONG_ACTION_VERBS if re.search(r"\b" + v + r"\b", clean_resume)]
    found_weak_verbs = [v for v in _WEAK_PASSIVE_VERBS if re.search(r"\b" + v + r"\b", clean_resume)]
    
    # Google XYZ Quantifier Metric Search ($100k, 45%, 10x, 50ms, etc.)
    metrics = re.findall(
        r'\b(?:\d+%\s*|\$\d+[\d,.]*[kmb]?|\d+x\b|\d+\s*(?:ms|seconds|qps|rps|users|nodes))\b',
        clean_resume,
        re.IGNORECASE
    )
    metric_count = len(metrics)

    # Compute Action Verb / Impact Score (0-100)
    verb_ratio = len(found_strong_verbs) / max(len(found_strong_verbs) + len(found_weak_verbs), 1)
    impact_score = min(100, int((verb_ratio * 50) + min(metric_count * 10, 50)))

    # 4. Calibrated ATS Survival Score
    # Baseline weighted sum
    survival = int((keyword_coverage * 0.55) + (impact_score * 0.30) + (15 if len(clean_resume) > 800 else 5))
    
    # Severe penalty if hard disqualifiers are triggered
    if disqualifiers:
        survival = max(10, survival - (len(disqualifiers) * 35))

    survival = max(0, min(100, survival))

    # 5. Strategic Recommendations
    recs = []
    if missing:
        top_missing = missing[:5]
        recs.append(f"Inject missing high-frequency ATS keywords: {', '.join(top_missing)}")
    if disqualifiers:
        recs.append(f"Warning: Position specifies hard knockouts ({'; '.join(disqualifiers)})")
    if metric_count < 3:
        recs.append("Quantify outcomes using Google XYZ formula (e.g. 'Improved latency by 35% across 10M requests').")
    if found_weak_verbs:
        recs.append(f"Replace passive phrasing ({', '.join(found_weak_verbs[:3])}) with high-agency engineering verbs.")

    return {
        "survival_score": survival,
        "keyword_coverage_pct": keyword_coverage,
        "hard_disqualifiers": disqualifiers,
        "matched_ngrams": matched,
        "missing_ngrams": missing,
        "action_verb_score": impact_score,
        "metric_quantifier_count": metric_count,
        "strong_verbs_found": found_strong_verbs,
        "weak_verbs_found": found_weak_verbs,
        "recommendations": recs,
    }
