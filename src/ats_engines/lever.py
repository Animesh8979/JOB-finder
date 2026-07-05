"""Lever deterministic parser — Lever uses stable input names."""
from __future__ import annotations

from typing import Any


def fill_lever(page: Any, cfg: dict[str, Any]) -> bool:
    try:
        # Lever form fields: name, email, phone, org, etc.
        from src.autofill_runner import _fill
        try:
            page.evaluate("window.scrollTo(0, 0)")
        except Exception:
            pass
        _fill(page, cfg)
    except Exception:
        return False
    return True
