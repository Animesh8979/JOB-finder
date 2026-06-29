"""Proxycurl client to automatically find recruiter contacts for a hiring company."""
from __future__ import annotations

import httpx
from typing import Any
from . import config, db

PROXYCURL_BASE_URL = "https://nubela.co/proxycurl/api"

def get_proxycurl_key() -> str:
    return config.get_secret("proxycurl_api_key", "PROXYCURL_API_KEY")

def enrich_recruiter_contacts(company_name: str, job_id: int) -> list[dict[str, Any]]:
    """Resolve company, find recruiter employees, and save them in the contacts DB."""
    api_key = get_proxycurl_key()
    if not api_key:
        raise ValueError("Proxycurl API key not configured. Add it in the Setup page.")

    headers = {"Authorization": f"Bearer {api_key}"}
    
    # Step 1: Resolve Company Name to LinkedIn Company URL
    resolve_url = f"{PROXYCURL_BASE_URL}/linkedin/company/resolve"
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(resolve_url, headers=headers, params={"company_name": company_name})
            if resp.status_code != 200:
                raise RuntimeError(f"Proxycurl resolve error: {resp.text}")
            company_url = resp.json().get("url")
            if not company_url:
                raise RuntimeError(f"Could not resolve company URL for '{company_name}'")
    except Exception as e:
        raise RuntimeError(f"Failed to resolve company name: {e}")

    # Step 2: Search for Recruiter Employees in the resolved company
    search_url = f"{PROXYCURL_BASE_URL}/linkedin/company/employee/search/"
    params = {
        "linkedin_company_profile_url": company_url,
        "keyword_regex": "recruiter|talent acquisition|hiring manager|talent partner|recruitment",
        "enrich_profiles": "enrich"
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(search_url, headers=headers, params=params)
            if resp.status_code != 200:
                raise RuntimeError(f"Proxycurl employee search error: {resp.text}")
            
            employees = resp.json().get("employees", [])
            saved_contacts = []
            
            # Step 3: Parse and insert found employees into DB
            for emp in employees[:5]:  # Limit to 5 recruiters to save database noise
                profile = emp.get("profile", {})
                first_name = profile.get("first_name", "")
                last_name = profile.get("last_name", "")
                name = f"{first_name} {last_name}".strip() or profile.get("full_name", "Anonymous Recruiter")
                
                # Fetch email if present in the profile (Proxycurl sometimes returns work_email)
                email = profile.get("work_email") or profile.get("personal_emails", [None])[0] or ""
                if not email:
                    # Make a unique placeholder email if empty to avoid DB unique violations on NULL
                    import uuid
                    email = f"recruiter-{uuid.uuid4().hex[:6]}@example.com"
                
                role = profile.get("occupation", "Recruiter / HR")
                linkedin_url = profile.get("linkedin_url", "")
                
                contact_fields = {
                    "name": name,
                    "email": email,
                    "company": company_name,
                    "role": role,
                    "source": "Proxycurl Search",
                    "notes": f"LinkedIn Profile: {linkedin_url}",
                    "job_id": job_id
                }
                
                try:
                    contact_id = db.add_contact(**contact_fields)
                    contact_fields["id"] = contact_id
                    saved_contacts.append(contact_fields)
                except Exception:
                    # If email is already saved, fail silently for this row
                    pass
            
            return saved_contacts
            
    except Exception as e:
        raise RuntimeError(f"Failed to search employees via Proxycurl: {e}")
