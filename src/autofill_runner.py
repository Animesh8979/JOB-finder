"""Standalone browser process for REVIEW-FIRST application auto-fill.

Run as:  python -m src.autofill_runner <path-to-config.json>
"""
from __future__ import annotations

import json
import os
import sys
import time
import re

def _clean_json(text: str) -> str:
    """Strips markdown code blocks from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text)
        text = re.sub(r"```$", "", text)
    return text.strip()

def _match_value(key: str, cfg: dict) -> str:
    """Map a field's name/id/placeholder/label text to a value to fill locally."""
    k = key.lower()
    if any(bad in k for bad in ("company", "search", "coupon", "how did you hear",
                                "password", "salary", "captcha", "referral code")):
        return ""
    if "first" in k and "name" in k:
        return cfg.get("first_name", "")
    if ("last" in k or "surname" in k or "family" in k) and "name" in k:
        return cfg.get("last_name", "")
    if "linkedin" in k:
        return cfg.get("linkedin", "")
    if "github" in k:
        return cfg.get("github", "")
    if any(w in k for w in ("portfolio", "website", "personal url", "your url")):
        return cfg.get("website", "") or cfg.get("linkedin", "")
    if "email" in k:
        return cfg.get("email", "")
    if any(w in k for w in ("phone", "mobile", "tel")):
        return cfg.get("phone", "")
    if any(w in k for w in ("city", "location", "where are you", "current location")):
        return cfg.get("location", "")
    if "name" in k and "user" not in k and "file" not in k:
        return cfg.get("full_name", "")
    return ""

def _get_element_label(frame, el) -> str:
    """Finds associated label text for an input/textarea element."""
    try:
        eid = el.get_attribute("id")
        if eid:
            # Safely escape ID
            lbl = frame.query_selector(f"label[for='{eid}']")
            if lbl:
                return lbl.inner_text().strip()
    except Exception:
        pass
    try:
        parent = el.query_selector("xpath=ancestor::label")
        if parent:
            return parent.inner_text().strip()
    except Exception:
        pass
    placeholder = el.get_attribute("placeholder")
    if placeholder: return placeholder.strip()
    aria = el.get_attribute("aria-label")
    if aria: return aria.strip()
    name = el.get_attribute("name")
    if name: return name.strip()
    return ""

def _bulk_llm_fallback(frame, cfg: dict, unfilled_elements: list) -> int:
    """Uses Gemini to bulk-map candidate profile data to unknown form fields, with retries and batching."""
    import httpx
    # Read the key from the inherited environment (set by autofill.py), NOT the cfg dict.
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key or not unfilled_elements:
        return 0

    filled_count = 0
    from src.profile_parser import profile_context
    ctx = profile_context(cfg.get("profile", {}))

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {"x-goog-api-key": gemini_key, "content-type": "application/json"}

    # Batch into chunks of 30 to prevent context overflow
    chunk_size = 30
    for i in range(0, len(unfilled_elements), chunk_size):
        chunk = unfilled_elements[i:i + chunk_size]
        schema_list = [{"element_id": e["id_key"], "label": e["label"], "type": e["type"]} for e in chunk]

        prompt = (
            f"Map the candidate's profile to these form fields. Return a clean JSON dictionary where keys are 'element_id'.\n"
            f"If 'type' is 'radio' or 'checkbox', output the boolean literal true or false.\n"
            f"If it's a question, generate a brief (1 sentence) answer. If it doesn't apply, omit it entirely.\n"
            f"FIELDS: {json.dumps(schema_list, indent=2)}\n\n"
            f"PROFILE CONTEXT:\n{ctx}"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
        }

        # Retry loop
        for attempt in range(3):
            try:
                resp = httpx.post(url, json=payload, headers=headers, timeout=25.0)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_json = data["candidates"][0]["content"]["parts"][0]["text"]
                    mapping = json.loads(_clean_json(raw_json))
                    
                    for el_dict in chunk:
                        eid = el_dict["id_key"]
                        if eid in mapping and mapping[eid] is not None:
                            try:
                                locator = frame.locator(el_dict["selector"]).first
                                tag = el_dict["type"]
                                val = mapping[eid]
                                
                                if tag in ("radio", "checkbox"):
                                    if str(val).lower() == "true": locator.check()
                                elif tag == "select":
                                    try: locator.select_option(label=str(val))
                                    except: locator.select_option(value=str(val))
                                else:
                                    locator.fill(str(val))
                                filled_count += 1
                            except Exception:
                                pass
                    break # Success, break retry loop
            except Exception as e:
                if attempt == 2: print(f"Bulk LLM chunk {i} failed after 3 retries: {e}")
                time.sleep(2)

    return filled_count

def _fill_page(page, cfg: dict) -> int:
    filled = 0
    frames = [page.main_frame] + page.main_frame.child_frames

    for frame in frames:
        # 1. Multi-File Upload Fix: Target resume specifically
        if cfg.get("resume_path"):
            # Only upload if the label implies resume/cv
            for inp in frame.locator('*css=input[type="file"]').all():
                try:
                    lbl = _get_element_label(frame, inp).lower()
                    if "resume" in lbl or "cv" in lbl or "upload" in lbl:
                        inp.set_input_files(cfg["resume_path"])
                        filled += 1
                except Exception:
                    pass

        # 2. Text & Radio Inputs via Shadow-piercing locator
        unfilled = []
        elements = frame.locator('*css=input, textarea, select, [role="textbox"], [role="combobox"], [contenteditable="true"]').all()
        for el in elements:
            try:
                tag = el.evaluate("el => el.tagName").lower()
                itype = (el.get_attribute("type") or "text").lower() if tag == "input" else tag
                if itype in ("hidden", "file", "submit", "button", "password", "search"):
                    continue
                
                # Invisible bounding box fix
                box = el.bounding_box()
                if not box or box["width"] == 0 or box["height"] == 0:
                    continue

                key = " ".join(filter(None, [
                    el.get_attribute("name"), el.get_attribute("id"),
                    el.get_attribute("placeholder"), el.get_attribute("aria-label"),
                ]))
                value = _match_value(key, cfg)
                label_text = _get_element_label(frame, el)
                
                if value and itype not in ("radio", "checkbox"):
                    if tag == "select":
                        try: el.select_option(label=value)
                        except: el.select_option(value=value)
                    else:
                        el.fill(value)
                    filled += 1
                else:
                    current_val = ""
                    if itype not in ("radio", "checkbox"):
                        current_val = el.input_value()
                    
                    if not current_val.strip() and not el.is_checked():
                        eid = el.get_attribute("id")
                        ename = el.get_attribute("name")
                        
                        # Generate ultra-safe CSS selector
                        if eid:
                            selector = f"[id='{eid}']"
                        elif ename:
                            selector = f"[name='{ename}']"
                        else:
                            idx = len(unfilled)
                            el.evaluate("(e, i) => e.setAttribute('data-ai-fallback', i)", str(idx))
                            selector = f"[data-ai-fallback='{idx}']"
                            
                        unfilled.append({
                            "selector": selector,
                            "id_key": eid or ename or selector,
                            "label": label_text,
                            "type": itype
                        })
            except Exception:
                pass
                
        if unfilled:
            filled += _bulk_llm_fallback(frame, cfg, unfilled)
            
    return filled

def _paginate_and_fill(page, cfg: dict) -> int:
    """The End-to-End Hunter: Fills current page, finds 'Next', and repeats."""
    total_filled = 0
    max_pages = 8 # Prevent infinite loops
    
    for page_num in range(max_pages):
        print(f"Filling Page {page_num + 1}...")
        total_filled += _fill_page(page, cfg)
        
        # Hunt for a Next/Continue button
        next_btn = None
        for frame in [page.main_frame] + page.main_frame.child_frames:
            try:
                # Look for common submit/next buttons
                btns = frame.locator('*css=button, input[type="submit"], input[type="button"], a[role="button"]').all()
                for btn in btns:
                    if btn.is_visible():
                        text = btn.inner_text().strip().lower() or btn.get_attribute("value").strip().lower()
                        if text in ("next", "continue", "save and continue", "next step"):
                            next_btn = btn
                            break
            except Exception:
                pass
            if next_btn: break
            
        if next_btn:
            print("Found 'Next' button, advancing to next page...")
            try:
                next_btn.click()
                page.wait_for_timeout(3000) # Give SPA time to render next page
            except Exception:
                break
        else:
            print("Reached the end of the application (no 'Next' button found).")
            break
            
    return total_filled

def run(cfg: dict) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        # Context locking & Stealth flags
        args = ["--start-maximized", "--disable-blink-features=AutomationControlled"]
        try:
            ctx = p.chromium.launch_persistent_context(
                cfg["user_data_dir"], headless=False, accept_downloads=True,
                viewport={"width": 1300, "height": 920}, args=args,
            )
        except Exception as e:
            print(f"Persistent context locked, falling back to ephemeral incognito context: {e}")
            browser = p.chromium.launch(headless=False, args=args)
            ctx = browser.new_context(viewport={"width": 1300, "height": 920})
            
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            # Dropped networkidle for domcontentloaded to prevent 60s timeout hangs
            page.goto(cfg["apply_url"], wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000) # Give SPA time to hydrate
        except Exception as e:
            print(f"Could not fully load the page (continuing anyway): {e}")

        if cfg.get("gated"):
            print("This is a login-gated site. Use your own logged-in session and the answer sheet.")
        else:
            try:
                # Prefer the specialized ATS engine when the apply host matches.
                try:
                    from src.ats_engines import fill_with_engine
                    used, msg = fill_with_engine(page, cfg["apply_url"], cfg)
                    print(msg)
                    if not used:
                        _paginate_and_fill(page, cfg)
                except ImportError:
                    _paginate_and_fill(page, cfg)
                print("Pre-filled all pages. REVIEW EVERYTHING, then submit yourself.")
            except Exception as e:
                print(f"Auto-fill hit an issue: {e}")

        print(">>> Review and submit in the browser. Close the window when you're done. <<<")
        try:
            while len(ctx.pages) > 0:
                time.sleep(0.5)
        except Exception:
            pass
        try:
            ctx.close()
        except Exception:
            pass

if __name__ == "__main__":
    try:
        cfg_data = sys.stdin.read()
        cfg = json.loads(cfg_data)
    except Exception as e:
        print(f"Error parsing config: {e}")
        sys.exit(2)
    run(cfg)
