"""Aggregate jobs from all enabled sources, filter, and de-duplicate."""
from __future__ import annotations

from typing import Any

from . import adzuna, arbeitnow, base, himalayas, jobicy, remoteok, remotive
from . import greenhouse, lever, weworkremotely, hackernews, ashby, builtin

REGISTRY = {
    # --- Free public APIs (no auth needed) ---
    "remotive": remotive,
    "remoteok": remoteok,
    "arbeitnow": arbeitnow,
    "himalayas": himalayas,
    "jobicy": jobicy,
    "weworkremotely": weworkremotely,
    "hackernews": hackernews,
    "builtin": builtin,
    # --- Require config (API keys or company board slugs) ---
    "adzuna": adzuna,
    "greenhouse": greenhouse,
    "lever": lever,
    "ashby": ashby,
}

# Default company board slugs for ATS sources.
# Users can override these via prefs; these cover popular tech companies.
DEFAULT_GREENHOUSE_BOARDS = [
    "airbnb", "discord", "figma", "gitlab", "gusto",
    "hashicorp", "notion", "plaid", "reddit", "stripe",
    "vercel", "webflow", "airtable", "brex", "cockroachlabs",
    "databricks", "dbt-labs", "duolingo", "elastic",
    "instacart", "loom", "miro", "openai", "retool", "rippling",
    "snyk", "square", "twilio",
]

DEFAULT_LEVER_BOARDS = [
    "netflix", "coinbase", "cloudflare", "postman",
    "anduril", "astranis", "benchling", "chainalysis",
    "deel", "grammarly", "mercury", "navan",
    "relativity", "scale", "samsara", "temporal",
]

DEFAULT_ASHBY_BOARDS = [
    "anthropic", "ramp", "linear", "vercel",
    "replit", "perplexityai", "cursor",
]


def build_query(prefs: dict[str, Any]) -> str:
    """A single representative search term for sources that accept one."""
    titles = prefs.get("titles") or []
    keywords = prefs.get("keywords") or []
    terms = titles[:1] or keywords[:2]
    return " ".join(terms).strip()


def _inject_ats_defaults(prefs: dict[str, Any]) -> dict[str, Any]:
    """Inject default ATS board slugs if user hasn't configured their own."""
    out = dict(prefs)
    if not out.get("greenhouse_boards"):
        out["greenhouse_boards"] = DEFAULT_GREENHOUSE_BOARDS
    if not out.get("lever_boards"):
        out["lever_boards"] = DEFAULT_LEVER_BOARDS
    if not out.get("ashby_boards"):
        out["ashby_boards"] = DEFAULT_ASHBY_BOARDS
    return out


def fetch_all(
    prefs: dict[str, Any], per_source_limit: int = 50
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Return (deduped+prefiltered jobs, {source: error_message})."""
    query = build_query(prefs)
    prefs = _inject_ats_defaults(prefs)
    enabled = prefs.get("sources") or list(REGISTRY)
    collected: list[dict[str, Any]] = []
    errors: dict[str, str] = {}

    for sid in enabled:
        mod = REGISTRY.get(sid)
        if mod is None:
            continue
        try:
            collected.extend(mod.fetch(query, per_source_limit, prefs))
        except Exception as e:  # one bad source shouldn't break the page
            errors[sid] = str(e)

    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for job in collected:
        if not base.matches_filters(job, prefs):
            continue
        key = job["dedupe_key"]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(job)

    return deduped, errors
