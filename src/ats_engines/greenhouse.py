"""Greenhouse deterministic schema-first filler.

Field names are VERIFIED from the official Greenhouse Job Board API docs:
  https://developers.greenhouse.io/job-board.html#submit-an-application
Example form HTML and curl both show these stable `name=` attributes:
  first_name, last_name, email, phone, location, latitude, longitude,
  country_short_name, resume, cover_letter, mapped_url_token, data_compliance[*]

Custom questions use `question_<id>` per-post (we can't prelist these — they
depend on the specific job application. The hybrid LLM filler handles those
opportunistically after this schema fills the known-core fields).

This adapter does NOT auto-submit. It returns control to caller after fill.
Falls back to the hybrid filler (src.autofill_runner._fill) on any exception,
so a page mutation can't break the user's progress.
"""
from __future__ import annotations

from typing import Any

# CRUD-ish field map: form_field_name -> profile_key_path
# Keys are VERIFIED to match the `name=` attribute Greenhouse emits.
# Values are dot-paths into the parsed profile dict (see src.profile_parser).
SCHEMA: dict[str, str] = {
    "first_name":            "first_name",
    "last_name":             "last_name",
    "email":                 "email",
    "phone":                 "phone",
    "location":              "location",
    # latitude / longitude / country_short_name are Hidden inputs that Greenhouse
    # expects pre-populated by a Google Places Autocomplete widget — out of scope
    # for a deterministic filler. Leaving them alone is safer than writing wrong values.
    # "latitude": "latitude",
    # "longitude": "longitude",
    # "country_short_name": "country_short_name",
    # resume / cover_letter are input_file (need a path on disk + file upload) —
    # handled by the hybrid filler, not by deterministic text injection.
}


def _safe_set(page: Any, selector: str, value: str) -> bool:
    """Set an input, select, or textarea value, swallowed-exception style. Returns True on success."""
    if not value:
        return False
    try:
        # CSS attribute selector — survives Greenhouse's React re-mounts that
        # reassign id= but never reassign name= (per official docs example).
        el = page.wait_for_selector(selector, timeout=1500)
        if el is None:
            return False
            
        tag_name = el.evaluate("el => el.tagName.toLowerCase()")
        if tag_name == "select":
            try:
                el.select_option(value=str(value), timeout=1000)
            except Exception:
                try:
                    el.select_option(label=str(value), timeout=1000)
                except Exception:
                    return False
        else:
            el.fill(str(value))
        return True
    except Exception:
        return False


def fill_greenhouse(page: Any, cfg: dict[str, Any]) -> bool:
    """Schema-first Greenhouse fill. Never submits.

    Args:
        page: Playwright Page on a Greenhouse apply form (boards.greenhouse.io).
        cfg: must contain 'profile' dict with the parsed candidate profile.

    Returns:
        True if at least one known field was filled successfully;
        False signals the dispatcher to fall back to the hybrid LLM filler.
    """
    profile = cfg.get("profile") or {}
    # Walk known schema; collect how many we actually filled.
    filled = 0
    for form_name, profile_key in SCHEMA.items():
        value = profile.get(profile_key)
        if not value:
            continue
        # Robust selector covering input, select, and textarea fields
        selector = f'input[name="{form_name}"], select[name="{form_name}"], textarea[name="{form_name}"]'
        if _safe_set(page, selector, str(value)):
            filled += 1

    # Even if we did fill some, hand off to the hybrid filler for the rest
    # (resume upload, custom questions, demographics). The hybrid filler is
    # idempotent on already-filled fields — it won't re-set them.
    try:
        from src.autofill_runner import _fill  # type: ignore
        try:
            page.evaluate("window.scrollTo(0, 0)")
        except Exception:
            pass
        _fill(page, cfg)
    except Exception:
        # As long as we filled at least one known field, count as success.
        pass

    return filled > 0
