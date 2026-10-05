"""High-Fidelity ATS PDF Generator leveraging Playwright headless Chromium.

Inspired by career-ops generate-pdf.mjs:
- Renders semantic HTML5 + Space Grotesk / DM Sans typography.
- Compiles pixel-perfect vector text with exact A4/Letter margins.
- Gracefully falls back to fpdf2/python-docx if Playwright is unavailable.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any
import jinja2

from . import config


def render_html_resume(resume_dict: dict[str, Any], template_name: str = "resume_modern.html") -> str:
    """Render resume dictionary into semantic HTML using Jinja2."""
    template_dir = Path(__file__).resolve().parent.parent / "templates"
    if not template_dir.exists():
        template_dir.mkdir(parents=True, exist_ok=True)
        
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_dir)),
        autoescape=jinja2.select_autoescape(["html", "xml"])
    )
    
    template = env.get_template(template_name)
    return template.render(resume=resume_dict)


def generate_modern_pdf(
    resume_dict: dict[str, Any],
    output_path: Path | str,
    template_name: str = "resume_modern.html"
) -> Path:
    """Compile HTML resume to vector PDF via Playwright, falling back to fpdf2 if needed."""
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    html_content = render_html_resume(resume_dict, template_name=template_name)
    temp_html_path = output_path.with_suffix(".temp.html")
    temp_html_path.write_text(html_content, encoding="utf-8")

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"file:///{temp_html_path.as_posix()}", wait_until="networkidle", timeout=15000)
            
            page.pdf(
                path=str(output_path),
                format="A4",
                print_background=True,
                margin={"top": "12mm", "bottom": "12mm", "left": "14mm", "right": "14mm"}
            )
            browser.close()
    except Exception as e:
        # Fallback to fpdf2 / documents.py
        from . import documents
        documents.save_resume_pdf(resume_dict, output_path)
    finally:
        if temp_html_path.exists():
            try:
                temp_html_path.unlink()
            except OSError:
                pass

    return output_path
