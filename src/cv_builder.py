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
from .anti_slop import audit_and_sanitize, sanitize_bullet

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
        sections["summary"] = [audit_and_sanitize(profile["summary"]).cleaned_text]

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
                item["highlights"] = [sanitize_bullet(b) for b in bullets if b]
                
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
                item["highlights"] = [sanitize_bullet(b) for b in bullets if b]
            elif pr.get("line"):
                item["highlights"] = [sanitize_bullet(pr["line"])]
                
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


def render_typst_direct(typst_source: str, output_pdf_path: str | Path) -> str | None:
    """Compile Typst document directly to vector PDF using in-process Python bindings.

    Guarantees zero-dependency vector PDF generation with zero external CLI subprocesses.
    Produces high-fidelity, linear Type-1/TrueType streams optimized for ATS parsing.
    """
    import tempfile
    try:
        import typst
    except ImportError:
        print("[cv_builder] typst package not installed for direct compilation")
        return None

    out_p = Path(output_pdf_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    # Sanitize em-dashes and artificial punctuation from Typst source
    clean_source = typst_source.replace("—", ", ").replace(" -- ", ", ")
    import re
    # Escape @ (prevents invalid label reference) and $ (prevents math mode crash) in raw text
    clean_source = re.sub(r'(?<!\\)@', r'\\@', clean_source)
    clean_source = re.sub(r'(?<!\\)\$', r'\\$', clean_source)

    with tempfile.NamedTemporaryFile("w", suffix=".typ", delete=False, encoding="utf-8") as f:
        f.write(clean_source)
        temp_typ = f.name

    try:
        typst.compile(temp_typ, output=str(out_p))
        if out_p.exists() and out_p.stat().st_size > 0:
            return str(out_p)
    except Exception as e:
        print(f"[cv_builder] Typst compilation failed: {e}")
    finally:
        if os.path.exists(temp_typ):
            try:
                os.remove(temp_typ)
            except Exception:
                pass
    return None


def build_typst_resume(profile: dict[str, Any]) -> str:
    """Generate clean, ATS-compliant Typst markup from profile data.
    
    Guarantees 0 em-dashes, clear typographic hierarchy, and dense ATS-friendly text flow.
    """
    name = (profile.get("name") or "Applicant").strip()
    headline = (profile.get("headline") or "").strip()
    email = (profile.get("email") or "").strip()
    phone = (profile.get("phone") or "").strip()
    location = (profile.get("location") or "").strip()
    
    raw_links = profile.get("links") or {}
    linkedin = ""
    github = ""
    if isinstance(raw_links, dict):
        linkedin = raw_links.get("linkedin", "")
        github = raw_links.get("github", "")
    elif isinstance(raw_links, list):
        for link_item in raw_links:
            if "linkedin.com" in link_item:
                linkedin = link_item
            elif "github.com" in link_item:
                github = link_item

    contacts = [c for c in [email, phone, location, linkedin, github] if c]
    contact_str = " | ".join(contacts)

    lines = [
        '#set page(paper: "a4", margin: (x: 1.5cm, top: 1.2cm, bottom: 1.2cm))',
        '#set text(font: "Liberation Sans", size: 9.5pt)',
        '#set par(justify: true, leading: 0.55em)',
        '',
        '#align(center)[',
        f'  #text(size: 16pt, weight: "bold")[{name}] \\',
    ]
    if headline:
        lines.append(f'  #text(size: 10pt, weight: "medium")[{headline}] \\')
    if contact_str:
        lines.append(f'  #text(size: 8.5pt)[{contact_str}]')
    lines.extend([
        ']',
        '#v(4pt)',
        '#line(length: 100%, stroke: 0.5pt + luma(120))',
        '#v(2pt)',
    ])

    # Summary
    summary = profile.get("summary") or ""
    if summary:
        clean_sum = audit_and_sanitize(summary).cleaned_text.replace('"', '\\"')
        lines.extend([
            '== Professional Summary',
            f'{clean_sum}',
            '#v(4pt)',
        ])

    # Skills
    skills = profile.get("skills") or []
    if skills:
        skills_str = ", ".join(skills).replace('"', '\\"')
        lines.extend([
            '== Core Technical Skills',
            f'#text(weight: "bold")[Technical Proficiencies:] {skills_str}',
            '#v(4pt)',
        ])

    # Experience
    experience = profile.get("experience") or []
    if experience:
        lines.append('== Professional Experience')
        for exp in experience:
            title = exp.get("title") or exp.get("position") or "Role"
            company = exp.get("company") or "Company"
            loc = exp.get("location") or ""
            dates = exp.get("dates") or (f"{exp.get('start','')} - {exp.get('end','')}".strip(" - ")) or "Present"
            
            header_right = f"{loc} | {dates}" if loc else dates
            lines.append(f'*#text(weight: "bold")[{title}]* at *{company}* #h(1fr) #text(style: "italic")[{header_right}]')
            
            bullets = exp.get("bullets") or exp.get("details") or []
            for b in bullets:
                clean_b = sanitize_bullet(b).replace('"', '\\"')
                if clean_b:
                    lines.append(f'- {clean_b}')
            lines.append('#v(2pt)')
        lines.append('#v(2pt)')

    # Projects
    projects = profile.get("projects") or []
    if projects:
        lines.append('== Technical Projects')
        for pr in projects:
            pname = pr.get("name") or "Project"
            tech = pr.get("tech") or []
            tech_str = f" [{', '.join(tech)}]" if tech else ""
            lines.append(f'*#text(weight: "bold")[{pname}]*{tech_str}')
            
            pbullets = pr.get("bullets") or pr.get("details") or []
            if not pbullets and pr.get("description"):
                pbullets = [pr["description"]]
            elif not pbullets and pr.get("line"):
                pbullets = [pr["line"]]
                
            for b in pbullets:
                clean_b = sanitize_bullet(b).replace('"', '\\"')
                if clean_b:
                    lines.append(f'- {clean_b}')
            lines.append('#v(2pt)')
        lines.append('#v(2pt)')

    # Education
    education = profile.get("education") or []
    if education:
        lines.append('== Education')
        for ed in education:
            if isinstance(ed, dict):
                degree = ed.get("degree") or ed.get("field") or "Degree"
                inst = ed.get("institution") or ed.get("school") or "University"
                yr = ed.get("year") or ed.get("dates") or ""
                lines.append(f'*{degree}* - {inst} #h(1fr) #text(style: "italic")[{yr}]')
            else:
                lines.append(f'- {str(ed)}')
        lines.append('#v(2pt)')

    # Certifications
    certs = profile.get("certifications") or []
    if certs:
        lines.append('== Certifications')
        for c in certs:
            lines.append(f'- {c}')

    return "\n".join(lines)


def generate_typst_cv(profile: dict[str, Any], output_pdf_path: str | Path) -> str | None:
    """Generate and compile a vector PDF using in-process Typst."""
    source = build_typst_resume(profile)
    return render_typst_direct(source, output_pdf_path)

