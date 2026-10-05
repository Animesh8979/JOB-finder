# Beast-Mode Upgrade Report — 2026-08-23

Scope: `D:\Ai job finder`. Constraints honored: free-only, public/GitHub sources,
zero C: drive writes, no background bloat. Every change verified with exit codes /
live runs; nothing is claimed without proof.

---

## Round 2 — Ultra Max (same day)

### Bugs found by actually LOOKING at the running app (visual audit via Playwright)

| # | Bug | Root cause | Fix | Proof |
|---|-----|-----------|-----|-------|
| 1 | Jobs feed stuck "Loading…" forever; 4×500 errors | `JobView.match_breakdown: dict[str, int]` vs stored `{evidence_snippets: []}` — one bad row 500'd the whole endpoint | Model → `dict[str, Any]` + `_safe_breakdown()` coercion so a corrupt row can never poison the feed | `GET /api/v2/jobs` 500 → **200** |
| 2 | Bogus "Network Error: body stream already read" toasts | `apiFetch` read the error body twice (`.json()` then `.text()`) | Single `text()` read + `JSON.parse` fallback | 0 console errors |
| 3 | App 403'd its own SSE on custom ports | Middleware allowlisted only ports {5173,8000,3000}; server on :8017 locked out its own UI | Allow the request's own Host port (still localhost-locked) | `/api/stream/events` 403 → **200** |
| 4 | RecruiterScoreCard dot-plot rendered as vertical scatter | `.dots { flex-direction: column }` inside a row-flex parent | Category grid + horizontal dot rows | Screenshot verified |
| 5 | Flaky `test_search_orchestrator_fetch_parallel` | Mock adapter honored cancel-token and returned cleanly — racing the orchestrator's timeout marker | Mock now simulates a hung upstream (ignores token, sleeps past both deadlines); only the orchestrator can decide the outcome | 5/5 deterministic passes |
| 6 | Stale TEST_AUDIT runs shown as "2 ACTIVE" forever | Test rows in real DB (predates session; conftest isolation is sound) | Purged 2 rows; remaining runs: 0 | SQL count |

### Dashboard upgrades
- **Application Funnel panel** (`FunnelPanel.tsx`): Discovered → Saved → Applied → Interview → Offer with animated bars + response-rate badge + avg pipeline match, fed by the existing `/api/stats` (rule-based SQL, zero LLM cost).
- **Pipeline stats strip** (round 1) now confirmed live with real data: 100 pipeline / 68 strong fits / 100% remote / 77% avg match.

### Auto-apply brain upgrades (technique adopted from GitHub research, zero new deps)
Sources read this session: github.com/Skyvern-AI/skyvern (README + form-filling docs), browser-use family comparisons (indexed-element vs vision approaches).
- **Indexed element manifest** (`_bulk_llm_fallback` rewrite): numbered interactive elements + real `<select>` option labels → LLM returns `{"i": n, "value": …}` actions instead of inventing selectors. Smaller prompts, fewer hallucinated targets, values that actually exist in dropdowns.
- **Post-fill verification pack** (`_write_fill_report`): full-page screenshot + exactly-what-was-filled JSON log saved to `data/outputs/apply_previews/` after every assisted fill — review-first made visible.
- Runaway-generation caps (500 chars/field) and strict "never invent employers/dates/credentials" prompt guardrails.

### UI resilience
- **ErrorBoundary** (`ErrorBoundary.tsx`) wired at app root: a render crash now shows a recovery panel instead of a white screen.
- **StealthEngineCard** in Settings: live engine status via new `GET /api/v2/stealth-status` (Camoufox active v0.5.5 verified in screenshot).

### Round-2 verification gate (all observed)
| Check | Result |
|---|---|
| `ruff check` (all touched backend files) | All checks passed |
| `pytest tests -q` (full suite) | **85 passed** |
| `npm run typecheck` + `npm run build` | Clean, built |
| Visual audit (headless Chromium, SSE-aware probe) | **0 console errors, 0 failed requests** |
| Live endpoints | `/api/v2/jobs` 200 · `/api/v2/stealth-status` 200 · `/api/stats` 200 |

---

## 1. Stealth Engine Upgrade — Camoufox (the headline change)

**What:** All three browser automation paths now launch through
`src/stealth_browser.py`, which prefers **Camoufox** — a free, open-source
anti-detect Firefox fork exposing the standard Playwright API with C++-level
fingerprint spoofing (navigator, WebGL, fonts, WebRTC, timezone/locale) and
humanized cursor movement — and transparently falls back to the previous
Playwright Chromium behavior whenever Camoufox is absent or fails.

| Path | File | Change |
|---|---|---|
| Job-page scraping thread | `src/scraper.py::_pw_manager` | Camoufox ephemeral browser; per-task contexts no longer override UA/timezone/viewport under Camoufox (would create fingerprint mismatches) |
| Review-first autofill window | `src/autofill_runner.py::run` | Visible Camoufox context with `humanize=True`; engine-specific profile dir; robust review-wait loop via `page.context` |
| LLM auto-apply loop | `src/auto_apply.py::connect_and_apply` | Async Camoufox persistent context; lifecycle owned by `AsyncExitStack` (single close, both engines) |

**Why it's better than what was there:** `playwright-stealth==1.0.6` injects JS
patches that modern anti-bots detect trivially and is unmaintained;
`undetected-chromedriver` targets Selenium-era Chromium. Camoufox intercepts at
the C++ implementation level so pages cannot see automation through JS inspection,
and rotates internally-consistent fingerprints drawn from real-world device
distributions (BrowserForge). uBlock Origin ships built-in.

**Disk discipline (verified):** `camoufox.pkgman` resolves its storage root once at
import time via `platformdirs.user_cache_dir("camoufox")`. The wrapper patches that
single call before first import, pinning everything to
`D:\Ai job finder\data\camoufox` (override: `CAMOUFOX_INSTALL_DIR`). Live proof:

```
Installed D:\Ai job finder\data\camoufox\browsers\official\152.0.4-beta.29-b9ccdc29\camoufox.exe
ENGINE USED: camoufox
UA: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0
webdriver flag: False
```

**Safety valves:**
- `CAMOUFOX_ENABLED=0` → forces Chromium instantly.
- Launch failure → logged warning + Chromium fallback (product never breaks).
- Chromium and Firefox keep *separate* profile dirs (`<dir>-camoufox`) to prevent
  cross-engine profile corruption.
- Proxy configured? → `geoip=True` aligns timezone/locale/geolocation with exit IP;
  if the GeoIP dataset fetch fails, one retry without geoip instead of hard failure.

**Honest caveat (from upstream README, 2026):** Camoufox had a maintenance gap and
is "under active development" again; sophisticated WAFs may still find inconsistencies.
It remains a large upgrade over JS-injection stealth for job-board scraping.

**Management CLI:** `python -m src.stealth_browser --status` / `--fetch`.
`setup.bat` step 5 installs + fetches best-effort (skips gracefully offline).

Sources (fetched & read during this session):
- https://github.com/daijro/camoufox (README)
- https://camoufox.com/python/installation/
- https://camoufox.com/python/usage/
- https://raw.githubusercontent.com/daijro/camoufox/main/pythonlib/camoufox/utils.py (launch_options kwargs)
- https://raw.githubusercontent.com/daijro/camoufox/main/pythonlib/camoufox/pkgman.py (INSTALL_DIR import-time binding)

## 2. Performance — killing idle CPU burn ("no PC lag")

- `frontend/src/components/CinematicBackground.tsx`: the cursor-parallax loop ran an
  infinite `requestAnimationFrame` cycle forever. Now: sleeps entirely when the orbs
  settle (epsilon threshold), wakes on next mousemove, and renders a static aurora
  under `prefers-reduced-motion: reduce`. Idle tab CPU → ~0.
- Removed unused `@splinetool/react-spline` + `@splinetool/runtime` from
  `frontend/package.json` → **65 packages pruned** from node_modules on reinstall.

## 3. UX/UI upgrades

- **Pipeline stats strip** (`CommandCenter.tsx::StatsStrip`): Pipeline count,
  Strong fits (75+), Remote %, Avg match — computed client-side from already-fetched
  jobs, zero extra API calls.
- **Keyboard shortcuts** (`CommandCenter.tsx`): `/` or `Ctrl/Cmd+K` focuses the
  command bar (suppressed while typing); `Esc` closes any drawer. Shortcut hint
  surfaced in the feed header.
- **Relative timestamps** (`LiveIntelFeed.tsx::relativeTime`): "3h ago" style with
  graceful fallback to raw text; full timestamp on hover.

## 4. Hygiene fixed in passing

- `src/scraper.py`: moved mid-file `import queue` to top (ruff E402).
- `src/autofill_runner.py`: removed unused `os` / `config` imports (F401).
- `requirements.txt`: documented optional camoufox install (commented — CI/Docker stay lean).
- `.env.example` + `_env_d_disk.bat`: `CAMOUFOX_ENABLED`, `CAMOUFOX_INSTALL_DIR` wired into existing D-disk discipline.

## 5. Verification gate (all observed, none assumed)

| Check | Command | Result |
|---|---|---|
| Python lint (touched files) | `ruff check src/stealth_browser.py src/scraper.py src/auto_apply.py src/autofill_runner.py` | All checks passed |
| Backend tests | `pytest tests -q` | **85 passed** (one order-flaky orchestrator test passed 3/3 on re-runs) |
| Server import chain | `import server; import src.auto_apply, src.scraper` | OK |
| Frontend types | `npm run typecheck` | Clean |
| Frontend build | `npm run build` | Built (14.4s) |
| Live stealth launch | wrapper → example.com | ENGINE=camoufox, webdriver=False, UA consistent |
| Storage location | status() | `data\camoufox` on D: |

## 6. Deliberately NOT done (constraint discipline)

- No new MCP servers / resident daemons (memory budget).
- No paid APIs (Apify, proxy vendors) — free tier only.
- No PostgreSQL/migration churn — SQLite is correct for single-user local-first.
- PDF engine left on plain Chromium (no stealth value in headless PDF rendering).

## 7. Next high-ROI ideas (researched, not implemented — awaiting direction)

1. ~~Settings-drawer stealth card~~ **DONE in Round 2.**
2. **JobSpy source enablement check**: verify current python-jobspy LinkedIn policy
   before re-enabling gated sources (ToS-sensitive).
3. ~~Vite code-splitting~~ — **DONE in Wave 3** (below).

---

## Wave 3 — Code splitting + review-first evidence UI (2026-08-24)

### Frontend bundle surgery
- All five drawers lazy-loaded (`CommandCenter.tsx`): `JobDetailDrawer`,
  `PrepareApplyDrawer`, `TailorDrawer`, `SettingsDrawer` via `React.lazy` +
  `<Suspense>` fallbacks.
- **Result:** main bundle **295KB** (was ~500KB+, chunk warning gone);
  deferred chunks verified in build output: SettingsDrawer 162KB,
  PrepareApplyDrawer 9KB, JobDetailDrawer 9KB, TailorDrawer 4KB.
- `MotionConfig reducedMotion="user"` wraps the app tree (framer-motion) —
  OS-level reduced-motion preference now disables animations.

### PrepareApplyDrawer — Recent Fill Verification Packs section
- New interface `PreviewItem`; fetches `/api/v2/apply-previews?limit=5`;
  renders company/title/generated_at/fields_filled_count per pack with
  screenshot link (`/apply-previews-files/{file}.png`) + JSON evidence link.
  Empty state explains the review-first evidence model.

### Verification gate (all observed)
| Check | Result |
|---|---|
| `npm run typecheck` + `npm run build` | Clean; >500kB warning **gone** |
| `pytest tests -q` (full suite) | **85 passed**, 1 warning, 211s |
| Live endpoints | `/api/v2/jobs`, `/api/v2/apply-previews`, `/api/v2/stealth-status` all **200** |
| Visual audit (headless Chromium) | **5/5 screenshots, 0 console errors, 0 HTTP ≥400** — command center, stealth card, recruiter scorecard, funnel panel, verification packs drawer |

### Audit-infrastructure lesson (recorded for future sessions)
Background processes started in one bash call are reaped before the next call
— uvicorn died silently between calls twice, causing `ERR_CONNECTION_REFUSED`
audit failures. **Fix:** kill-port → start-server → poll-health → run-audit
must execute inside a SINGLE bash invocation. First audit pass also missed the
verification-packs screenshot because job cards are clickable `div`s, not
buttons — selector fixed to `div.cursor-pointer`, and misses now print loudly
instead of skipping silently.

---

## Wave 4 — A11y, ToS-safe sourcing, corpus audio mastering (2026-08-25)

### 1. Job cards made keyboard-accessible (bug found during audit)
- `LiveIntelFeed.tsx`: clickable job `div`s had no semantics — keyboard users
  could not open any job. Added `role="button"`, `tabIndex={0}`,
  `aria-label`, `aria-pressed`, Enter/Space `onKeyDown`, and a
  `focus-visible` ring.
- **Live DOM probe PASS**: `role=button tabIndex=0`, Enter key opens the detail
  drawer (Prepare Apply button reachable). Typecheck + build clean
  (main bundle 302KB, +7KB).

### 2. LinkedIn scrape source gated behind explicit opt-in (ToS research)
- Research (sources fetched this session): repo moved to
  github.com/speedyapply/JobSpy (PyPI redirects). LinkedIn still supported but
  README states it "is the most restrictive and usually rate limits around the
  10th page with one ip. Proxies are a must basically"; easy-apply filter no
  longer works; no ToS disclaimer exists in the library — and LinkedIn's own
  ToS prohibits scraping regardless.
- **Change:** both scrape paths (`src/job_discovery.py`,
  `src/sources/jobspy_adapter.py`) now exclude LinkedIn unless env
  `JOBSPY_LINKEDIN_ENABLED=1`. Default = Indeed/Glassdoor/Google/ZipRecruiter.
- Verified: ruff clean, gate present in source, full suite **85 passed**.

### 3. Corpus audio mastering (621 videos, non-destructive)
- Full-corpus LUFS measurement (4 parallel ffmpeg workers): median **-14.3**
  (already in target band), range -26.3…-6.6. Earlier "-24 everywhere" was
  sample bias toward quiet dark-caption videos.
- 94 files outside -17…-13 band re-mastered with two-pass linear loudnorm
  (I=-16, LRA=7, TP=-1.5) — video streams copied untouched. Output tree:
  `D:\short videos\__loudnorm_fixed__\` mirroring categories, originals
  untouched; `_loudnorm_manifest.csv` maps in→out LUFS.
- Verification: 87/94 inside band. 7 masters are peak-limited so TP=-1.5 caps
  boost regardless of mode (linear and dynamic passes converge identically);
  residual: those 7 sit at -16.9…-17.5 LUFS (~1 LU under band edge) — left as-is
  rather than brickwall-limiting audible quality for a vanity number.
- Lesson recorded: measurement CSV columns were written swapped (bucket↔category),
  caught by path-existence check before any data damage.
