"""
Autonomous Auto-Apply Engine leveraging Playwright over CDP to a local Edge browser.
This allows the bot to use the user's active session, bypassing login and bot challenges.
"""
import logging
import asyncio
from typing import Dict, Any

try:
    from playwright.async_api import async_playwright
except ImportError:
    pass  # Will be caught when function is called if not installed

from src import llm, db, config

logger = logging.getLogger(__name__)

async def connect_and_apply(job_url: str, profile_text: str) -> Dict[str, Any]:
    """
    Connects to an isolated Edge browser profile for safe background automation.
    Requires the user to run setup_bot_profile.py once to log into ATS portals.
    """
    logger.info(f"Initiating Auto-Apply sequence for: {job_url}")
    
    try:
        import os
        import html2text
        from contextlib import asynccontextmanager

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
                    
        @asynccontextmanager
        async def managed_playwright():
            p = await async_playwright().start()
            try:
                yield p
            finally:
                await p.stop()

        async with managed_playwright() as p:
            try:
                # Launch isolated persistent context
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=str(bot_profile_dir),
                    channel="msedge",
                    headless=True,  # Run headlessly in the background
                    args=["--disable-blink-features=AutomationControlled", "--no-first-run"]
                )
            except Exception as e:
                logger.error(f"Failed to launch persistent context: {e}")
                return {"status": "error", "message": f"Failed to launch isolated bot profile. Ensure it is not currently open. Error: {e}"}

            try:
                page = context.pages[0] if context.pages else await context.new_page()
                
                # Navigate to the job listing
                await page.goto(job_url, wait_until="networkidle")
                
                # Parse the DOM to find interactive elements
                from bs4 import BeautifulSoup
                import json
                
                max_iterations = 3
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
                        
                    logger.info(f"Iteration {iteration+1}: Executing {len(actions)} actions from LLM.")
                    
                    executed_any = False
                    for action in actions:
                        try:
                            act = action.get('action')
                            sel = action.get('selector')
                            val = action.get('value')
                            
                            if not sel: continue
                            
                            locator = page.locator(sel).first
                            
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
                    "message": f"Auto-apply sequence completed via LLM execution loop.",
                    "snapshot_length": len(minified_markdown)
                }
            finally:
                await context.close()
                
    except Exception as e:
        logger.error(f"Playwright error during auto-apply: {e}")
        return {"status": "error", "message": f"Auto-apply error: {e}"}
