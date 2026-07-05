"""ATS engine dispatcher — detects apply URL's host and picks a validator.

Each engine returns (ok, error_msg, fields_filled). Engines must be DEFENSIVE: if
they can't recognize the form, they fall back to relying on the existing hybrid
LLM filler in src.autofill_runner. Engines MUST NOT auto-submit.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

# Each entry: host regex -> module with fill_<name>(page, cfg) -> bool
_ENGINES: dict[str, Any] = {}


def register(pattern: str, module: Any) -> None:
    _ENGINES[pattern] = module


# Register built-in engines (lazy import so missing modules don't break startup).
def _ensure_registered() -> None:
    if _ENGINES:
        return
    from src.ats_engines import greenhouse, lever, workday  # type: ignore
    register(r"greenhouse\.io", greenhouse)
    register(r"lever\.co", lever)
    register(r"myworkdayjobs\.com|workday\.com", workday)


def engine_for(apply_url: str) -> Any | None:
    _ensure_registered()
    host = (urlparse(apply_url).netloc or "").lower()
    for pat, mod in _ENGINES.items():
        if re.search(pat, host):
            return mod
    return None


def fill_with_engine(page: Any, apply_url: str, cfg: dict[str, Any]) -> tuple[bool, str]:
    """Dispatcher: returns (used_engine, status_message)."""
    mod = engine_for(apply_url)
    if mod is None:
        return (False, "No specialized engine for this host; using generic hybrid filler.")
    name = mod.__name__.split(".")[-1]
    try:
        func = getattr(mod, f"fill_{name}", None) or getattr(mod, "fill", None)
        if not callable(func):
            return (False, f"Engine {name} has no fill() — falling back to hybrid filler.")
        ok = func(page, cfg) is not False
        return (ok, f"Used ATS engine: {name}")
    except Exception as e:
        return (False, f"Engine {name} failed: {e}; falling back to hybrid filler.")
