"""Automated CV builder using RenderCV.

Produces high-quality, ATS-friendly LaTeX-based PDFs directly from our parsed 
and tailored JSON profile format.
"""
from __future__ import annotations

import os
import sys
import yaml
import subprocess
import shutil
from pathlib import Path
from typing import Any

from . import config

def build_rendercv_yaml(profile: dict[str, Any], output_path: Path, theme: str = "sb2nov") -> None:
    """Transform our standard profile dictionary into RenderCV YAML schema."""
    
    cv_data: dict[str, Any] = {
        "name": profile.get("name") or "Applicant",
    }
    
    # Optional contact info
    if profile.get("location"):
        cv_data["location"] = profile["location"]
    if profile.get("email"):
        cv_data["email"] = profile["email"]
    if profile.get("phone"):
        phone_str = str(profile["phone"]).strip()
        if not phone_str.startswith("+"):
            phone_str = "+1 " + phone_str
        cv_data["phone"] = phone_str
        
    # Handle links which can be a list or dict
    raw_links = profile.get("links", [])
    socials = []
    if isinstance(raw_links, list):
        for link in raw_links:
            if "linkedin.com" in link:
                socials.append({"network": "LinkedIn", "username": link.split("/")[-1]})
            elif "github.com" in link:
                socials.append({"network": "GitHub", "username": link.split("/")[-1]})
            else:
                socials.append({"network": "Website", "url": link})
    elif isinstance(raw_links, dict):
        if raw_links.get("linkedin"):
            socials.append({"network": "LinkedIn", "username": raw_links["linkedin"].split("/")[-1]})
        if raw_links.get("github"):
            socials.append({"network": "GitHub", "username": raw_links["github"].split("/")[-1]})
        if raw_links.get("portfolio"):
            socials.append({"network": "Website", "url": raw_links["portfolio"]})

    if socials:
        cv_data["social_networks"] = socials

    sections = {}

    # Summary
    if profile.get("summary"):
        sections["summary"] = [profile["summary"]]

    # Experience
    if profile.get("experience"):
        exp_list = []
        for exp in profile["experience"]:
            item = {
                "company": exp.get("company") or "Company",
                "position": exp.get("title") or "Position",
            }
            if exp.get("location"):
                item["location"] = exp["location"]
            
            # Date handling
            if exp.get("dates"):
                item["date"] = exp["dates"]
            elif exp.get("start") and exp.get("end"):
                item["date"] = f"{exp['start']} - {exp['end']}"
            else:
                item["date"] = "Present"
                
            # Bullets handling (support 'details' or 'bullets')
            bullets = exp.get("details") or exp.get("bullets")
            if bullets:
                item["highlights"] = bullets
                
            exp_list.append(item)
        sections["experience"] = exp_list

    # Education
    if profile.get("education"):
        edu_list = []
        for ed in profile["education"]:
            if isinstance(ed, dict):
                item = {
                    "institution": ed.get("institution") or ed.get("school") or "Institution",
                    "area": ed.get("degree") or ed.get("field") or "Degree",
                }
                if ed.get("dates"):
                    item["date"] = str(ed["dates"])
                elif ed.get("year"):
                    item["date"] = str(ed["year"])
                
                # Check for details (like GPA)
                if ed.get("details"):
                    item["highlights"] = ed["details"]
                    
                edu_list.append(item)
            else:
                edu_list.append(str(ed))
        sections["education"] = edu_list
        
    # Projects
    if profile.get("projects"):
        proj_list = []
        for pr in profile["projects"]:
            item = {
                "name": pr.get("name") or "Project",
            }
            # Add role/position if available (some themes support it)
            if pr.get("role"):
                item["position"] = pr["role"]
            
            # Bullets handling
            bullets = pr.get("details") or pr.get("bullets")
            if bullets:
                item["highlights"] = bullets
            elif pr.get("line"):
                item["highlights"] = [pr["line"]]
                
            proj_list.append(item)
        sections["projects"] = proj_list

    # Skills (RenderCV accepts skills as a list of dicts)
    if profile.get("skills"):
        skills = profile["skills"]
        # Split skills into logical chunks so it looks better
        if len(skills) > 12:
            third = len(skills) // 3
            sections["skills"] = [
                {"label": "Languages & Core", "details": ", ".join(skills[:third])},
                {"label": "Frameworks & Tools", "details": ", ".join(skills[third:2*third])},
                {"label": "Concepts & Cloud", "details": ", ".join(skills[2*third:])}
            ]
        else:
            sections["skills"] = [
                {"label": "Technical Skills", "details": ", ".join(skills)}
            ]

    # Certifications & Languages
    if profile.get("certifications"):
        sections["certifications"] = profile["certifications"]
        
    cv_data["sections"] = sections
    
    design = {
        "theme": theme
    }

    rendercv_doc = {
        "cv": cv_data,
        "design": design
    }

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(rendercv_doc, f, sort_keys=False, allow_unicode=True)


def generate_cv_pdf(job: dict[str, Any], profile: dict[str, Any], theme: str = "classic") -> str | None:
    """Generate a PDF using RenderCV based on the tailored profile.
    
    Returns the absolute path to the generated PDF.
    """
    import re
    def slugify(text: str) -> str:
        s = re.sub(r"[^A-Za-z0-9]+", "_", (text or "").strip()).strip("_")
        return (s or "untitled")[:50]
        
    base_name = f"{slugify(job.get('company',''))}_{slugify(job.get('title',''))}_CV"
    
    # We will generate this in a temporary subdirectory inside outputs to keep it clean,
    # then move the PDF out.
    work_dir = config.OUTPUTS_DIR / "rendercv_build"
    work_dir.mkdir(parents=True, exist_ok=True)
    
    yaml_path = work_dir / f"{base_name}.yaml"
    build_rendercv_yaml(profile, yaml_path, theme=theme)
    
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    
    # Call RenderCV CLI via subprocess
    try:
        subprocess.run(
            [sys.executable, "-m", "rendercv", "render", str(yaml_path)],
            cwd=str(work_dir),
            env=env,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
    except subprocess.CalledProcessError as e:
        print(f"RenderCV Failed:\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}")
        return None
        
    # Find the resulting PDF in the output folder created by RenderCV
    rcv_output_dir = work_dir / "rendercv_output"
    generated_pdf = None
    if rcv_output_dir.exists():
        for file in rcv_output_dir.glob("*.pdf"):
            generated_pdf = file
            break
            
    if generated_pdf:
        final_pdf_path = config.OUTPUTS_DIR / f"{base_name}.pdf"
        shutil.copy2(generated_pdf, final_pdf_path)
        # Cleanup
        shutil.rmtree(work_dir, ignore_errors=True)
        return str(final_pdf_path)
        
    return None
