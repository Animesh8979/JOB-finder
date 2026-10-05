"""Autonomous Browser Navigation Agent.

Bridges modern agentic navigation (browser-use architecture) with battle-tested
local stealth infrastructure (Camoufox anti-detect + Playwright fallback,
autofill_runner indexed manifests, selector sanitization, and review-first gates).

Capabilities:
1. Multi-Step Navigation: Discovers 'Apply', 'Easy Apply', or external job forms.
2. Wizard Handling: Progresses through multi-page application flows (Workday, Greenhouse, Lever).
3. Precision Form Filling: Delegates field mapping to autofill_runner indexed LLM manifests.
4. Bot Detection Evasion: Uses Camoufox C++ fingerprint spoofing with automatic Playwright fallback.
5. Telemetry Tracking: Records navigation and apply attempts directly into the bandit engine.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import config
from .stealth_browser import launch_async as stealth_launch_async

logger = logging.getLogger(__name__)

# Action safety bounds
MAX_NAVIGATION_STEPS = 12
PAGE_TIMEOUT_MS = 25000


@dataclass
class BrowserAgentResult:
    status: str  # "SUCCESS", "REVIEW_REQUIRED", "LOGIN_REQUIRED", "CAPTCHA_DETECTED", "FAILED"
    url: str
    job_id: Optional[int] = None
    steps_executed: int = 0
    fields_filled: int = 0
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)
    snapshot_summary: str = ""
    error: Optional[str] = None


class AutonomousBrowserAgent:
    """High-intelligence browser automation agent."""

    def __init__(self, headless: bool = True, user_data_dir: Optional[Path] = None):
        self.headless = headless
        self.user_data_dir = user_data_dir or (config.DATA_DIR / "bot_profile")
        self.user_data_dir.mkdir(parents=True, exist_ok=True)

    async def detect_captcha(self, page) -> bool:
        """Inspects page for common anti-bot/CAPTCHA challenges."""
        try:
            content = (await page.content()).lower()
            indicators = [
                "cf-turnstile", "recaptcha", "g-recaptcha", "hcaptcha",
                "challenge-running", "arkoselabs", "human verification",
                "verify you are human", "press and hold"
            ]
            for ind in indicators:
                if ind in content:
                    logger.warning("CAPTCHA / Bot-Wall detected: %s", ind)
                    return True
            # Also check if any iframe points to captcha
            for frame in page.frames:
                url = frame.url.lower()
                if any(x in url for x in ("recaptcha", "turnstile", "hcaptcha")):
                    return True
        except Exception as e:
            logger.debug("Captcha check error: %s", e)
        return False

    async def detect_login_wall(self, page) -> bool:
        """Checks if current page is blocked by an auth/login wall."""
        try:
            url = page.url.lower()
            if any(k in url for k in ("/login", "/signin", "/auth", "/session/new")):
                return True
            # Check for prominent sign-in forms
            signin_btn = await page.query_selector("button:has-text('Sign In'), button:has-text('Log In'), input[type='password']")
            if signin_btn:
                return True
        except Exception:
            pass
        return False

    async def find_and_click_apply_button(self, page) -> Tuple[bool, str]:
        """Discovers and triggers 'Apply' or 'Apply Now' buttons across diverse ATS layouts."""
        apply_selectors = [
            "button:has-text('Apply Now')",
            "a:has-text('Apply Now')",
            "button:has-text('Easy Apply')",
            "button:has-text('Apply')",
            "a:has-text('Apply')",
            "[data-qa='apply-button']",
            "[data-automation-id='adventureButton']",
            "a[href*='apply']",
            "button[id*='apply']"
        ]

        for sel in apply_selectors:
            try:
                elem = await page.query_selector(sel)
                if elem and await elem.is_visible():
                    txt = (await elem.text_content() or "").strip()
                    logger.info("Found apply trigger with selector '%s' (text: '%s')", sel, txt)
                    # Wait for navigation or popup
                    await elem.click()
                    await page.wait_for_timeout(2500)
                    return True, txt
            except Exception as e:
                logger.debug("Apply trigger probe failed for %s: %s", sel, e)
                continue
        return False, ""

    async def _fill_page_async(
        self,
        page: Any,
        fill_cfg: Dict[str, Any],
        fill_log: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        """Asynchronously discovers, maps, and fills form inputs on an AsyncPage."""
        from .autofill_runner import _match_value
        filled = 0
        all_frames = [page.main_frame] + getattr(page.main_frame, "child_frames", [])
        resume_path = fill_cfg.get("resume_path")

        for frame in all_frames:
            try:
                loc = frame.locator("input, textarea, select")
                if asyncio.iscoroutine(loc):
                    loc = await loc
                inputs = await loc.all() if hasattr(loc, "all") else []
            except Exception as e:
                logger.debug("Frame locator error: %s", e)
                continue

            for el in inputs:
                try:
                    if not (await el.is_visible()) or not (await el.is_enabled()):
                        continue

                    tag = (await el.evaluate("el => el.tagName") or "").lower()
                    itype = ((await el.get_attribute("type")) or "text").lower() if tag == "input" else tag

                    if itype in ("hidden", "submit", "button", "password", "search"):
                        continue

                    # Handle resume file upload
                    if itype == "file":
                        if resume_path:
                            rpath = Path(resume_path).resolve()
                            # Path validation: Must be an existing PDF file
                            if rpath.exists() and rpath.suffix.lower() == ".pdf":
                                fname = ((await el.get_attribute("name")) or "").lower()
                                fid = ((await el.get_attribute("id")) or "").lower()
                                if any(k in fname or k in fid for k in ("resume", "cv", "file", "upload", "attachment", "document")):
                                    await el.set_input_files(str(rpath))
                                    filled += 1
                                    if fill_log is not None:
                                        fill_log.append({
                                            "label": fname or fid or "resume_upload",
                                            "value": str(rpath.name),
                                            "via": "file_upload"
                                        })
                        continue

                    # Build key from attributes and associated label
                    eid = await el.get_attribute("id")
                    lbl_text = ""
                    if eid:
                        try:
                            lbl_el = await frame.query_selector(f"label[for='{eid}']")
                            if lbl_el:
                                lbl_text = (await lbl_el.inner_text() or "").strip()
                        except Exception:
                            pass

                    key_parts = [
                        await el.get_attribute("name"),
                        eid,
                        await el.get_attribute("placeholder"),
                        await el.get_attribute("aria-label"),
                        lbl_text,
                    ]
                    key = " ".join(filter(None, key_parts)).strip()
                    val = _match_value(key, fill_cfg)

                    if val:
                        if tag == "select":
                            try:
                                await el.select_option(label=str(val))
                            except Exception:
                                try:
                                    await el.select_option(value=str(val))
                                except Exception:
                                    pass
                        elif itype in ("checkbox", "radio"):
                            if str(val).lower() in ("true", "1", "yes"):
                                await el.check()
                        else:
                            await el.fill(str(val))
                        filled += 1
                        if fill_log is not None:
                            fill_log.append({"label": key[:60], "value": str(val)[:120], "via": "profile_async"})
                except Exception as ex:
                    logger.debug("Field fill error for element: %s", ex)
                    continue

        return filled

    async def navigate_and_apply(
        self,
        job_url: str,
        profile_data: Dict[str, Any],
        resume_pdf_path: Optional[str] = None,
        job_id: Optional[int] = None,
        auto_submit: bool = False
    ) -> BrowserAgentResult:
        """Executes full end-to-end autonomous navigation and form filling."""
        from contextlib import AsyncExitStack
        from . import telemetry_bandit
        from .scraper import validate_url_for_ssrf

        # SSRF Security Gate (permits loopback when test mode is enabled)
        import os
        allow_local = os.environ.get("JOBFINDER_ALLOW_LOCAL_URLS") == "1"
        if not allow_local:
            try:
                validate_url_for_ssrf(job_url)
            except Exception as e:
                logger.error("SSRF validation failed for job URL '%s': %s", job_url, e)
                return BrowserAgentResult(
                    status="FAILED",
                    url=job_url,
                    job_id=job_id,
                    error=f"SSRF Security Violation: {e}",
                    snapshot_summary=f"URL rejected by security filter: {e}"
                )

        actions_taken = []
        fields_filled = 0
        step_count = 0

        # Record start in Telemetry Bandit if job_id provided
        if job_id:
            try:
                engine = telemetry_bandit.TelemetryEngine()
                engine.record_transition(
                    job_id=job_id,
                    arm_id="browser_use_nav",
                    new_stage=telemetry_bandit.LifecycleStage.TAILORED,
                    notes=f"Starting autonomous browser run for {job_url}"
                )
            except Exception as e:
                logger.error("Telemetry transition error: %s", e)

        async with AsyncExitStack() as stack:
            try:
                context = await stack.enter_async_context(
                    stealth_launch_async(user_data_dir=self.user_data_dir, headless=self.headless)
                )
                page = context.pages[0] if context.pages else await context.new_page()
                page.set_default_timeout(PAGE_TIMEOUT_MS)

                # Step 1: Navigate to Job URL
                logger.info("BrowserAgent: Navigating to %s", job_url)
                await page.goto(job_url, wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)
                step_count += 1
                actions_taken.append({"step": step_count, "action": "goto", "url": job_url})

                # Step 2: Check for Captcha or Login
                if await self.detect_captcha(page):
                    return BrowserAgentResult(
                        status="CAPTCHA_DETECTED",
                        url=page.url,
                        job_id=job_id,
                        steps_executed=step_count,
                        actions_taken=actions_taken,
                        snapshot_summary="Hit anti-bot verification challenge; human intervention required."
                    )

                if await self.detect_login_wall(page):
                    return BrowserAgentResult(
                        status="LOGIN_REQUIRED",
                        url=page.url,
                        job_id=job_id,
                        steps_executed=step_count,
                        actions_taken=actions_taken,
                        snapshot_summary="Login required for domain. Please log in via Setup or run headless=False."
                    )

                # Step 3: Find and click Apply if not already on an application form
                clicked_apply, apply_text = await self.find_and_click_apply_button(page)
                if clicked_apply:
                    step_count += 1
                    actions_taken.append({"step": step_count, "action": "click_apply", "label": apply_text})

                # Step 4: Multi-Step Form Fill Loop (Handles Workday, Greenhouse, etc.)
                max_form_pages = 4
                for form_page_idx in range(max_form_pages):
                    await page.wait_for_timeout(2000)
                    # Extract profile attributes and link fallbacks
                    profile_links = profile_data.get("links") or {}
                    if isinstance(profile_links, list):
                        links_dict = {}
                        for lk in profile_links:
                            if "linkedin" in lk:
                                links_dict["linkedin"] = lk
                            elif "github" in lk:
                                links_dict["github"] = lk
                        profile_links = links_dict

                    name_val = profile_data.get("name", "")
                    name_parts = name_val.split() if name_val else []
                    first_n = profile_data.get("first_name") or (name_parts[0] if name_parts else "")
                    last_n = profile_data.get("last_name") or (" ".join(name_parts[1:]) if len(name_parts) > 1 else "")

                    fill_cfg = {
                        "profile": profile_data,
                        "resume_path": resume_pdf_path,
                        "first_name": first_n,
                        "last_name": last_n,
                        "full_name": name_val,
                        "email": profile_data.get("email", ""),
                        "phone": profile_data.get("phone", ""),
                        "linkedin": profile_data.get("linkedin") or profile_links.get("linkedin", ""),
                        "github": profile_data.get("github") or profile_links.get("github", ""),
                        "location": profile_data.get("location", ""),
                        "website": profile_data.get("website") or profile_links.get("portfolio", "") or profile_links.get("website", ""),
                        "years_experience": str(profile_data.get("years_experience", 1)),
                        "experience_years": str(profile_data.get("years_experience", 1)),
                        "cover_letter": profile_data.get("cover_letter", ""),
                        "custom_answers": profile_data.get("custom_answers", {}),
                    }

                    fill_log = []
                    page_filled = await self._fill_page_async(page, fill_cfg, fill_log=fill_log)
                    fields_filled += page_filled
                    step_count += 1
                    actions_taken.append({
                        "step": step_count,
                        "action": f"fill_page_{form_page_idx + 1}",
                        "filled_count": page_filled,
                        "log": fill_log[:10]
                    })

                    # Look for Next / Continue / Review buttons
                    next_button = await page.query_selector(
                        "button:has-text('Next'), button:has-text('Continue'), "
                        "button:has-text('Review Application'), button:has-text('Save and continue')"
                    )

                    if next_button and await next_button.is_visible():
                        btn_txt = (await next_button.text_content() or "Next").strip()
                        await next_button.click()
                        actions_taken.append({"step": step_count, "action": "next_page", "button": btn_txt})
                        await page.wait_for_timeout(3000)
                    else:
                        break  # No more wizard pages

                # Step 5: Final Submission Check
                final_status = "REVIEW_REQUIRED"
                if auto_submit:
                    submit_button = await page.query_selector(
                        "button:has-text('Submit application'), button:has-text('Submit'), "
                        "input[type='submit'][value*='Submit']"
                    )
                    if submit_button and await submit_button.is_visible():
                        await submit_button.click()
                        await page.wait_for_timeout(4000)
                        final_status = "SUCCESS"
                        actions_taken.append({"step": step_count + 1, "action": "submit_confirmed"})
                        if job_id:
                            try:
                                engine = telemetry_bandit.TelemetryEngine()
                                engine.record_transition(
                                    job_id=job_id,
                                    arm_id="browser_use_nav",
                                    new_stage=telemetry_bandit.LifecycleStage.SUBMITTED,
                                    notes="Application submitted autonomously by BrowserAgent"
                                )
                            except Exception as e:
                                logger.error("Telemetry update error: %s", e)

                return BrowserAgentResult(
                    status=final_status,
                    url=page.url,
                    job_id=job_id,
                    steps_executed=step_count,
                    fields_filled=fields_filled,
                    actions_taken=actions_taken,
                    snapshot_summary=f"Processed application across {step_count} navigation steps; filled {fields_filled} inputs."
                )

            except Exception as e:
                logger.exception("Browser navigation error on %s", job_url)
                return BrowserAgentResult(
                    status="FAILED",
                    url=job_url,
                    job_id=job_id,
                    steps_executed=step_count,
                    fields_filled=fields_filled,
                    actions_taken=actions_taken,
                    error=str(e),
                    snapshot_summary=f"Execution halted due to exception: {e}"
                )

    async def discover_board_jobs(
        self,
        board_url: str,
        search_query: str,
        max_jobs: int = 15
    ) -> List[Dict[str, Any]]:
        """Navigates to a company career site or job board, searches, and extracts requisitions."""
        from contextlib import AsyncExitStack
        from .scraper import validate_url_for_ssrf
        discovered: List[Dict[str, Any]] = []

        try:
            validate_url_for_ssrf(board_url)
        except Exception as e:
            logger.error("SSRF validation failed for board URL '%s': %s", board_url, e)
            return []

        async with AsyncExitStack() as stack:
            try:
                context = await stack.enter_async_context(
                    stealth_launch_async(user_data_dir=self.user_data_dir, headless=self.headless)
                )
                page = context.pages[0] if context.pages else await context.new_page()
                await page.goto(board_url, wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)

                # Search input discovery
                search_inp = await page.query_selector("input[type='search'], input[placeholder*='search' i], input[placeholder*='job' i]")
                if search_inp:
                    await search_inp.fill(search_query)
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(4000)

                # Extract job anchors
                links = await page.query_selector_all("a[href*='/job/'], a[href*='/jobs/'], a[href*='gh_jid'], a[href*='/o/']")
                for link in links[:max_jobs]:
                    try:
                        href = await link.get_attribute("href")
                        title = (await link.text_content() or "").strip()
                        if href and len(title) > 3:
                            full_url = href if href.startswith("http") else f"{board_url.rstrip('/')}/{href.lstrip('/')}"
                            discovered.append({
                                "title": title.split("\n")[0].strip(),
                                "url": full_url,
                                "source_board": board_url
                            })
                    except Exception:
                        continue
            except Exception as e:
                logger.error("Job board discovery failed on %s: %s", board_url, e)

        return discovered
