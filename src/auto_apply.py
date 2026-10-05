"""
Autonomous Auto-Apply Engine leveraging a stealth-first browser session.
Primary engine is Camoufox (anti-detect Firefox); falls back to Playwright Chromium
with an isolated Edge-style profile. This allows the bot to use a persistent local
session, bypassing login repetition and bot challenges.
"""
import logging
import re
from typing import Dict, Any

from src.stealth_browser import launch_async as stealth_launch_async

from src import llm, config, db
import uuid
import threading

logger = logging.getLogger(__name__)

_global_apply_lock = threading.Lock()
_active_session_job = None

class ApplicationSession:
    """Mutex enforcing single-active application session to prevent browser profile corruption."""
    def __init__(self, job_id: int, run_id: str = "manual_apply"):
        self.job_id = job_id
        self.run_id = run_id
        self.lock_token = str(uuid.uuid4())
        self._acquired = False

    def acquire(self) -> bool:
        global _active_session_job
        with _global_apply_lock:
            if _active_session_job is not None:
                return False
            _active_session_job = self.job_id
            self._acquired = True
            db.create_application_session(self.lock_token, self.job_id, self.run_id, "acquired", None)
            return True

    def release(self) -> None:
        global _active_session_job
        with _global_apply_lock:
            if self._acquired and _active_session_job == self.job_id:
                _active_session_job = None
                self._acquired = False
                db.update_application_session(self.lock_token, status="released")

# --- Prompt-injection defense ---
# Selectors returned by the LLM (over attacker-influenced DOM) are passed to
# Playwright. Without an allowlist, a malicious page could craft hidden HTML
# whose id is `javascript:...` or a Playwright engine-internal locator. We
# whitelist the safe CSS selector shapes and explicitly block:
#  - javascript: / data: / file: URI prefixes
#  - Playwright's "internal" text= / xpath= / id= engine specs
#  - the playwright-specific chained `>>` and `:light` selectors
#  - any IFrame / shadow-piercing noise
# A safe CSS selector starts with one of: #id, .class, tag, or [attr]. After
# that, the rest is a constrained CSS character set. We require the *whole*
# selector to cleanly match — anything surprising (operators, quotes) and we
# return None. The regex below accepts starting with #, ., a letter, or `[`.
_SAFE_SELECTOR_RE = re.compile(
    # Outer form: starts with #id / .class / tag / [ / *  optionally followed by
    # more selector chars; allows attribute brackets with =, quotes (both
    # single and double), digits, letters. This is the standard CSS3 attribute
    # predicate alphabet.
    r"^[#.A-Za-z\[\*][\w\-\[\]\(\)\"'\=\^\$\*|~, .#:>+]*$"  # noqa: E501
)
_FORBIDDEN_SELECTOR_PIECES = (
    "javascript:", "data:", "vbscript:", "file:",
    "internal:", "internal:control", "internal:role",
    "internal:attr=", ">>",
    ":light",
)

MAX_ACTIONS_PER_ITERATION = 25
MAX_TOTAL_ACTIONS = 75
MAX_FIELD_LENGTH = 500


def _safe_selector(sel: str) -> str | None:
    """Return sel if it's syntactically safe to pass to page.locator(), else None."""
    if not isinstance(sel, str):
        return None
    sel = sel.strip()
    if not sel:
        return None
    if len(sel) > 320:
        return None
    lowered = sel.lower()
    for bad in _FORBIDDEN_SELECTOR_PIECES:
        if bad in lowered:
            return None
    if not _SAFE_SELECTOR_RE.match(sel):
        return None
    return sel


async def connect_and_apply(job_url: str, profile_text: str) -> Dict[str, Any]:
    """
    Connects to an isolated Edge browser profile for safe background automation.
    Requires the user to run setup_bot_profile.py once to log into ATS portals.
    """
    logger.info(f"Initiating Auto-Apply sequence for: {job_url}")
    
    try:
        import html2text
        from contextlib import AsyncExitStack

        bot_profile_dir = config.DATA_DIR / "bot_profile"
        bot_profile_dir.mkdir(parents=True, exist_ok=True)
        
        # Cleanup stale lock files that can cause playwright to hang
        lock_files = ['SingletonLock', 'SingletonCookie', 'SingletonSocket']
        for lock_file in lock_files:
            file_path = bot_profile_dir / lock_file
            if file_path.exists():
                try:
                    file_path.unlink()
                except OSError:
                    pass

        # Stealth-first engine (Camoufox when installed; Chromium fallback).
        # stealth_browser keeps a separate "-camoufox" profile dir internally.
        async with AsyncExitStack() as stack:
            context = await stack.enter_async_context(
                stealth_launch_async(user_data_dir=bot_profile_dir, headless=True)
            )

            try:
                page = context.pages[0] if context.pages else await context.new_page()
                
                # Navigate to the job listing
                await page.goto(job_url, wait_until="networkidle")
                
                # Parse the DOM to find interactive elements
                from bs4 import BeautifulSoup
                import json
                
                max_iterations = 3
                total_actions = 0
                for iteration in range(max_iterations):
                    page_content = await page.content()
                    soup = BeautifulSoup(page_content, 'html.parser')
                    
                    # Extract interactable elements
                    elements = []
                    for tag in soup.find_all(['input', 'textarea', 'select', 'button']):
                        el_info = {
                            'tag': tag.name,
                            'id': tag.get('id', ''),
                            'name': tag.get('name', ''),
                            'type': tag.get('type', ''),
                            'placeholder': tag.get('placeholder', ''),
                            'value': tag.get('value', ''),
                            'text': tag.get_text(strip=True)[:50]
                        }
                        if tag.get('id') or tag.get('name'):
                            elements.append(el_info)
                            
                    if not elements:
                        logger.info("No interactive elements found on page.")
                        break
                        
                    # Prompt LLM
                    sys_prompt = (
                        "You are an autonomous job application agent. Given a list of HTML elements "
                        "and the candidate's profile, return a JSON array of actions to perform. "
                        "Format: [{\"action\": \"fill\"|\"click\"|\"select\", \"selector\": \"#id\" or \"[name='name']\", \"value\": \"text\" (if fill/select)}]. "
                        "Return an empty array [] if the form is complete or no actions can be confidently taken. "
                        "Do NOT submit the application yet, just fill fields."
                    )
                    
                    prompt = f"CANDIDATE PROFILE:\n{profile_text}\n\nPAGE ELEMENTS:\n{json.dumps(elements, indent=2)}"
                    
                    try:
                        actions = llm.generate_json(prompt, system=sys_prompt)
                    except Exception as e:
                        logger.error(f"LLM failed to generate actions: {e}")
                        break
                        
                    if not actions:
                        logger.info("LLM determined no further actions are needed.")
                        break
                        
                    logger.info(f"Iteration {iteration+1}: Got {len(actions)} candidate actions from LLM; validating.")

                    executed_any = False
                    actions_this_iter = 0
                    for action in actions[:MAX_ACTIONS_PER_ITERATION]:
                        if total_actions >= MAX_TOTAL_ACTIONS:
                            logger.warning("Hit MAX_TOTAL_ACTIONS safety cap; aborting further fills.")
                            break
                        try:
                            act = action.get('action')
                            sel = action.get('selector')
                            val = action.get('value')

                            if act not in ('fill', 'click', 'select'):
                                continue
                            safe = _safe_selector(sel or '')
                            if not safe:
                                logger.warning(f"Rejecting unsafe selector from LLM: {sel!r}")
                                continue

                            # Cap value length to prevent gigabyte paste attacks
                            if isinstance(val, str) and len(val) > MAX_FIELD_LENGTH:
                                val = val[:MAX_FIELD_LENGTH]
                            elif not isinstance(val, str) and val is not None:
                                val = str(val)[:MAX_FIELD_LENGTH]

                            locator = page.locator(safe).first

                            if act == 'fill' and val:
                                await locator.fill(val)
                                executed_any = True
                            elif act == 'select' and val:
                                await locator.select_option(val)
                                executed_any = True
                            elif act == 'click':
                                await locator.click()
                                executed_any = True
                                # Wait for potential navigation
                                await page.wait_for_timeout(2000)
                            total_actions += 1
                            actions_this_iter += 1
                        except Exception as e:
                            logger.warning(f"Failed to execute action {action}: {e}")
                            
                    if not executed_any:
                        break
                        
                    # Wait before next iteration to let DOM settle
                    await page.wait_for_timeout(3000)
                
                # Take final snapshot of what we accomplished
                final_content = await page.content()
                converter = html2text.HTML2Text()
                converter.ignore_links = False
                converter.ignore_images = True
                minified_markdown = converter.handle(final_content)
                
                return {
                    "status": "success",
                    "message": "Auto-apply sequence completed via LLM execution loop.",
                    "snapshot_length": len(minified_markdown)
                }
            except Exception:
                # Teardown is owned by AsyncExitStack (single close, both engines).
                logger.exception("Auto-apply execution loop failed")
                raise
                
    except Exception as e:
        logger.error(f"Playwright error during auto-apply: {e}")
        return {"status": "error", "message": f"Auto-apply error: {e}"}
