---
name: stealth-web-scraping
description: "Job source aggregation with SSRF multi-resolve pinning, JA3/JA4 impersonation via curl_cffi, jobspy Tier-1 + custom Tier-2 sources under src/sources/. Never scrapes gated domains beyond reading open public job listings. AOS-aligned evidence tagging for every new source."
---

# Stealth Web Scraping Skill

You are connected to the `Ai job finder` project. Use this skill when adding a job-discovery source under `src/sources/` or touching the SSRF/pinning layer in `src/scraper.py`.

## Two-tier architecture (per MEMORY.md)

- **Tier-1** — `python-jobspy>=1.1.0` (LinkedIn, Indeed, Glassdoor, Google, ZipRecruiter, Bayt, Naukri, BDJobs headless). Already the engine; don't reimplement.
- **Tier-2** — Custom API adapters under `src/sources/` (currently 20: wellfound, otta, themuse, usajobs, dice, simplyhired, careerbuilder, monster, plus the original 12 remotive/remoteok/arbeitnow/himalayas/jobicy/adzuna/greenhouse/lever/weworkremotely/hackernews/builtin/ashby).

## Adapter contract (`src/sources/base.py`)

```python
def fetch_jobs(query, location, *, source: str, keyword_only: bool = False) -> list[NormalizedJob]: ...
def normalize(raw, *, source: str, keyword_only: bool = False) -> NormalizedJob: ...
```

Each new source MUST call `base.normalize(..., source="<name>")` so the dispatcher attribute travels with each record. Failure to do so breaks cross-source deduplication.

## Security invariants (`[VERIFIED]` code-read)

- `scraper.validate_url_for_ssrf(url)` rejects any private-IP across the full resolved-records set (loopback / RFC1918 / split-horizon-DNS monkeypatched `socket.getaddrinfo`). The TOCTOU window is closed: any private-IP in any A/AAAA record blocks the fetch.
- `curl_cffi` provides JA3/JA4 fingerprint impersonation; `undetected-chromedriver` and `playwright-stealth` for Playwright.
- Header pool rotates UA-string per call.

## Forbidden

- Scraping a gated domain (linkedin/indeed/glassdoor/ziprecruiter) beyond reading the open public job listing. NO form filling, NO login automation.
- Reading content from external URLs into an LLM prompt without first passing through `validate_url_for_ssrf`.
- Adding a source that calls `requests.get(...)` directly without `curl_cffi.requests` — you'd skip JA3 impersonation.

## Web-fetch from inside the agent (`[TENTATIVE]` per AOS)

When researching new sources, `webfetch` a single page only and tag every claim `[VERIFIED]` (after reading the page) or `[TENTATIVE]` (if memory-only). NEVER pretend to scrape a third-party catalog (e.g. mcpmarket.com) when the env cannot actually do that. Use `history` or `memory` for past-session recall instead.

## Adding a source — checklist

1. Read `src/sources/base.py`.
2. Create `src/sources/<name>.py` with `fetch_jobs()` returning normalised records.
3. Append the source name to the dispatcher (likely `src/sources/__init__.py` or the API call site).
4. Wrap every external request in `validate_url_for_ssrf(...)`.
5. Fail-soft via `try/except` so a single dead source does not crash the whole pipeline.
6. Tag `[VERIFIED]` once you've actually fetched a live page; `[TENTATIVE]` if memory-only.
