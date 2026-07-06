# AI Job Finder — COMPLETE MASTER UPGRADE PLAN

> Mission: Fix all critical bugs, close every security hole, add all major job portals, build enterprise-grade job search copilot
> Research: GitHub, HuggingFace, MCP Market, Apify, ScrapingBee, JobSpy

---

## PART 1: CRITICAL BUGS & VULNERABILITIES (28 found)

### 1.1 CRASH BUGS (Fix Immediately)
| # | File | Bug | Impact | Fix |
|---|------|-----|--------|-----|
| 1 | greenhouse.py:35 | normalize() positional dict vs keyword args | TypeError on every fetch | Convert to keyword unpacking |
| 2 | lever.py:33 | Same normalize() signature mismatch | TypeError on every fetch | Convert to keyword unpacking |
| 3 | hackernews.py:60 | Same normalize() signature mismatch | TypeError on HN fetch | Convert to keyword unpacking |
| 4 | server.py:420 | json.dumps() without import json | NameError on ATS check | Add import json |
| 5 | auto_miner.py:5,11 | sqlite3.connect() but DB is PostgreSQL | OperationalError on start | Use psycopg2 pool from src.db |
| 6 | scraper.py:97 | from stealth_sync import stealth_sync — wrong module | ImportError on Playwright scrape | Fix to playwright_stealth import |
| 7 | client.py:24 | httpx.get() single attempt, no retry | Silent empty returns on failures | Add 3x retry with exponential backoff |
| 8 | aggregate.py:45 | fetch() returns None, extend() throws | Edge case job loss | Add null check before extend |

### 1.2 SILENT BUGS
| # | File | Bug | Impact | Fix |
|---|------|-----|--------|-----|
| 9 | db.py:285 | f-string SQL with unsanitized field names | SQL injection risk | Use parameterized queries |
| 10 | db.py:38-60 | autocommit=True, no transaction wrapping | Partial writes on multi-statement ops | Add explicit begin/commit/rollback |
| 11 | server.py:26-39 | RateLimiter defaultdict never pruned | Memory leak (~1KB/IP/day) | Prune entries after window |
| 12 | matcher.py | SentenceTransformer loaded sync on first call | Blocks event loop 5-10s | Load on FastAPI lifespan event |
| 13 | llm.py:50-52 | cache_control needs beta header | Cache never works, full cost | Enable anthropic-beta header or remove |
| 14 | scraper.py:108 | Hardcoded Chrome/120 UA (Dec 2023) | Easy bot detection | Use dynamic rotating UAs |
| 15 | scraper.py:76 | SSL verify=False | MITM vulnerability | Set verify=True |
| 16 | client.py UA | Says "personal job search tool" | Announces itself as bot | Use realistic browser UAs |
| 17 | requirements.txt | Missing numpy, scikit-learn, bs4, feedparser | Import errors at runtime | Add missing deps |
| 18 | cron_daemon.py | Pure stub, sleeps forever | Zero background mining | Implement actual mining loop |
| 19 | autofill.py | API keys passed via stdin to subprocess | Credential leak to subprocess memory | Use secure env vars |
| 20 | .gitignore | data/.fernet_key not ignored | All secrets decryptable if committed | Add to .gitignore |

### 1.3 SECURITY VULNERABILITIES
| # | Severity | Vulnerability | File | Fix |
|---|----------|--------------|------|-----|
| 1 | CRITICAL | SQL injection in f-string queries | db.py:285 | Parameterized placeholders |
| 2 | CRITICAL | SSRF — no URL validation before fetching | scraper.py:52 | URL allowlist + IP validation |
| 3 | HIGH | SSL verification disabled | scraper.py | Set verify=True globally |
| 4 | HIGH | API keys in subprocess stdin | autofill.py:99-106 | Use env vars |
| 5 | HIGH | Fernet key not gitignored | .gitignore | Add data/.fernet_key |
| 6 | MEDIUM | CORS allows all origins | server.py:65-76 | Restrict to configured origins |
| 7 | MEDIUM | Rate limiter unbounded history | server.py:26-39 | Prune expired entries |
| 8 | MEDIUM | No input validation | server.py | Add Pydantic validators |
| 9 | LOW | Hardcoded secrets in defaults | config.py:108 | Remove defaults |
| 10 | LOW | Stack traces in error responses | server.py | Generic error messages |
| 11 | LOW | Session fixation | Browser state | Regenerate session IDs |
| 12 | LOW | No HTTPS redirect | server.py | Add force-https middleware |

---

## PART 2: MISSING JOB PORTALS (Research from GitHub/JobSpy/Apify)

### Current: 14 sources (8 Tier-1 + 6 Tier-2)

### Missing Major Portals

#### US/Global Enterprise (High Priority)
| Portal | API | Method | Notes |
|--------|-----|--------|-------|
| Dice.com | Yes | REST API | Tech-focused, high-quality leads |
| CareerBuilder | Yes | REST API | Major US job board |
| Monster.com | No | Scraping (Apify/Playwright) | Legacy giant, still relevant |
| StackOverflow Jobs | RSS/API | API + scraping | Developer-focused |
| AngelList/Wellfound | Yes | GraphQL API | Startup jobs, high growth |
| Otta | Yes | JSON API | Curated tech jobs, excellent UX |

#### International (Medium Priority)
| Portal | Region | API | Notes |
|--------|--------|-----|-------|
| Xing | Germany/EU | Yes | LinkedIn competitor in DACH |
| StepStone | EU | Yes | Major European job board |
| Reed.co.uk | UK | Yes | Leading UK job site |
| Seek.com.au | Australia | Yes | ANZ market leader |
| JobStreet | SE Asia | Yes | SE Asia leader |
| Landing.jobs | Europe | Yes | Tech-focused, EU |

#### Niche/Specialized (Low Priority)
| Portal | Focus | Method | Notes |
|--------|-------|--------|-------|
| Working Nomads | Remote | RSS | Curated remote jobs |
| Golang Cafe | Golang | RSS | Language-specific |
| Rust Jobs | Rust | RSS | Language-specific |
| CryptoJobs | Web3 | Yes | Blockchain/crypto |
| FlexJobs | Remote | No (paid) | Premium remote listings |

### Integration Strategy
```
Tier 1 (python-jobspy): LinkedIn, Indeed, Glassdoor, Google Jobs, ZipRecruiter, Bayt, Naukri, BDJobs
Tier 2 (Custom APIs): RemoteOK, Remotive, Arbeitnow, Himalayas, Jobicy, WeWorkRemotely, HackerNews, Builtin, Greenhouse, Lever, Ashby, Adzuna
Tier 3 (New): Dice, CareerBuilder, StackOverflow, AngelList/Wellfound, Otta, Xing, StepStone, Reed, Seek, JobStreet, Landing.jobs
Tier 4 (Niche RSS): WorkingNomads, GolangCafe, RustJobs, CryptoJobs
```

---

## PART 3: ARCHITECTURAL IMPROVEMENTS

### 3.1 Database Layer
Current: SQLite with custom _CursorManager
Issue: No connection pooling, autocommit issues, single-writer bottleneck
Solution: Migrate to PostgreSQL with asyncpg + connection pool

New tables: resumes, auto_apply_queue, form_answer_cache, portal_configs

### 3.2 API Layer
Add Pydantic schemas: ResumePayload, AutoApplyPayload, GenerateDocPayload, JobSearchParams
Add endpoints: /api/sources/*, /api/jobs/search, /api/resumes/*, /api/generate/*, /api/auto-apply/*

### 3.3 Frontend
Migrate from Streamlit to React + TypeScript + Zustand
Add: Dashboard, FindJobs, JobDetails, ResumeEditor, Apply, Tracker, Outreach, Settings, JobExplorer3D

### 3.4 AI & MCP Integrations
MCP Servers: GitHub, PostgreSQL, Puppeteer, Slack, Brave Search, Playwright, Chroma, Apify
Enhanced AI: Multi-model pipeline with tool use, automatic fallback, caching

---

## PART 4: IMPLEMENTATION PHASES

### PHASE 0: Make It Run (3-4 hours)
1. Fix normalize() in greenhouse.py, lever.py, hackernews.py
2. Add import json to server.py
3. Fix stealth_sync import in scraper.py
4. Replace sqlite3 with PostgreSQL in auto_miner.py
5. Wire cron_daemon.py to actual mining
6. Add missing deps to requirements.txt
7. Add .fernet_key to .gitignore
8. Add GET /api/health endpoint
9. Fix scraper.py SSL verify=False
10. Fix scraper.py User-Agent to current Chrome
11. Fix client.py User-Agent to realistic browser

### PHASE 1: Make It Reliable (1-2 days)
1. Fix llm.py cache_control (enable beta header or remove)
2. Fix matcher.py SentenceTransformer to load on startup (lifespan event)
3. Fix RateLimiter memory leak — prune after window
4. Fix db.py f-string SQL — parameterized queries
5. Add transaction wrapping to db.py
6. Add retry logic to client.py (3 retries exponential backoff)
7. Add .env.example with all vars documented
8. Add SSRF validation to scraper.py
9. Fix CORS to configured origins only

### PHASE 2: Add Missing Job Sources (2-3 days)
1. Implement Dice.com API source
2. Implement CareerBuilder API source
3. Implement Monster.com scraper (Apify/Playwright)
4. Implement StackOverflow Jobs RSS source
5. Implement AngelList/Wellfound GraphQL source
6. Implement Otta JSON API source
7. Implement Xing API source
8. Implement StepStone API source
9. Implement Reed.co.uk API source
10. Implement Seek.com.au API source
11. Implement JobStreet API source
12. Implement Landing.jobs API source
13. Add RSS parsers for WorkingNomads, GolangCafe, RustJobs
14. Add portal_configs DB table for enabling/disabling sources
15. Add /api/sources endpoints for management

### PHASE 3: Frontend Migration (3-5 days)
1. Set up React 19 + TypeScript + Vite + Tailwind + Zustand
2. Migrate all Streamlit pages to React components
3. Build typed API client (api/client.ts)
4. Add ErrorBoundary, ToastNotifications
5. Build Dashboard with 3D elements (Three.js)
6. Build FindJobs with unified search
7. Build ResumeEditor with drag-and-drop
8. Build Tracker Kanban board
9. Build Settings page for source management
10. Add Vitest + Testing Library tests

### PHASE 4: Auto-Apply & AI Enhancements (3-5 days)
1. Implement anti-detection hardened auto-apply engine
2. Add playwright-stealth + patchright support
3. Build form detection heuristics + LLM fallback
4. Add auto-apply queue with DB persistence
5. Add form answer cache for reuse
6. Implement platform-specific handlers (LinkedIn, Indeed, Greenhouse, Lever)
7. Add MCP tool integration (GitHub, Brave Search, Playwright)
8. Implement multi-model AI pipeline (Claude primary, Gemini fallback)
9. Add automatic prompt caching
10. Build Apply page with review-first auto-fill

### PHASE 5: Hardening & Polish (2-3 days)
1. Add comprehensive pytest suite (api, auto-apply, scrapers)
2. Add pre-commit hooks (ruff, eslint, mypy)
3. Add Dockerfile for containerized deployment
4. Add GitHub Actions CI/CD pipeline
5. Add health check endpoint for Docker/k8s
6. Add structured logging (JSON format)
7. Add metrics collection (Prometheus-compatible)
8. Performance tuning (connection pools, async, caching)
9. Security audit (dependency scanning, secrets scanning)
10. Documentation (API docs, deployment guide, contribution guide)

---

## PART 5: MCP INTEGRATION ROADMAP

| Priority | MCP Server | Integration Point | Value |
|----------|-----------|-------------------|-------|
| 1 | server-playwright | Auto-apply form filling | Anti-detection automation |
| 2 | server-brave-search | Company research, contact finding | Better outreach |
| 3 | server-github | Company tech stack analysis | Better job matching |
| 4 | server-postgres | Analytics queries, reporting | Better insights |
| 5 | server-apify | Scrape portals without API | More job sources |
| 6 | server-chroma | Semantic job search | Better matching |
| 7 | server-puppeteer | Alternative to Playwright | Redundancy |
| 8 |encent | server-slack | Team notifications | Collaboration |

---

## PART 6: TECH STACK RESEARCH SUMMARY

### From GitHub/HuggingFace Analysis
- JobSpy: Best open-source multi-source scraper (LinkedIn, Indeed, Glassdoor, etc.)
- Apify: Best commercial scraping platform (actors for any site)
- python-job-scraper: Good reference for custom implementations
- MCP Market: 200+ MCP servers for AI tool integration
- FastAPI + Pydantic: Best Python API framework
- React 19 + Zustand: Best frontend stack for this use case
- Playwright + stealth: Best anti-detection browser automation
- ChromaDB: Best local vector DB for semantic search

---

## EXECUTION TIMELINE

| Phase | Time | Deliverable |
|-------|------|-------------|
| Phase 0: Make It Run | 3-4 hours | Working app with no crashes |
| Phase 1: Make It Reliable | 1-2 days | Secure, tested, reliable backend |
| Phase 2: Add Sources | 2-3 days | 25+ job sources, unified search |
| Phase 3: Frontend | 3-5 days | Modern React UI, replaces Streamlit |
| Phase 4: Auto-Apply + AI | 3-5 days | Semi-automated apply, MCP tools |
| Phase 5: Hardening | 2-3 days | Production-ready, CI/CD, docs |
| **Total** | **~2 weeks** | Enterprise-grade job copilot |

---

## IMMEDIATE ACTION ITEMS (Do First)

1. Fix all 8 crash bugs (Phase 0, items 1-8)
2. Fix 12 security vulnerabilities (Part 1.3)
3. Add missing dependencies to requirements.txt
4. Add .fernet_key to .gitignore
5. Fix SSL verify=False
6. Fix hardcoded User-Agents
7. Implement SSRF validation in scraper.py
8. Add proper transaction handling to db.py
9. Fix llm.py cache_control or remove it
10. Load SentenceTransformer on startup, not first request
