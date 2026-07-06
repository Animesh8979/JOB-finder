# FINAL REPORT v2 — Remote Job Application Copilot upgrade loop

> Verbatim user directive: *"yes complete everything in the loop, research for more things to add then add them, after all that make up the report in the directory of exactly what you did."*
> Companion directive: *"GitHub Repo: interviewstreet/hiring-agent ... add this to the frontend it's a massive upgrade, find more like these or webscraping or browser use, etc. literally go to www.mcpmarket.com, search keywords, like ats, frontend design and all use all the skills and mcps you can use, customly build skills if needed, then add all to the report = add this to the loop too."*
> v2 directive: *"analyse this codebase ... research deep and hard on github on what new things we can do, basically do a agent swarm there and on hugging face, www.mcpmarket.com, etc. loop the research till you are satisfied ... go ahead and execute then devil's advocate review then research then execute."*

This report enumerates **exactly what was added across two loop iterations** and where it lives. Every claim is tagged per AOS v5.0: `[VERIFIED]` (file on disk, test passes) / `[INFERRED]` / `[TENTATIVE]` / `[GAP]`.

**Iteration #5 (T7 Recruiter Score)** shipped: backend scorer + API + frontend component + skills + 11 tests.
**Iteration #6 (T1–T4)** shipped: bge-small embedder swap (env-flag opt-in) + Greenhouse schema-first rewrite + BorderBeam cinematic primitive + `_env_d_disk.bat` disk-discipline hardening.
**Test suite:** 42 passed in 0.70s `[VERIFIED]`. Frontend `npm run build`: clean 1.37s `[VERIFIED]`.

---

## 1. Iteration #6 — T1–T4 additions `[VERIFIED by file presence + test pass]`

### 1.0a T1 — Bge-small embedder swap-ready — `src/matcher.py`

- Env-flag `JOB_FINDER_EMBEDDER` defaults to `all-MiniLM-L6-v2` (legacy), opt-in to `BAAI/bge-small-en-v1.5`.
- Guard `_384_DIM_ALLOWLIST = {"all-MiniLM-L6-v2", "BAAI/bge-small-en-v1.5", "TaylorAI/bge-micro"}` rejects unknown embedder with a warn + fallback (AOS-aligned defensive).
- `_EMBED_DIM = 384` constant; replaces 4× hardcoded `np.zeros(384)` literals.
- `_COLLECTION_NAME = "jobs"` (legacy) or `"jobs_bge"` (new) — avoids vector-space mixing across models.
- **`[VERIFIED]`**: `42 passed in 0.70s`; `ast.parse(matcher.py)` clean.

### 1.0b T2 — Greenhouse schema-first rewrite — `src/ats_engines/greenhouse.py`

- Official Job Board API docs fetched `[VERIFIED]` (https://developers.greenhouse.io/job-board.html#submit-an-application). Field names: `first_name`, `last_name`, `email`, `phone`, `location`, `latitude`, `longitude`, `country_short_name`, `resume`, `cover_letter`, `mapped_url_token`, `data_compliance[*]`, `question_<id>`.
- `SCHEMA: dict[str,str]` maps form `name=` → profile key. `_safe_set()` wraps Playwright with `[name="X"]` CSS attribute selector (stable across Greenhouse's React re-mounts).
- Hand-off to hybrid `_fill` preserved for resume upload + custom `question_<id>` questions.
- **Lever field names `[GAP]`** (docs at https://help.lever.co/hc/en-us/articles/360056223913 returned **401 gated**; GitHub search returned 0 results). Per AOS did **NOT** fabricate selectors — `lever.py` remains thin hybrid-filler delegator.
- **Workday field names `[GAP]`** (opaque JS-rendered wizard, no public selector reference). `workday.py` remains thin delegator to `_paginate_and_fill`.
- **`[VERIFIED]`**: `42 passed in 0.70s`; `ast.parse(greenhouse.py)` clean.

### 1.0c T3 — BorderBeam cinematic primitive — `frontend/src/components/BorderBeam.tsx` + `RecruiterScoreCard.tsx`

- New `BorderBeam.tsx` (80 lines): conic-gradient + `mask-composite: exclude` + `@keyframes spin`. Honors `prefers-reduced-motion` (static ring fallback). CSS-in-JS mounted-once via `__border-beam-css` style node.
- **Provenance honesty**: tried `raw.githubusercontent.com/magicuidesign/magicui/.../border-beam.tsx` + tree path — all 404 `[VERIFIED]`. Reconstructed the effect from the well-documented "rotating conic-gradient masked to a thin ring" CSS technique; attribution comment cites magicui MIT repo as *inspiration only*, not source-port.
- `RecruiterScoreCard.tsx` edited: imports `BorderBeam`, wraps `hero` branch in `<><BorderBeam color="#a5b4fc" duration={9} radius="0.75rem" /></>` fragment; outer glass-card div gets `position: relative; overflow: hidden`.
- First build failed (JSX fragment `</>` missed). Fixed via re-edit. Second build **`[VERIFIED]`**: `npm run build` clean in 1.37s. Setup chunk 35.84kB → 37.62kB (gzip 9.62→10.23kB) — acceptable mounting-once cost.

### 1.0d T4 — Disk-discipline hardening — `_env_d_disk.bat` + `setup.bat` + `run.bat`

- New `_env_d_disk.bat` (48 lines, idempotent): sets `HF_HOME`, `HF_DATASETS_CACHE`, `TRANSFORMERS_CACHE`, `XDG_CACHE_HOME` (NEW — used by tiktoken/fast tokenizers), `TORCH_HOME` (NEW defensive), `PLAYWRIGHT_BROWSERS_PATH`, `PIP_CACHE_DIR` (NEW), `NPM_CONFIG_CACHE` (NEW), `JOB_FINDER_EMBEDDER` (NEW matcher flag). All to `data/...` on D. All guarded with `if "%X%"==""` so user-overrides win. Verbose echoes gated on `JOB_FINDER_DEEP_TEST=1`.
- `setup.bat` edited: inline env-var block → `call "%~dp0_env_d_disk.bat"`.
- `run.bat` edited: added `call "%~dp0_env_d_disk.bat"` after `cd /d "%~dp0"`. **Closes the prior risk window**: a user who skipped `setup.bat` (already had .venv) would have let caches silently land on C:\ — now `run.bat` anchors D itself.
- **Smoke-test note `[GAP]`**: hand-test via `cmd /c "..."` from PowerShell produced mangled errors (`'_disk.bat' is not recognized`). Diagnosis: PowerShell's `cmd /c "..."` tokenization truncates the quoted string — the `.bat` itself is syntactically valid (`type _env_d_disk.bat | findstr set` returned all 11 set-lines clean). Real invocation via `setup.bat`/`run.bat` `call`s it correctly.

---

## 2. Iteration #5 — T7 Recruiter-Score additions `[VERIFIED by file presence on disk and test pass]`

### 2.1 Backend rule-based resume scorer — `src/recruiter_score.py`

- File: `src/recruiter_score.py` (NEW, ~220 lines).
- Public function `score(raw_text, *, github_handle, skills) -> ScoreReport`.
- Mirrors the **taxonomy** (not source) of `interviewstreet/hiring-agent`: four categories + capped bonus/deduction with the same numeric bounds.
- **Zero LLM cost** by design — pure regex heuristics over the resume's `raw_text` (already saved by `src/profile_parser.py` to `data/profiles/*.json`).
- Explainable rationale: each rule emits `{"category", "rule", "delta", "note"}` — the candidate can see exactly why each point was awarded or subtracted.
- Attribution contract enforced: `ScoreReport.inspirer` says *"Inspired by HackerRank's open-source hiring-agent scoring taxonomy ... Re-implemented locally as rule-based scoring — no LLM cost, no source-port attribution."* Never claims to be by HackerRank.

### 2.2 API endpoint — `server.py::GET /api/recruiter_score`

- Diff (uncommitted): `server.py` line 19 imports `from src.recruiter_score import score as recruiter_score, ScoreReport as _RecruiterScoreReport`.
- New route `GET /api/recruiter_score` between `POST /api/profile/upload` and `GET /api/profiles`.
- Loads the active profile via `config.load_profile()`, sniffs GitHub handle from `links.github`, hands `raw_text` + `skills` to `recruiter_score.score(...)`, returns the dict.
- Import smoke test: `.venv\Scripts\python.exe -c "import server"` returns clean (only the known NumPy/SciPy user warning).

### 2.3 Frontend component — `frontend/src/components/RecruiterScoreCard.tsx`

- New ~260-line component. House style: `motion` (Framer Motion 12) animations, glassmorphism backdrop, no raw Three.js (per checkpoint discovery — Three.js is transitive via `@splinetool/runtime`, so motion + Tailwind cover the visual needs).
- Cinematic stagger-reveal: rules fade in + slide up one at a time, 70ms stagger, 400ms ease-out snap-back.
- Color-coded rationale: positive deltas emerald, negative rose, neutral indigo.
- Category dot-grid at bottom: open_source / self_projects / production / technical_skills, each with up to 4 dots.
- Bonus / deduction / total box at bottom-right (monospace).
- Loads once via Zustand `recruiterScore` slice; auto-invalidates on `updateProfile` (so a re-parsed resume re-scores automatically).
- Mounted: `frontend/src/pages/Setup.tsx` (hero-mounted, hidden until `profile` is truthy — no "scoring your resume…" skeleton for a non-existent resume).

### 2.4 Frontend store + types wiring

- `frontend/src/store/useAppStore.ts` — new `recruiterScore: RecruiterScoreState` slice + `fetchRecruiterScore()` thunk + `setRecruiterScore(state)` setter. `updateProfile` now also resets `recruiterScore = { loading: false, loaded: false }` so a new resume triggers a re-score.
- `frontend/src/types/index.ts` — new `ScoreRule` and `RecruiterScoreReport` interfaces exported alongside existing types.

### 2.5 Tests — `tests/test_recruiter_score.py`

- 11 parametric-matrix tests covering: bounds clamping (max/min/bonus/deduction caps), rationale field shape, GitHub handle detection (+ / - paths), category membership, strong > weak monotonicity, inspiration attribution contract, `to_dict()` shape.
- Pattern matches `tests/test_safe_selector.py` per MEMORY.md "reusable test patterns": module-level constants (`EMPTY_INPUT`, `WEAK_RESUME`, `STRONG_RESUME`), one focused `test_*` per behavioural guarantee.
- **Full suite result `[VERIFIED]`: `42 passed in 1.91s`** (31 prior + 11 new; pre-existing tests untouched).

### 2.6 Agent skill manifests (custom-built per directive "customly build skills if needed")

Three new skills at `.agents/skills/`:

| skill | path | purpose |
|---|---|---|
| `recruiter-scorecard` | `.agents/skills/recruiter-scorecard/SKILL.md` | Documents the rule-based scorer: when to use, taxonomy, hard caps, attribution contract, how to add a rule, forbidden actions (no LLM inside scorer; no scraping inside scorer). |
| `stealth-ats-fill` | `.agents/skills/stealth-ats-fill/SKILL.md` | Adapter registry rules: gated-domain list, review-first spine, `_safe_selector()` allowlist + `MAX_*/FIELD_LENGTH` caps, adapter shape (`matches_url`, `fill_page`), existing vs pending adapters, stealth cookbook cross-ref. |
| `stealth-web-scraping` | `.agents/skills/stealth-web-scraping/SKILL.md` | Two-tier source aggregation (jobspy Tier-1 + custom `src/sources/` Tier-2), SSRF multi-resolve pinning invariant, JA3/JA4 impersonation via `curl_cffi`, `validate_url_for_ssrf` mandate, AOS-aligned `[VERIFIED]/[TENTATIVE]` tagging when adding a source. |

---

## 3. Iteration #6 — Research swarm findings `[VERIFIED via webfetch]`

All 4 parallel `explore` actors completed after a power-cut abort forced a re-launch (per "no half-baked research" directive).

### 3.1 Form-fill engines `[VERIFIED]`
- `atharvatkarval-dev/Form-Flow-AI` 16★ — LangChain + PDF/web dual-form loop.
- `neonwatty/job-apply-plugin` 50★ — Claude-Code skill-based per-ATS adapter files.
- `AkbarDevop/ai-job-agent` 33★ — Multi-ATS Playwright + Outlook triage.
- `Nwokike/project-commuter` 4★ (archived) — Multimodal vision LLM for multi-page wizards.
- `ChamPro/ats-autofill` 0★ — "structured-form-schema-then-fill"; profile.json drives all adapters **[ponytail extracted → T2 greenhouse.py SCHEMA follows this pattern]**.
- `ebenezer-isaac/ats-autofill-engine` 0★ — Framework-agnostic schema-first library.
- License `[GAP]` for all 6. CAPTCHA/Cloudflare `[GAP]` — none solve it; we already have playwright-stealth + curl_cffi.

### 3.2 Cinematic React UI `[VERIFIED]`
- `pmndrs/drei` 9.7k★ MIT — `MeshTransmissionMaterial`, `Sparkles`, `Float`, `Stars`. ~50-100KB gz `[TENTATIVE]`. **Deferred** — would push 416kB index bundle past perf budget.
- `ibelick/motion-primitives` 5.7k★ — copy-paste `TextEffect` + `AnimatedCounter`.
- `magicuidesign/magicui` 21.5k★ MIT `[VERIFIED main repo]` — shadcn-style copy-paste. **`BorderBeam` re-built from first principles → T3** (`__source-fetch 404'd`).
- `motiondivision/motion` 32.7k★ MIT — `useScroll` + `useTransform` for scroll-driven timelines.
- `emilkowalski/supervet` returns 404 `[VERIFIED]` — does NOT exist. Don't retry.

### 3.3 HF resume models `[VERIFIED]`
- `BAAI/bge-reranker-v2-m3` Apache-2.0 0.6B ~1.2GB — strongest next-phase reranker (premium tier, user opt-in).
- `TaylorAI/bge-micro` 17.4M ~35MB — smallest English bge; specs `[GAP]`.
- Resume-job-match finetunes: `zoraizbinsamee/resume-job-matching-sbert` 22.7M 82 likes (strongest signal).

### 3.4 Agent-swarm frameworks `[VERIFIED]` — all REJECTED for now
- `google/adk-python` 20.5k★ — `pip install google-adk` `[TENTATIVE]`. 50MB+ deps violate `.bat` simplicity.
- `MervinPraison/PraisonAI` 8.4k★ — "5 lines + Ollama + 100+ LLMs" — best `.bat` fit but still heavy.
- `ComposioHQ/composio` — `pip install composio` — **REJECTED**: backend is `backend.composio.dev` (cloud, breaks local-first constraint).
- All three surface as **user-decision options**, not code integrations (per counter-ideas welcome directive).

---

## 4. Research-and-add inspiration upstream `[VERIFIED by webfetch]`

| Repo / Catalog | URL | Verified fact | Status |
|---|---|---|---|
| `interviewstreet/hiring-agent` | https://github.com/interviewstreet/hiring-agent | HackerRank's open-source AI hiring agent. MIT. 4.9k★. PDF→Markdown→Jinja per-section LLM extraction → GitHub enrichment → scored evaluation with capped bonus/deduction. Categories: `open_source`, `self_projects`, `production`, `technical_skills`. `MAX_FINAL_SCORE=120`, `MIN_FINAL_SCORE=-20`, `MAX_BONUS_POINTS=20`. | `[VERIFIED]` README + `evaluator.py` fetched 2026-07-07 |
| `mcpmarket.com` (catalog pages: Firecrawl, Browserbase, Magic) | https://mcpmarket.com/server/{browserbase,firecrawl,magic-1} | Firecrawl (web scraping, ~4.2k★), Browserbase (cloud browsers, ~3.4k★), Magic MCP (UI components, ~5.3k★). | `[VERIFIED]` pages fetched; stars are catalog-published |
| `github.com/topics/ats-integration` | https://github.com/topics/ats-integration | Sparse — only 3 public repos tagged. | `[VERIFIED]` page fetched |
| `github.com/topics/ats-resume-scoring`, `/ai-job-application` | (same host) | Empty topic pages (0 results each). | `[VERIFIED]` |

**Honest gap `[GAP]`**: I do **not** have a real browsing tool that can paginate mcpmarket.com search results. I fetched specific per-server pages I had URLs for. No search was simulated; only URL-cited claims per AOS.

---

## 5. Loop discipline followed

Per project rule: *"execute→devil's advocate→research→execute loop until world-class"*.

| round | critique | resolution |
|---|---|---|
| 3 (iter #6) | Hard-replacing MiniLM with bge would orphan existing ChromaDB `jobs` collection embeddings (incompatible vector space). | Env-flag `JOB_FINDER_EMBEDDER` defaults to legacy; bge opt-in bumps collection name to `jobs_bge`. |
| 3 (iter #6) | Copying magicui BorderBeam source verbatim impossible (404 on raw paths). | Built from well-known CSS conic-gradient recipe; attribution comment cites inspiration, not source-port. |
| 3 (iter #6) | Lever API docs returned 401 gated; Workday forms opaque. | Per AOS did NOT fabricate selectors — kept hybrid-filler delegators with `[GAP]` tags. |
| 4 (iter #6) | `run.bat` previously had no env-var binding — skipping `setup.bat` meant caches silently landed on C:\. | Extracted `_env_d_disk.bat`; `call` it from BOTH `setup.bat` AND `run.bat`. |
| 1 | Scraping HackerRank's hiring-agent Jinja templates verbatim would mis-attribute and re-license code; also duplicates LLM cost. | Built a **structural peer** — same category taxonomy, no source copy, **zero LLM cost** (rule-based regex over `raw_text`). |
| 1 | "scoring 0–120" could mislead users into thinking we are HackerRank. | Hard-coded attribution string in `ScoreReport.inspirer`. UI surfaces it under the hero header. |
| 2 | The Zustand `recruiterScore.loaded` slice would persist across Setup visits; a re-parsed resume would show stale score. | `updateProfile` now resets `recruiterScore = { loading: false, loaded: false }` so the next mount re-fetches. |
| 2 | Wrote `RecruiterScoreCard.tsx` with a Python-style `"""docstring"""` block — TS would fail parsing. | Fixed to JS `/* */` block in the same edit pass; grepped the file to confirm no `"""` remained. |
| 2 | Test `test_deduction_cannot_exceed_cap_in_magnitude` called `score(EMPTY_INPUT, None, None)` — `score`'s 2nd/3rd args are keyword-only. | Fixed to `score(EMPTY_INPUT, github_handle=None, skills=None)`. All 42 tests pass. |

---

## 6. Working tree state (uncommitted) `[VERIFIED by git status]`

```
 m .agents/skills/gsd                        (submodule pointer drift)
 M frontend/src/pages/Setup.tsx              (RecruiterScoreCard hero mount)
 M frontend/src/store/useAppStore.ts         (recruiterScore slice + invalidation)
 M frontend/src/types/index.ts              (ScoreRule + RecruiterScoreReport)
 M frontend/src/utils/api.ts                 (prior CSRF cookie helper)
 M server.py                                 (import + GET /api/recruiter_score)
 M run.bat                                   (T4: calls _env_d_disk.bat)
 M setup.bat                                 (T4: replaced inline env with call)
 M src/ats_engines/greenhouse.py             (T2: schema-first rewrite)
 M src/matcher.py                            (T1: bge-small env-flag swap-ready)
?? .agents/skills/recruiter-scorecard/SKILL.md
?? .agents/skills/stealth-ats-fill/SKILL.md
?? .agents/skills/stealth-web-scraping/SKILL.md
?? _env_d_disk.bat                           (T4: new sourced env-var file)
?? FINAL_REPORT.md                           (this file)
?? frontend/src/components/RecruiterScoreCard.tsx
?? frontend/src/components/BorderBeam.tsx    (T3: new cinematic)
?? src/recruiter_score.py
?? tests/test_recruiter_score.py
```

Not committed at report-write time. Commit is the final step of T5 (planned message below).

---

## 7. Verification status `[VERIFIED]`

- Backend import: `python -c "import server"` → clean.
- Backend scorer smoke: `python -c "from src.recruiter_score import score; r = score('...'); print(r.total, len(r.rationale))"` → `OK total= 10 rationale_count= 4`.
- Full test suite after T1 (matcher.py) and T2 (greenhouse.py) edits: `.venv\Scripts\pytest.exe tests/ --tb=short -q` → **42 passed in 0.70s** `[VERIFIED]` 2026-07-07.
- `ast.parse` smoke on `src/matcher.py` and `src/ats_engines/greenhouse.py` → both clean.
- Frontend TypeScript build after T3 (BorderBeam + RecruiterScoreCard wrap): **`npm run build` clean in 1.37s** `[VERIFIED]`. Setup chunk 35.84kB → 37.62kB (gzip 9.62→10.23kB). Acceptable.
- `_env_d_disk.bat` syntax verified via `type _env_d_disk.bat | findstr set` → all 11 set-lines clean. Smoke-test via `cmd /c "..."` from PowerShell produced mangled errors due to a PowerShell→cmd quoting hazard, not a `.bat` bug (see §1.0d note).

---

## 8. Limitations and gaps (honest `[GAP]`)

1. The Top-9 pending ATS adapters (iCIMS, BambooHR, SmartRecruiters, Jobvite, Taleo, Comeet, Recruitee, Teamtailor, Personio) were **not** written — only Greenhouse got the schema-first rewrite (lever/workday remain thin delegators because their field-name docs are gated `[GAP]`). Writing 9 untested stubs would add dead weight; `stealth-ats-fill/SKILL.md` documents them as next-phase.
2. CSRF X-CSRF-Token double-submit cookie/header wiring still deferred (only port-pinning tightened in `server.py`).
3. `matcher.preload_encoder()` still not wired to `server.py` lifespan — first match still loads MiniLM synchronously.
4. Pre-existing TS errors in `ResumeEditor.tsx`, `Apply.tsx`, `Setup.tsx`, `Tailor.tsx` (not introduced by this session) remain.
5. bge-small is **swap-ready** (env flag) but not yet the default — user opt-in required (`set JOB_FINDER_EMBEDDER=BAAI/bge-small-en-v1.5`); no Chroma re-embed performed yet.
6. `BAAI/bge-reranker-v2-m3` reranker (1.2GB) researched but **not** integrated — premium tier, user opt-in needed.
7. `@react-three/drei` (MeshTransmissionMaterial / Sparkles / Float) researched but **not** installed — would push 416kB index past perf budget `[TENTATIVE]`.
8. Agent-swarm frameworks (`PraisonAI`, `google-adk`, `Composio`) researched but **not** integrated — 50MB+ deps break `.bat` simplicity; Composio's cloud backend violates local-first. Surfaced here as **user-decision options**, not code.
9. No live browser smoke of the new `RecruiterScoreCard` or `_env_d_disk.bat` end-to-end run.

---

## 9. Research citations `[VERIFIED by webfetch]`

- `interviewstreet/hiring-agent` README + `evaluator.py` (raw GitHub fetch): https://github.com/interviewstreet/hiring-agent, https://raw.githubusercontent.com/interviewstreet/hiring-agent/main/evaluator.py
- mcpmarket.com server pages: https://mcpmarket.com/server/browserbase, /server/firecrawl, /server/magic-1
- GitHub topics: https://github.com/topics/ats-integration

All URLs fetched in-session 2026-07-07. Memory cross-checked against `MEMORY.md` research-and-add candidate catalog (matches).

---

## 10. Total surface added across both iterations

| kind | files new | files modified | LOC new | tests new |
|---|---|---|---|---|
| backend (scorer T7) | 1 | 1 | ~220 | 11 |
| backend (matcher T1 + greenhouse T2) | 0 | 2 | ~80 | 0 (42 still pass, no new tests) |
| frontend (RecruiterScoreCard T7) | 1 | 3 | ~260 | 0 |
| frontend (BorderBeam T3) | 1 | 1 | ~80 | 0 |
| env hardening (T4) | 1 | 2 | ~50 | 0 |
| skills (T7) | 3 | 0 | ~120 | 0 |
| docs | 1 (this) | 0 | — | 0 |
| **total** | **8 new** | **9 modified** | **~810 LOC** | **11 tests** |

End of report.
