"""Value-add intelligence that sets this tool apart:

- prescore()                 local relevance rank (no AI) → score the best jobs first, cap cost
- ats_coverage()             local ATS keyword check of a resume against a job (no AI)
- flag_possible_fabrication() local guard that catches invented skills (no AI)
- analyze_fit()              on-demand AI "should I apply?" with matched/missing skills

The local functions are fast and free; only analyze_fit calls the AI.
"""
from __future__ import annotations

import re
from typing import Any

from . import llm
from .profile_parser import profile_context

# --- tokenization helpers ----------------------------------------------------
_STOP = set(
    "a an the and or for to of in on with at by from as is are be was were been being this "
    "that these those you your we our us they their it its will would can could should may "
    "might must have has had do does did not no yes if then else than so such into over under "
    "about across after before between during without within job jobs role roles team teams "
    "work working experience years year you'll we're who what when where which while able strong "
    "plus etc per via using use used able ability join looking seeking ideal candidate company "
    "remote position opportunity responsibilities requirements qualifications skills benefits".split()
)
# Short tokens that ARE real skills (so we don't drop them by length).
_KEEP_SHORT = {"go", "ml", "ai", "qa", "ci", "cd", "aws", "gcp", "sql", "etl", "api", "ux",
               "ui", "r", "c", "c#", "c++", "js", "ts", "db", "bi"}

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+#./-]{0,30}")
_PHRASE_RE = re.compile(r"\b([A-Z][a-zA-Z+#.]+(?:\s[A-Z][a-zA-Z+#.]+){1,2})\b")


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


# --- local relevance pre-rank ------------------------------------------------
def prescore(job: dict[str, Any], profile: dict[str, Any], prefs: dict[str, Any]) -> float:
    """Cheap 0..1 relevance estimate used to order jobs before paid AI scoring."""
    skills = {_norm(s) for s in (profile or {}).get("skills", []) if s}
    skills |= {_norm(k) for k in (prefs.get("keywords") or []) if k}
    titles = [_norm(t) for t in (prefs.get("titles") or []) + ((profile or {}).get("target_titles") or []) if t]

    title = _norm(job.get("title", ""))
    body = _norm(f"{job.get('title','')} {' '.join(job.get('tags') or [])} {job.get('description','')}")

    skill_hits = sum(1 for s in skills if s and s in body)
    skill_score = skill_hits / max(len(skills), 1)
    title_score = 1.0 if any(t and t in title for t in titles) else (
        0.5 if any(t and any(w in title for w in t.split()) for t in titles) else 0.0
    )
    return round(0.6 * skill_score + 0.4 * title_score, 4)


# --- ATS keyword coverage ----------------------------------------------------
def ats_coverage(resume_text: str, job_description: str, top_n: int = 22) -> dict[str, Any]:
    """How many of the job's key terms appear in the resume (ATS-style check)."""
    jd = job_description or ""
    counts: dict[str, int] = {}
    for tok in _tokens(jd):
        if tok in _STOP:
            continue
        if (len(tok) <= 2 and tok not in _KEEP_SHORT) or tok.isdigit():
            continue
        counts[tok] = counts.get(tok, 0) + 1
    # Multi-word Title-Case phrases (e.g. "Machine Learning").
    for ph in _PHRASE_RE.findall(jd):
        p = _norm(ph)
        if len(p) > 4:
            counts[p] = counts.get(p, 0) + 2

    ranked = sorted(counts, key=lambda k: (counts[k], len(k)), reverse=True)[:top_n]
    resume_l = _norm(resume_text)
    present = [k for k in ranked if k in resume_l]
    missing = [k for k in ranked if k not in resume_l]
    coverage = round(100 * len(present) / max(len(ranked), 1))
    return {"coverage": coverage, "present": present, "missing": missing}


def check_resume_ats(resume_text: str, job_description: str, profile: dict[str, Any], prefs: dict[str, Any]) -> dict[str, Any]:
    """Perform a deep ATS compatibility analysis on a resume against a job description."""
    if not resume_text or not job_description:
        return {}
        
    text_lower = resume_text.lower()
    headers_map = {
        "work_experience": ["work experience", "professional experience", "experience", "employment history", "work history"],
        "education": ["education", "academic background", "credentials"],
        "skills": ["skills", "technical skills", "areas of expertise", "core competencies"],
        "projects": ["projects", "personal projects", "portfolio"],
        "summary": ["summary", "professional summary", "about me", "objective"]
    }
    
    sections_found = []
    sections_missing = []
    for section, keywords in headers_map.items():
        if any(kw in text_lower for kw in keywords):
            sections_found.append(section.replace("_", " ").title())
        else:
            sections_missing.append(section.replace("_", " ").title())
            
    metrics_regex = re.compile(
        r'\b(?:\d+%|\$\d+(?:\.\d+)?(?:\s*[kmbt](?:illion)?)?|\d+\s*(?:%|percent|users|customers|servers|jobs|developers|contributors|hours|days|weeks|months|years))\b',
        re.IGNORECASE
    )
    metric_matches = metrics_regex.findall(resume_text)
    metrics_count = len(metric_matches)
    
    action_verbs = {
        "led", "managed", "developed", "built", "implemented", "designed", "created", "optimized",
        "engineered", "architected", "executed", "accelerated", "accomplished", "achieved", "analyzed",
        "coordinated", "delivered", "directed", "established", "expanded", "formulated", "improved",
        "increased", "launched", "maximized", "minimized", "pioneered", "reduced", "spearheaded", "transformed"
    }
    resume_words = set(re.findall(r'\b[a-zA-Z]+\b', text_lower))
    verbs_found = [v for v in action_verbs if v in resume_words]
    verbs_count = len(verbs_found)
    
    coverage_info = ats_coverage(resume_text, job_description)
    
    readability_score = 100 - (len(sections_missing) * 15)
    word_count = len(resume_text.split())
    if word_count < 250 or word_count > 1500:
        readability_score -= 15
    readability_score = max(50, min(100, readability_score))
    
    impact_score = min(100, (metrics_count * 15) + (len(verbs_found) * 5))
    impact_score = max(40, impact_score)
    
    data = {}
    if llm.config.provider_ready():
        prompt = (
            "You are an advanced Applicant Tracking System (ATS) evaluator (like Greenhouse/Lever).\n"
            "Compare the candidate's resume text against the job description below for semantic alignment and role suitability.\n\n"
            f"CANDIDATE RESUME TEXT:\n\"\"\"\n{resume_text[:4000]}\n\"\"\"\n\n"
            f"JOB DESCRIPTION:\n\"\"\"\n{job_description[:4000]}\n\"\"\"\n\n"
            "Return JSON with ONLY these exact fields:\n"
            "{\n"
            '  "alignment_score": int (1-100, how well their background matches the role expectations),\n'
            '  "explanation": "2-3 sentences explaining the fit and gaps",\n'
            '  "missing_keywords_semantic": ["term1", "term2"] (important technologies or skills the job wants but are missing from resume),\n'
            '  "actionable_suggestions": ["tip1", "tip2"] (specific suggestions to optimize the resume formatting or content for this role)\n'
            "}"
        )
        try:
            data = llm.generate_json(
                prompt,
                system="You are an unbiased, expert ATS resume screening algorithm.",
                model=prefs.get("writing_model"),
                max_tokens=600
            )
        except Exception:
            pass
            
    if not isinstance(data, dict):
        data = {}
        
    alignment_score = data.get("alignment_score", 70)
    explanation = data.get("explanation", "ATS scanner completed heuristics check.")
    missing_semantic = data.get("missing_keywords_semantic") or coverage_info.get("missing")[:5]
    actionable_suggestions = data.get("actionable_suggestions") or [
        "Include more metrics and quantified results to show business impact.",
        "Add missing skills to your skills section if you possess them.",
        "Ensure all major section headings are clear and standard."
    ]
    
    ats_score = round(
        0.40 * coverage_info.get("coverage", 60) +
        0.30 * alignment_score +
        0.15 * readability_score +
        0.15 * impact_score
    )
    
    return {
        "ats_score": max(20, min(100, ats_score)),
        "readability": {
            "sections_found": sections_found,
            "sections_missing": sections_missing,
            "word_count": word_count,
            "score": readability_score
        },
        "impact": {
            "quantified_metrics_count": metrics_count,
            "metric_examples": metric_matches[:5],
            "action_verbs_count": verbs_count,
            "verbs_found": sorted(verbs_found),
            "score": impact_score
        },
        "keywords": {
            "coverage_percent": coverage_info.get("coverage", 0),
            "matched": coverage_info.get("present", []),
            "missing": coverage_info.get("missing", [])
        },
        "semantic_match": {
            "alignment_score": alignment_score,
            "explanation": explanation,
            "missing_semantic": missing_semantic,
            "suggestions": actionable_suggestions
        }
    }


# --- anti-fabrication guard --------------------------------------------------
def flag_possible_fabrication(resume: dict[str, Any], profile: dict[str, Any]) -> list[str]:
    """Return tailored skills that don't trace back to the original resume text.

    Enforces the 'never invent' promise with code, not just a prompt. Flagged items are
    surfaced so the user can remove anything that crept in.
    """
    source = _norm(
        (profile or {}).get("raw_text", "")
        + " " + " ".join(map(str, (profile or {}).get("skills", [])))
        + " " + " ".join(
            " ".join(str(b) for b in (e.get("bullets") or []))
            for e in (profile or {}).get("experience", [])
        )
    )
    if not source:
        return []

    flagged: list[str] = []
    for skill in resume.get("skills", []) or []:
        s = _norm(skill)
        if not s:
            continue
        if s in source:
            continue
        # multi-word skill counts as present if all significant words appear
        words = [w for w in re.split(r"[\s/]+", s) if len(w) > 2]
        if words and all(w in source for w in words):
            continue
        flagged.append(str(skill))
    return flagged


# --- AI fit analysis (on-demand) ---------------------------------------------
def analyze_fit(job: dict[str, Any], profile: dict[str, Any], prefs: dict[str, Any]) -> dict[str, Any]:
    prompt = (
        "Assess how well the candidate fits this job and advise honestly.\n\n"
        f"JOB TITLE: {job.get('title','')}\nCOMPANY: {job.get('company','')}\n"
        f"JOB DESCRIPTION:\n\"\"\"\n{(job.get('description') or '')[:3500]}\n\"\"\"\n\n"
        "Return JSON: {\n"
        '  "score": int 1-10,\n'
        '  "verdict": str (1-2 sentences: should they apply, and why),\n'
        '  "matched_skills": [str] (candidate strengths this role wants),\n'
        '  "missing_skills": [str] (gaps the candidate likely lacks),\n'
        '  "emphasize": [str] (what to highlight in resume/cover letter)\n'
        "}"
    )
    data = llm.generate_json(
        prompt,
        system="You are a candid, experienced technical recruiter. Be realistic, not flattering.",
        cached_context=profile_context(profile),
        model=prefs.get("writing_model"),
        max_tokens=700,
    )
    return data if isinstance(data, dict) else {}

# --- red flag detector -------------------------------------------------------

RED_FLAGS = {
    "toxic_culture": ["fast-paced environment", "wear many hats", "like a family", "work hard play hard",
                      "self-starter", "hit the ground running", "rockstar", "ninja", "guru", "unicorn",
                      "high-pressure", "no hand-holding"],
    "scope_creep": ["other duties as assigned", "willing to do whatever it takes", "flexible with responsibilities"],
    "bad_compensation": ["competitive salary", "salary commensurate", "unpaid", "equity only", "volunteer"],
    "high_turnover": ["immediately", "urgent hire", "asap", "right away", "due to growth"],
    "unrealistic": ["must have 10+ years", "entry level.*5 years", "junior.*senior"],
}

def detect_red_flags(description: str) -> dict[str, list[str]]:
    """Scan job description for toxic signals and return matched phrases by category."""
    desc_lower = (description or "").lower()
    found = {}
    for category, flags in RED_FLAGS.items():
        matches = [flag for flag in flags if re.search(r'\b' + flag + r'\b', desc_lower)]
        if matches:
            found[category] = matches
    return found

# --- company dossier & interview prep ----------------------------------------

def generate_company_dossier(company: str, job_title: str, job_desc: str, prefs: dict, match_score: int = 0) -> dict:
    """Use AI to generate a brief dossier on the company culture and tech stack.
    Only deep-researches if the match score is high enough (e.g. > 85), saving tokens.
    """
    if not company:
        return {}
        
    from . import config
    import json
    cache_path = config.DATA_DIR / "company_intel.json"
    cache = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text())
        except Exception:
            pass
            
    if company in cache:
        return cache[company]
        
    if match_score < 85:
        # Don't burn tokens on low-match jobs
        return {"overview": "Match score too low for deep GPT Research.", "likely_tech_stack": [], "culture_signals": "", "why_join_angles": []}
        
    # Here is where the GPT-Researcher MCP call would occur.
    # We fallback to standard LLM generation if the MCP server is not hooked up.
    prompt = (
        f"Create a deep research dossier for {company} focusing on engineering culture and stack, based on this JD for {job_title}:\n"
        f"\"\"\"\n{(job_desc or '')[:3500]}\n\"\"\"\n\n"
        "Return JSON:\n"
        "{\n"
        '  "overview": "Brief 2-3 sentence overview of what the company does",\n'
        '  "likely_tech_stack": ["React", "Python", "AWS", "..."],\n'
        '  "culture_signals": "What the JD suggests about their engineering culture",\n'
        '  "why_join_angles": ["Angle 1", "Angle 2"]\n'
        "}"
    )
    data = llm.generate_json(
        prompt,
        system="You are an expert tech career advisor researching a company. Be analytical and critical.",
        model=prefs.get("writing_model"),
        max_tokens=600,
    )
    if isinstance(data, dict) and data:
        cache[company] = data
        cache_path.write_text(json.dumps(cache, indent=2))
        return data
    return {}

def generate_interview_prep(job: dict, profile: dict, prefs: dict) -> dict:
    """Generate mock interview questions and suggested answers."""
    prompt = (
        f"Generate interview prep for the {job.get('title','')} role at {job.get('company','')}.\n"
        f"Job Description snippet: {(job.get('description') or '')[:2000]}\n\n"
        "Return JSON:\n"
        "{\n"
        '  "behavioral_questions": [{"question": "...", "sample_answer_bullet_points": ["..."]}],\n'
        '  "technical_questions": [{"question": "...", "key_talking_points": ["..."]}],\n'
        '  "questions_to_ask_them": ["Smart question 1", "Smart question 2"]\n'
        "}"
    )
    data = llm.generate_json(
        prompt,
        system="You are an expert tech interviewer and career coach.",
        cached_context=profile_context(profile),
        model=prefs.get("writing_model"),
        max_tokens=1500,
    )
    return data if isinstance(data, dict) else {}

# --- salary intelligence -----------------------------------------------------

def estimate_salary(job: dict, profile: dict, prefs: dict) -> dict:
    """Estimate salary ranges based on the job title, location, and seniority."""
    prompt = (
        f"Estimate the realistic base salary range for this role.\n"
        f"Title: {job.get('title', '')}\n"
        f"Location: {job.get('location', 'Remote')}\n"
        f"Company: {job.get('company', '')}\n"
        f"Candidate Experience: {profile.get('years_experience', 0)} years\n\n"
        "Return JSON:\n"
        "{\n"
        '  "low_range": int (e.g. 120000),\n'
        '  "median": int,\n'
        '  "high_range": int,\n'
        '  "currency": "USD" or "EUR" etc,\n'
        '  "confidence_note": "Why you estimate this",\n'
        '  "negotiation_tip": "Specific negotiation advice for this role"\n'
        "}"
    )
    data = llm.generate_json(
        prompt,
        system="You are an expert tech compensation analyst.",
        model=prefs.get("writing_model"),
        max_tokens=400,
    )
    return data if isinstance(data, dict) else {}

# --- smart follow-ups --------------------------------------------------------

def generate_followup_email(job: dict, profile: dict, prefs: dict, followup_number: int, days_since_apply: int) -> tuple[str, str]:
    """Draft a follow-up email based on the sequence."""
    prompt = (
        f"Draft follow-up email #{followup_number} for the {job.get('title','')} role at {job.get('company','')}.\n"
        f"It has been {days_since_apply} days since applying.\n"
        "Return JSON: {\"subject\": \"...\", \"body\": \"...\"}\n"
        "Keep the body short, professional, and zero-fluff. Never invent names."
    )
    data = llm.generate_json(
        prompt,
        system="You are an expert executive assistant drafting email.",
        cached_context=profile_context(profile),
        model=prefs.get("writing_model"),
        max_tokens=400,
    )
    if isinstance(data, dict):
        return data.get("subject", ""), data.get("body", "")
    return "", ""
