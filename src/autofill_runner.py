"""Standalone browser process for REVIEW-FIRST application auto-fill.

Run as:  python -m src.autofill_runner <path-to-config.json>

It opens a real, visible Chromium window, best-effort fills the obvious fields and
uploads the resume, then waits while YOU review and click Submit. It NEVER submits and
NEVER closes the form for you. Closing the window ends the process.

Kept deliberately separate from Streamlit so Playwright's sync API runs in its own
process (no event-loop conflicts).
"""
from __future__ import annotations

import json
import sys
import time


def _match_value(key: str, cfg: dict) -> str:
    """Map a field's name/id/placeholder/label text to a value to fill."""
    k = key.lower()
    # Never touch these.
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
    if "cover" in k or "why do you want" in k or "message" in k:
        return cfg.get("cover_letter", "")
    if "name" in k and "user" not in k and "file" not in k:
        return cfg.get("full_name", "")
    return ""


def _get_element_label(page, el) -> str:
    """Finds associated label text for an input/textarea element."""
    try:
        eid = el.get_attribute("id")
        if eid:
            lbl = page.query_selector(f"label[for='{eid}']")
            if lbl:
                return lbl.inner_text().strip()
    except Exception:
        pass
    
    # Try parent label
    try:
        parent = el.query_selector("xpath=ancestor::label")
        if parent:
            return parent.inner_text().strip()
    except Exception:
        pass
        
    placeholder = el.get_attribute("placeholder")
    if placeholder:
        return placeholder.strip()
        
    aria = el.get_attribute("aria-label")
    if aria:
        return aria.strip()
        
    name = el.get_attribute("name")
    if name:
        return name.strip()
        
    return ""


def _generate_answer_to_question(question_text: str, cfg: dict) -> str:
    """Uses LLM to write a custom, brief response to an application form question."""
    import httpx
    
    provider = cfg.get("provider", "claude")
    anthropic_key = cfg.get("anthropic_api_key", "")
    gemini_key = cfg.get("gemini_api_key", "")
    model = cfg.get("writing_model", "claude-sonnet-4-6")
    if provider == "gemini":
        model = cfg.get("gemini_model", "gemini-2.0-flash")

    # Construct resume context
    from src.profile_parser import profile_context
    profile = cfg.get("profile", {})
    ctx = profile_context(profile)

    prompt = (
        f"You are applying to the following job:\n"
        f"Title: {cfg.get('job_title', '')}\n"
        f"Company: {cfg.get('job_company', '')}\n"
        f"Description: {cfg.get('job_description', '')[:1200]}\n\n"
        f"Answer this application form question truthfully using ONLY details from the candidate profile.\n"
        f"Keep the answer concise (under 120 words), writing in the first-person ('I'). Do not exaggerate.\n\n"
        f"QUESTION: {question_text}\n"
        f"ANSWER:"
    )

    try:
        if provider == "gemini" and gemini_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            headers = {
                "x-goog-api-key": gemini_key,
                "content-type": "application/json"
            }
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": f"SYSTEM INSTRUCTION: You answer application questions truthfully based on the candidate's profile context:\n{ctx}\n\nUSER PROMPT:\n{prompt}"}
                        ]
                    }
                ],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 300}
            }
            resp = httpx.post(url, json=payload, headers=headers, timeout=20.0)
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        elif provider == "claude" and anthropic_key:
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": anthropic_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            payload = {
                "model": model,
                "max_tokens": 300,
                "system": f"You answer application questions truthfully based on the candidate's profile context:\n{ctx}",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
            resp = httpx.post(url, json=payload, headers=headers, timeout=20.0)
            if resp.status_code == 200:
                data = resp.json()
                return "".join(b["text"] for b in data["content"] if b["type"] == "text").strip()
    except Exception as e:
        print(f"Error calling LLM for custom question: {e}")
    return ""


def _fill(page, cfg: dict) -> int:
    filled = 0
    
    # Gather all frames (including main page and iframes like Greenhouse/Lever)
    frames = [page.main_frame] + page.main_frame.child_frames

    for frame in frames:
        # 1) Resume upload — set every file input we can find.
        if cfg.get("resume_path"):
            for inp in frame.query_selector_all("input[type=file]"):
                try:
                    inp.set_input_files(cfg["resume_path"])
                    filled += 1
                except Exception:
                    pass

        # 2) Text inputs / textareas by heuristic.
        for el in frame.query_selector_all("input, textarea"):
            try:
                itype = (el.get_attribute("type") or "text").lower()
                if itype in ("hidden", "file", "checkbox", "radio", "submit", "button", "password", "search"):
                    continue
                if not el.is_visible():
                    continue
                key = " ".join(filter(None, [
                    el.get_attribute("name"), el.get_attribute("id"),
                    el.get_attribute("placeholder"), el.get_attribute("aria-label"),
                ]))
                value = _match_value(key, cfg)
                
                # Get label text for diagnostic or LLM custom questions
                label_text = _get_element_label(frame, el)
                
                if value:
                    el.fill(value)
                    filled += 1
                else:
                    # If we don't have a heuristic match, check if it's a qualitative question
                    tag_name = el.evaluate("el => el.tagName").lower()
                    if tag_name == "textarea" or (tag_name == "input" and len(label_text) > 20):
                        # Skip if already prefilled/not empty
                        current_val = el.input_value()
                        if not current_val.strip() and label_text:
                            ai_answer = _generate_answer_to_question(label_text, cfg)
                            if ai_answer:
                                el.fill(ai_answer)
                                filled += 1
            except Exception:
                pass
                
    return filled



def run(cfg: dict) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            cfg["user_data_dir"], headless=False, accept_downloads=True,
            viewport={"width": 1300, "height": 920},
            args=["--start-maximized"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            page.goto(cfg["apply_url"], wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"Could not open the page: {e}")

        if cfg.get("gated"):
            print("This is a login-gated site (e.g. LinkedIn). Not auto-filling — "
                  "use your own logged-in session and the answer sheet to paste details.")
        else:
            try:
                n = _fill(page, cfg)
                print(f"Pre-filled {n} field(s). REVIEW EVERYTHING, then submit yourself.")
            except Exception as e:
                print(f"Auto-fill hit an issue (form may be unusual): {e}")

        print(">>> Review and submit in the browser. Close the window when you're done. <<<")
        # Stay alive until the user closes the browser window.
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
    import os
    if len(sys.argv) < 2:
        print("usage: python -m src.autofill_runner <config.json>")
        sys.exit(2)
    cfg_file = sys.argv[1]
    try:
        with open(cfg_file, "r", encoding="utf-8") as fh:
            cfg = json.load(fh)
    finally:
        try:
            if os.path.exists(cfg_file):
                os.remove(cfg_file)
        except Exception:
            pass
    run(cfg)
