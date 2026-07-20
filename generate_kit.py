import sys
import json
import asyncio

sys.path.insert(0, r"d:\Ai job finder")
from src.tailor import cover_letter
from src.outreach import draft_email

async def main():
    with open('data/profiles/default.json', encoding='utf-8') as f:
        profile = json.load(f)
        
    # Fix the links issue to avoid AttributeError
    profile["links"] = {}
        
    job_description = """
    Company: ApplyPilot
    Role: Founding Generalist, Ops and Success
    Location: Ahmedabad, India (with an option for remote work)
    Compensation: ₹4 Lakhs – ₹5 Lakhs per year
    
    Responsibilities:
    - Serving as a dedicated success manager for early-cohort "Ultra" plan users.
    - Managing the end-to-end user journey, including onboarding, activation, weekly check-ins, and tracking interview milestones.
    - Ensuring every user successfully reaches the goal of 3 interviews within 30 days.
    - Building and refining the playbooks required to scale these operations.
    
    About Us:
    ApplyPilot is an AI job-search assistant that scans platforms like LinkedIn, Indeed, Naukri, and Glassdoor to build application kits, find hiring manager emails, and automate personalized cold outreach for candidates.
    """
    
    job = {
        "company": "ApplyPilot",
        "title": "Founding Generalist, Ops and Success",
        "description": job_description
    }
    
    contact = {
        "name": "Hiring Manager",
        "company": "ApplyPilot",
        "email": "hr@applypilot.com"
    }
    
    prefs = {"identity": {"name": profile.get("name", "Animesh Shukla")}}
    
    print("Generating Cover Letter...")
    cl = await cover_letter(job, profile, prefs)
    
    print("Generating Cold Email...")
    email = await draft_email(contact, job, profile, prefs)
    
    with open(r"C:\Users\shukl\.gemini\antigravity\brain\4f284bb6-4245-480f-be3e-c929bc9cb7bd\applypilot_application_kit.md", "w", encoding="utf-8") as f:
        f.write("# ApplyPilot - Application Kit\n\n")
        f.write("## Customized Cover Letter\n\n")
        f.write(cl + "\n\n")
        f.write("---\n\n")
        f.write("## Cold Outreach Email\n\n")
        if hasattr(email, 'subject'):
            f.write(f"**Subject:** {email.subject}\n\n")
            f.write(f"**To:** {email.to_address}\n\n")
            f.write(email.body + "\n\n")
        else:
            f.write(str(email) + "\n\n")

if __name__ == "__main__":
    asyncio.run(main())
