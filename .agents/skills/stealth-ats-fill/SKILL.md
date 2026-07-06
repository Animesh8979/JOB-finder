---
name: stealth-ats-fill
description: "Adapter registry for ATS form filling. Hardens src/ats_engines/ against prompt-injection via the _safe_selector() allowlist. Maps field-schema per provider (Greenhouse/Lever/Ashby/Workday/iCIMS/BambooHR/SmartRecruiters) and never auto-submits on gated domains."
---

# Stealth ATS Fill Skill

You are connected to the `Ai job finder` project. Use this skill whenever you extend `src/ats_engines/` to add a new ATS adapter or modify the form-fill pipeline.

## Inviolable rules (per MEMORY.md)

- **Gated domains — open-only, never auto-fill**: `linkedin.com`, `indeed.com`, `glassdoor.com`, `ziprecruiter.com`. Even if an adapter exists for one of these, it MUST either refuse the request or route to the manual review surface. The user makes every click on gated domains.
- **Review-first spine**: pre-fill only. Auto-submit stays OFF by default. Only Greenhouse/Lever/Ashby MAY have an opt-in auto-apply track with explicit per-job consent — and even there, NEVER on gated parents.
- **Prompt-injection defence**: every selector the LLM emits must pass `src/auto_apply.py` `_safe_selector()` (type guard → forbidden-substring scan → regex). Caps: `MAX_ACTIONS_PER_ITERATION = 25`, `MAX_TOTAL_ACTIONS = 75`, `MAX_FIELD_LENGTH = 500`.

## Adapter shape (matches `src/ats_engines/__init__.py`)

```python
def matches_url(url: str) -> bool: ...      # host-pattern matcher
def fill_page(page, apply_url, cfg) -> tuple[bool, str]: ...
```

Register via `register(matches_url, fill_page)` in the engine module. The dispatcher lazy-imports so a missing module never breaks app startup.

## Existing adapters `[VERIFIED]`

- `greenhouse.py` — host `greenhouse.io`
- `lever.py`     — host `lever.co`
- `workday.py`   — hosts `myworkdayjobs.com`, `workday.com`
- `__init__.py`  — `register`, `_ensure_registered`, `engine_for(url)`, `fill_with_engine(...) -> (bool, msg)`

## Pending adapters (planned in T7 — see FINAL_REPORT.md)

iCIMS, BambooHR, SmartRecruiters, Jobvite, Taleo, Comeet, Recruitee, Teamtailor, Personio. v1 ships Top-3 (iCIMS, BambooHR, SmartRecruiters); the rest are documented in FINAL_REPORT for next-phase.

## Stealth-cookbook (cross-ref `stealth-scraping-automation`)

When driving ATS forms via Playwright:
- `playwright-stealth` plugin is mandatory.
- Randomized jitter `random.uniform(1.2, 3.8)` between fills, never `time.sleep(2)`.
- `domcontentloaded` over `networkloaded` — the latter hangs on heavy ATS bundles.
- One Edge profile per ATS host under `data/bot_profile/<host>/` for cookie/UA continuity.

## Test coverage gaps

- No end-to-end test exercises `fill_with_engine` against a real Greenhouse/Lever form.
- `_safe_selector()` is covered via `tests/test_safe_selector.py` (21 cases, parametric matrix) — that proves the ALLOWLIST works, not the FILLER.
