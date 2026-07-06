---
name: recruiter-scorecard
description: "Rule-based resume advisor inspired by interviewstreet/hiring-agent. Deterministic scoring of parsed resumes against the hiring-agent taxonomy (open_source / self_projects / production / technical_skills + capped bonus/deduction), explainable per-rule rationale, zero LLM cost."
---

# Recruiter Scorecard Skill

You are connected to the `Ai job finder` project. Use this skill when asked to evaluate, score, or critique a parsed candidate resume locally without invoking an LLM.

## When to use

- User asks "how does my resume look?" or "score my resume"
- The `RecruiterScoreCard` React component wants data via `/api/recruiter_score`
- A test wants deterministic rule-based scoring output

## Code surfaces (`[VERIFIED]` by file read)

- `src/recruiter_score.py` — pure function `score(raw_text, *, github_handle, skills) -> ScoreReport`.
- `server.py` — `GET /api/recruiter_score` reads the saved profile, calls `score()`, returns the dict.
- `frontend/src/components/RecruiterScoreCard.tsx` — renders rationale as animated cards.

## Taxonomy (mirrors interviewstreet/hiring-agent README)

| category          | signal                                                                                              |
|-------------------|-----------------------------------------------------------------------------------------------------|
| open_source       | GitHub handle present (regex `github\.com/<handle>`), dedicated Open Source / Contributions section |
| self_projects     | Projects section present; quantified outcome density (%, x/$/MAU/DAU/QPS bullets)                    |
| production        | Production-verb density (built/led/shipped/deployed/scaled/owned/etc.)                              |
| technical_skills  | Skills section + extracted skill count                                                              |

Hard caps:
- `MAX_FINAL_SCORE = 120`, `MIN_FINAL_SCORE = -20`
- `MAX_BONUS_POINTS = 20`, `MAX_DEDUCTION_POINTS = 20`

## Attribution contract

This is a STRUCTURAL PEER, NOT a port. Always say "inspired by" HackerRank's open-source hiring-agent taxonomy. Never claim the scoring engine itself is by HackerRank — only the *rubric taxonomy* is mirrored. The scoring rules are project-specific Python regex heuristics.

## Adding a new rule

1. Add to `src/recruiter_score.py` `score()`.
2. Append a rationale entry: `{"category", "rule", "delta", "note"}`.
3. Add a test to `tests/test_recruiter_score.py` following the matrix pattern.
4. Run: `python -m pytest tests/test_recruiter_score.py -v`.

## Forbidden

- Calling an LLM inside `score()`. This skill is deterministic and zero-cost by design.
- Claiming direct descent from HackerRank code. Inspirer string in `ScoreReport.inspirer` is the authoritative attribution.
- Scraping `mcpmarket.com` or any third-party registry from inside the scorer.
