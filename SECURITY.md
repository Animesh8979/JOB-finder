# Security policy

> Remote Job Application Copilot is **local developer tooling**. It runs on
> your machine, holds your API keys, and fills application forms in a real
> browser. The threat model below covers the realistic day-to-day risks —
> nothing here is a promise that the tool will protect you from misuse.

## Trust boundary

- The **only** secrets that ever leave your machine are the AI API requests
  you make (Anthropic, Google Gemini) and the outbound HTTP fetches that the
  scraper issues when looking up public job postings.
- Backend (`server.py`) binds to `127.0.0.1` by default; the Streamlit and
  React UIs call it from the same machine. CORS is locked to the local
  origins we ship. The container image binds `0.0.0.0` only for CI/dev.
- Auto-apply and outreach are **review-first**: the tool never submits an
  application or sends an email. That is the load-bearing rule. The opt-in
  auto-apply track only runs against non-gated ATS-native pages
  (Greenhouse/Lever/Ashby) and requires an explicit per-job confirmation.

## What is hardened by default

- API keys live in `data/secrets.json` encrypted with Fernet (`data/.fernet_key`).
  `data/.fernet_key` and `data/chroma/` are `.gitignore`-d.
- `server.py` rate-limits LLM-touching endpoints, requires `POST` for any
  mutating endpoint, and rejects obvious cross-origin attempts.
- `scraper.validate_url_for_ssrf` rejects URLs whose hostname resolves to
  **any** private or loopback address across every resolved record — closes
  the split-horizon DNS window.
- `auto_apply` runs every LLM-suggested selector through an allowlist
  (`_safe_selector`) before executing it in the browser. Selector shapes
  that could escape (`:light`, `>>`, `javascript:`, `internal:`, ... ) are
  refused. Per-iteration and total action caps prevent runaway loops.

## Reporting an issue

If you find a vulnerability, open a private issue (or email the maintainer
listed in `README.md`). Please include a reproduction and the commit SHA.

## Out of scope / known limitations

- This tool is **not** a hardened multi-tenant SaaS. Do not expose the
  backend to the public internet without putting it behind an authenticated
  reverse proxy.
- Auto-apply on gated job boards (LinkedIn, Indeed, Glassdoor, ZipRecruiter)
  is **disabled by policy** because auto-apply on these sites is a fast
  route to getting your account banned. There is no setting that re-enables
  it from a release build.
- The optional `data/bot_profile/` directory lets the local Edge/Chromium
  profile persist — that's a convenience, but treat it as a sensitive dir
  (it can hold session cookies).
