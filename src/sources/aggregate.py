"""Aggregate jobs from all enabled sources, filter, and de-duplicate."""
from __future__ import annotations

from typing import Any

from . import adzuna, arbeitnow, himalayas, jobicy, remoteok, remotive
from . import greenhouse, lever, weworkremotely, hackernews, ashby, builtin
from . import wellfound, otta, themuse, usajobs, dice, simplyhired, careerbuilder, monster
from . import jobspy_adapter

REGISTRY = {
    # --- JobSpy Tier-1 Scraping Swarm ---
    "jobspy": jobspy_adapter,
    # --- Free public APIs (no auth needed) ---
    "remotive": remotive,
    "remoteok": remoteok,
    "arbeitnow": arbeitnow,
    "himalayas": himalayas,
    "jobicy": jobicy,
    "weworkremotely": weworkremotely,
    "hackernews": hackernews,
    "builtin": builtin,
    "themuse": themuse,
    "otta": otta,
    "wellfound": wellfound,
    "dice": dice,
    "simplyhired": simplyhired,
    "careerbuilder": careerbuilder,
    "monster": monster,
    "usajobs": usajobs,
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
    """Return (deduped+prefiltered jobs, {source: error_message}) via parallel orchestrator."""
    from .search_orchestrator import SearchOrchestrator
    orchestrator = SearchOrchestrator(source_timeout_sec=12.0, global_timeout_sec=45.0, max_workers=8)
    return orchestrator.fetch_parallel(prefs, per_source_limit=per_source_limit)
