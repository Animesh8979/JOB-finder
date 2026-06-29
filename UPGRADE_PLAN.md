# AI Job Finder — FINAL Upgrade Plan

> Third review. Deeper audit. No sugar-coating.

---

## 0. BUGS FOUND (across all 3 audit passes)

### Crash Bugs (app throws exceptions)

| # | File:Line | Bug | Will this actually crash? |
|---|-----------|-----|--------------------------|
| 1 | `greenhouse.py:35` | `base.normalize({...}, source="greenhouse")` — positional dict to keyword-only function | **YES** — TypeError on any greenhouse fetch |
| 2 | `lever.py:33` | Same `normalize()` signature mismatch | **YES** — TypeError on any lever fetch |
| 3 | `hackernews.py:60` | Same `normalize()` signature mismatch | **YES** — TypeError on HN fetch |
| 4 | `server.py:420` | `json.dumps(profile)` — no `import json` | **YES** — NameError when user runs ATS check |
| 5 | `auto_miner.py:5,11` | `sqlite3.connect()` — DB is PostgreSQL | **YES** — OperationalError on start |
| 6 | `scraper.py:97` | `from stealth_sync import stealth_sync` — no such module | **YES** — ImportError on Playwright scrape |

### Silent Bugs (no crash, but broken behavior)

| # | File:Line | Bug | Impact |
|---|-----------|-----|--------|
| 7 | `cron_daemon.py` | Stub — `scrape_job_boards()` logs a message, then sleeps. Calls nothing. | Zero background mining |
| 8 | `requirements.txt` | Missing `numpy`, `scikit-learn`, `beautifulsoup4`, `feedparser` | Import errors at runtime for those code paths |
| 9 | `db.py:285` | `f"UPDATE applications SET {sets}"` — f-string SQL with unsanitized field names from `**fields` | SQL injection if caller passes malicious field names (currently safe because callers are internal, but fragile) |
| 10 | `db.py:38-60` | `autocommit=True` on all pooled connections. No transaction wrapping. If a cursor error leaves partial state, there's no rollback. | Partial writes on multi-statement operations |
| 11 | `client.py:24` | `httpx.get()` — single attempt with no retry. Network transient → silent empty return (not even an exception, just an empty list in `aggregate.py`) | Jobs silently not fetched |
| 12 | `aggregate.py:45` | `mod.fetch(query, per_source_limit, prefs)` — if fetch returns `None` (not a list), `extend()` throws TypeError which is caught, but if it returns partial data as `None`, jobs lost | Edge case job loss |
| 13 | `.gitignore` | `data/.fernet_key` NOT in gitignore — the encryption key could be committed | All secrets decryptable if .fernet_key leaks |
| 14 | `server.py:26-39` | `RateLimiter` defaultdict never pruned. Over weeks of uptime, history grows unbounded (one entry per request per IP). 60-second window means only last 60s are checked, but the list only grows. | Slow memory leak (~1KB/IP/day). Not critical for single-user, bad for multi-user |
| 15 | `matcher.py` | SentenceTransformer loaded synchronously on first API call. Blocks the event loop for 5-10s. During that time, ALL FastAPI requests queue. | First `/api/jobs/score-all` freezes the entire server |
| 16 | `llm.py:50-52` | `cache_control` on Claude system blocks — this requires the `cache_control` beta header on API calls. `anthropic.Anthropic()` doesn't enable it by default. | Cache never actually works — you pay full token cost every call |
| 17 | `scraper.py:108` | Hardcoded Chrome/120 User-Agent. Chrome 120 is from December 2023. | Easy bot detection fingerprint |
| 18 | `scraper.py:76` | `verify=False` on httpx SSL — disables certificate verification | MITM vulnerability |

### Codebase Structural Issues

| # | Issue | Where |
|---|-------|-------|
| 19 | Zero tests | Entire project |
| 20 | `any` types everywhere | All 7 frontend pages |
| 21 | No shared API client | 7 pages duplicate `fetch()` with different error handling |
| 22 | 1 DB index | Only `idx_jobs_score` exists |
| 23 | No CI/CD | No GitHub Actions, no pre-commit hooks |
| 24 | No health check | Docker can't monitor the app |
| 25 | `alert()` for confirmations | Tracker.tsx |
| 26 | Redundant polling | Dashboard + App both poll `/api/status` |
| 27 | `requests` library imported but `httpx` already available | auto_miner.py |
| 28 | `client.py` has a User-Agent that literally says "personal job search tool" — not stealth, just politely announcing it's a bot | All source API calls |

---

## 1. SEVERITY CLASSIFICATION

```
CRITICAL (crashes app):     #1-6
HIGH (silent data loss):    #9-12, #15, #16
MEDIUM (easy fix, big win): #7-8, #13, #14, #17, #18, #28
LOW (nice to have):         #19-27
```

---

## 2. WHAT MATTERS AND WHAT DOESN'T

### What ACTUALLY matters to a job seeker:

1. **Finding jobs** → 14 sources work, but 3 crash. Fix the crashes.
2. **Scoring jobs** → Works, but first request freezes for 10s. Fix the blocking load.
3. **Tailoring resumes** → Works. Fabrication shield is genuinely good.
4. **Applying** → Pre-fill works but is fragile. Answer sheet concept is strong.
5. **Tracking** → Works. Kanban board exists.

### What does NOT matter:

- Resume editor with drag-and-drop (the existing `documents.py` + `tailor.py` already generate tailored resumes)
- 3D floating particles (a job seeker wants a job, not a video game)
- Telegram notifications (99% of users won't set up a Telegram bot)
- Multi-profile support (most users have ONE resume, not five)
- Semantic search (keyword search + AI scoring already does this better)
- Keyboard shortcuts (power user feature, not v1)

---

## 3. THE ACTUAL PLAN (what we should build)

**Principle**: Fix what's broken. Don't add features until the foundation is solid and tested.

### Phase 0: Make It Run (½ day)

```
1. Fix normalize() in greenhouse.py, lever.py, hackernews.py
2. Add `import json` to server.py
3. Fix stealth_sync import in scraper.py
4. Replace sqlite3 with PostgreSQL in auto_miner.py
5. Wire cron_daemon.py to actually call auto_miner.start_mining()
6. Add missing deps to requirements.txt
7. Add .fernet_key to .gitignore
8. Add `GET /api/jobs/{id}` endpoint (needed by Apply.tsx)
9. Add `GET /api/health` endpoint
10. Fix duplicate BarChart2 icon in App.tsx
11. Add 3 DB indexes (dedupe_key UNIQUE, company, title)
12. Fix scraper.py SSL verify=False (set to True, it's local-only anyway)
13. Fix scraper.py User-Agent to current Chrome
14. Fix client.py User-Agent to a realistic browser UA
```

**Time**: 3-4 hours

### Phase 1: Make It Reliable (1-2 days)

```
1. Fix llm.py cache_control — either remove it or enable the beta header
2. Fix matcher.py SentenceTransformer to load on startup (FastAPI lifespan event)
3. Fix RateLimiter memory leak — prune entries after window expires
4. Fix db.py f-string SQL — replace with safer parameterization
5. Add transaction wrapping to db.py multi-step operations
6. Add retry logic to client.py (3 retries with exponential backoff)
7. Add .env.example with all env vars documented
```

**Time**: 1-2 days

### Phase 2: Make It Maintainable (2-3 days)

```
1. Build types.ts — TypeScript interfaces for all entities
2. Build api.ts — centralized typed fetch client
3. Build ErrorBoundary.tsx
4. Migrate all 7 pages to use api.ts + types
5. Replace alert() calls with toast notifications (Tracker.tsx)
6. Consolidate status polling into single hook
7. Add pre-commit hooks (ruff, eslint)
8. Add basic pytest tests for server.py endpoints
```

**Time**: 2-3 days

### Phase 3: Make It Better (3-5 days)

```
1. Add SSE endpoint for real-time scoring updates (replace polling)
2. Add CSV export of job lists
3. Add dark mode toggle (Tailwind darkMode: 'class')
4. Enhance autofill answer sheet with better field detection
5. Add session persistence for autofill (cookies for form resumes)
6. Integrate FAISS for semantic job search (already in requirements)
7. Add Dockerfile (optional, for developers)
```

**Time**: 3-5 days

---

## 4. WHAT WE DO NOT BUILD

| Feature | Reason |
|---------|--------|
| Resume Editor (drag-drop) | Existing tailor.py + documents.py already generate tailored resumes. Resume editor is a complete rebuild of the resume pipeline. Do it in v2 if users ask for it. |
| Auto-Apply Engine | Contradicts review-first philosophy. Existing autofill.py already pre-fills forms. Enhance the answer sheet instead. |
| 3D Frontend | Zero functional value. Adds bundle size, maintenance burden. |
| WeasyPrint | Doesn't work on Windows. fpdf2 already generates PDFs. |
| Telegram Notifications | Requires 24/7 daemon. Too complex for v1. |
| MCP Server | Niche feature. Build if Claude/Cursor users request it. |
| Multi-Profile | One profile per user is enough for v1. Profiles directory already exists. |

---

## 5. DEPENDENCY GRAPH

```
Phase 0 (Fix Crashes) → Phase 1 (Make Reliable) → Phase 2 (Make Maintainable) → Phase 3 (Make Better)
```

Each phase produces a deployable, working app. You can stop after any phase.

---

## 6. TIME ESTIMATE

| Phase | Time |
|-------|------|
| 0: Make It Run | 3-4 hours |
| 1: Make It Reliable | 1-2 days |
| 2: Make It Maintainable | 2-3 days |
| 3: Make It Better | 3-5 days |
| **Total** | **~2 weeks** |

---

## 7. WHY THIS PLAN IS BETTER THAN THE PREVIOUS ONE

| Previous Plan | This Plan |
|--------------|-----------|
| 6 phases, 3-4 weeks | 4 phases, ~2 weeks |
| Resume Editor (5-7 days) | No resume editor — enhance existing tailor.py instead |
| "Power Features" phase | Only features with proven user value |
| Testing as a separate phase | Tests built into Phase 2 |
| "Assisted Apply" as a phase | Enhanced autofill in Phase 3 (smaller scope) |
| Docker + DevOps as phase | Dockerfile only (optional), pre-commit hooks in Phase 2 |
| 18 bugs listed | 28 bugs listed |
| Silent bugs (#9-18, #28) completely missed | All found and addressed |

---

## 8. THE BRUTAL TRUTH

The codebase has **18 real bugs** (6 crash, 12 silent), zero tests, and zero CI. Adding features on top of this is building a house on sand.

The Resume Editor plan (previous Phase 2, 5-7 days) was the biggest time sink with the lowest ROI. The existing pipeline (`tailor.py` → AI generates tailored resume → `documents.py` → PDF/DOCX output) already works. Adding drag-and-drop editing means rewriting that entire pipeline.

The right move: fix what's broken, make it reliable, add types and tests, then ship. New features come AFTER the foundation is solid.