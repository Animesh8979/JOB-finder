"""Workday deterministic parser — Workday forms are multi-page and JS-heavy."""
from __future__ import annotations

import time
import random
from typing import Any


def _paginate_and_fill(page: Any, cfg: dict[str, Any]) -> None:
    """Traverse multi-page Workday applications and fill each page."""
    from src.autofill_runner import _fill
    
    max_pages = 10
    for _ in range(max_pages):
        try:
            page.evaluate("window.scrollTo(0, 0)")
        except Exception:
            pass
            
        # Let the hybrid engine fill the current page
        _fill(page, cfg)
        
        try:
            # Robust Playwright selectors for navigating pagination
            next_btn = page.locator(
                'button[data-automation-id="bottom-navigation-next-button"], '
                'button:has-text("Next"), '
                'button[title="Next"]'
            ).first
            
            if not next_btn.is_visible(timeout=2000):
                break
                
            next_btn.click()
            # Mandatory jitter as per stealth-ats-fill SKILL rules
            time.sleep(random.uniform(1.2, 3.8))
            
            # Wait for the next page to load via domcontentloaded
            page.wait_for_load_state("domcontentloaded", timeout=10000)
        except Exception:
            # Next button not found or click failed (end of form)
            break


def fill_workday(page: Any, cfg: dict[str, Any]) -> bool:
    try:
        # Workday's Apply flow is multi-page. We use our robust paginator.
        _paginate_and_fill(page, cfg)
    except Exception:
        return False
    return True
