"""Standalone browser process for REVIEW-FIRST application auto-fill.

Run as:  python -m src.autofill_runner <path-to-config.json>
"""
from __future__ import annotations

import json
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
    if "cover" in k and any(w in k for w in ("letter", "note", "message", "statement", "additional")):
        return cfg.get("cover_letter", "")
    if any(w in k for w in ("years of experience", "experience years", "experience_years", "yoe")):
        return str(cfg.get("years_experience") or cfg.get("experience_years") or "")
    if "experience" in k and any(w in k for w in ("year", "how many", "total")):
        return str(cfg.get("years_experience") or cfg.get("experience_years") or "")
    if "name" in k and "user" not in k and "file" not in k:
        return cfg.get("full_name", "")
    custom_map = cfg.get("custom_answers") or {}
    for ckey, cval in custom_map.items():
        if ckey.lower() in k:
            return str(cval)
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

_SELECT_OPTION_CAP = 12  # options shown to the LLM per <select> (prompt economy)


def _select_options(el, limit: int = _SELECT_OPTION_CAP) -> list[str]:
    """Real option labels for a <select>, so the LLM picks values that exist."""
    try:
        if (el.evaluate("el => el.tagName") or "").lower() != "select":
            return []
        opts = el.evaluate(
            "el => Array.from(el.options).map(o => (o.label || o.value).trim()).filter(Boolean)"
        )
        return [o for o in opts if o][:limit]
    except Exception:
        return []


def _bulk_llm_fallback(frame, cfg: dict, unfilled_elements: list, fill_log: list | None = None) -> int:
    """LLM form mapping using an INDEXED element manifest.

    Technique adopted from the browser-use agent family (indexed interactive
    element list -> model acts by index): the model returns {"i": <index>,
    "value": ...} against a numbered manifest instead of inventing selectors.
    Fewer hallucinated targets, smaller prompts, and <select> elements ship
    their real option labels so chosen values actually exist.
    """
    if not unfilled_elements:
        return 0

    from src import llm
    from src.profile_parser import profile_context
    ctx = profile_context(cfg.get("profile", {}))

    filled_count = 0
    # Batch into chunks of 25 to prevent context overflow
    chunk_size = 25
    for i in range(0, len(unfilled_elements), chunk_size):
        chunk = unfilled_elements[i:i + chunk_size]
        manifest = []
        for idx, e in enumerate(chunk):
            entry = {"i": idx, "label": (e.get("label") or "")[:120], "type": e.get("type")}
            if e.get("options"):
                entry["options"] = e["options"]
            manifest.append(entry)

        prompt = (
            "Map the candidate's profile onto this numbered list of form fields.\n"
            "Return a JSON array: [{\"i\": <index>, \"value\": <string|boolean>}].\n"
            "Rules:\n"
            "- For radio/checkbox fields output the boolean true/false.\n"
            "- For fields with an 'options' list, value MUST be one of those exact option strings.\n"
            "- For open questions answer in one short sentence using ONLY the candidate's real background.\n"
            "- Never invent employers, dates, or credentials. If a field does not apply, omit it.\n\n"
            f"FIELDS: {json.dumps(manifest, indent=1)}\n\n"
            f"PROFILE CONTEXT:\n{ctx}"
        )

        try:
            mapping = llm.generate_json(
                prompt,
                system=(
                    "You are a precise form-autofill engine. Return ONLY a JSON array of "
                    "{\"i\": index, \"value\": value} objects. Never return selectors."
                ),
                temperature=0.1
            )
            actions = mapping if isinstance(mapping, list) else []
            for act in actions:
                try:
                    if not isinstance(act, dict) or "i" not in act:
                        continue
                    pos = int(act["i"])
                    if not (0 <= pos < len(chunk)):
                        continue
                    el_dict = chunk[pos]
                    val = act.get("value")
                    if val is None:
                        continue
                    locator = frame.locator(el_dict["selector"]).first
                    tag = el_dict["type"]
                    if tag in ("radio", "checkbox"):
                        if str(val).lower() == "true":
                            locator.check()
                    elif tag == "select":
                        try:
                            locator.select_option(label=str(val))
                        except Exception:
                            locator.select_option(value=str(val))
                    else:
                        text = str(val)
                        if len(text) > 500:  # cap runaway generations
                            text = text[:500]
                        locator.fill(text)
                    filled_count += 1
                    if fill_log is not None:
                        fill_log.append({
                            "label": el_dict.get("label") or el_dict.get("id_key") or "",
                            "value": str(val)[:200],
                            "via": "llm",
                        })
                except Exception:
                    continue
        except Exception as e:
            print(f"Bulk LLM chunk {i} failed: {e}")

    return filled_count

def _fill_page(page, cfg: dict, fill_log: list | None = None) -> int:
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
                        if fill_log is not None:
                            fill_log.append({"label": lbl or "resume upload", "value": "resume.pdf", "via": "upload"})
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
                    if fill_log is not None:
                        fill_log.append({"label": label_text or key[:60], "value": str(value)[:200], "via": "profile"})
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
                            "type": itype,
                            "options": _select_options(el),
                        })
            except Exception:
                pass
                
        if unfilled:
            filled += _bulk_llm_fallback(frame, cfg, unfilled, fill_log)

    return filled

def _paginate_and_fill(page, cfg: dict, fill_log: list | None = None) -> int:
    """The End-to-End Hunter: Fills current page, finds 'Next', and repeats."""
    total_filled = 0
    max_pages = 8 # Prevent infinite loops

    for page_num in range(max_pages):
        print(f"Filling Page {page_num + 1}...")
        total_filled += _fill_page(page, cfg, fill_log)
        
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

def _write_fill_report(page, cfg: dict, fill_log: list) -> str:
    """Save a review-first verification pack: full-page screenshot + fill log.

    The user reviews THIS before touching the real Submit button — the whole
    point of the review-first principle, made visible.
    """
    try:
        from src import config as _config

        out_dir = _config.OUTPUTS_DIR / "apply_previews"
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        slug = re.sub(r"[^a-z0-9]+", "-", (cfg.get("job_company") or "application").lower()).strip("-")[:40] or "application"
        base = out_dir / f"{slug}-{stamp}"

        png_path = f"{base}.png"
        try:
            page.screenshot(path=png_path, full_page=True, timeout=15000)
        except Exception as e:
            print(f"Screenshot skipped: {e}")
            png_path = ""

        report = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "apply_url": cfg.get("apply_url"),
            "job_title": cfg.get("job_title"),
            "job_company": cfg.get("job_company"),
            "fields_filled": fill_log,
            "screenshot": png_path,
            "reminder": "REVIEW-FIRST: nothing was submitted. Verify every field, then submit yourself.",
        }
        json_path = f"{base}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Fill report saved: {json_path}" + (" (+ screenshot)" if png_path else ""))
        return json_path
    except Exception as e:
        print(f"Fill report skipped: {e}")
        return ""

def run(cfg: dict) -> None:
    from contextlib import ExitStack

    from src.stealth_browser import launch_sync

    with ExitStack() as stack:
        # Stealth-first: Camoufox (humanized cursor, rotated fingerprint) with a
        # transparent fallback to Chromium. Each engine keeps its OWN profile dir
        # (stealth_browser appends "-camoufox") to avoid cross-engine corruption.
        fill_log: list = []
        try:
            ctx = stack.enter_context(launch_sync(
                headless=False,
                user_data_dir=cfg["user_data_dir"],
                humanize=True,
            ))
        except Exception as e:
            print(f"Persistent profile locked or unavailable ({e}); using an ephemeral session instead.")
            ctx = stack.enter_context(launch_sync(headless=False))

        page = ctx.pages[0] if getattr(ctx, "pages", None) else ctx.new_page()
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
                        _paginate_and_fill(page, cfg, fill_log)
                except ImportError:
                    _paginate_and_fill(page, cfg, fill_log)
                print("Pre-filled all pages. REVIEW EVERYTHING, then submit yourself.")
            except Exception as e:
                print(f"Auto-fill hit an issue: {e}")

        # Review-first verification pack: screenshot + exactly-what-was-filled log.
        _write_fill_report(page, cfg, fill_log)

        print(">>> Review and submit in the browser. Close the window when you're done. <<<")
        try:
            holder = page.context  # works for both Context- and Browser-shaped handles
            while len(holder.pages) > 0:
                time.sleep(0.5)
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
