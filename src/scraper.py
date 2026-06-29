"""Web scraping utility to extract plain text from any job listing URL.

Uses httpx as a fast first pass, and falls back to Playwright running in a separate
thread (to avoid Streamlit event-loop conflicts) for JS-heavy job boards.
"""
from __future__ import annotations

import threading
import httpx
import socket
import ipaddress
import random
import time
from urllib.parse import urlparse, urljoin
from curl_cffi import requests as cffi_requests
from . import config

# A basic set of headers to look like a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

def is_private_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved
    except ValueError:
        return True  # Treat invalid IPs as private/unsafe

def validate_url_for_ssrf(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or parsed.scheme not in ("http", "https"):
        raise ValueError("Only http and https schemes are allowed.")
    
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid URL hostname.")
        
    try:
        addr_info = socket.getaddrinfo(hostname, None)
        for family, _, _, _, sockaddr in addr_info:
            ip = sockaddr[0]
            if is_private_ip(ip):
                raise ValueError("Access to private/local network ranges is prohibited.")
        # Return the first resolved IP for DNS pinning
        return addr_info[0][4][0]
    except socket.gaierror as e:
        raise ValueError(f"Unable to resolve hostname: {e}")

def _scrape_with_httpx(url: str) -> str:
    """Attempt to use Jina Reader API for perfect markdown extraction, fallback to curl_cffi."""
    try:
        validate_url_for_ssrf(url)
        # Jina is safe because Jina's server makes the request to the target url.
        jina_url = f"https://r.jina.ai/{url}"
        proxy = config.proxy_url()
        with httpx.Client(headers=HEADERS, timeout=15.0, follow_redirects=True, proxy=proxy if proxy else None) as client:
            resp = client.get(jina_url)
            if resp.status_code == 200 and len(resp.text) > 100:
                return resp.text
    except Exception:
        pass
        
    # State-of-the-Art JA3/JA4 Fingerprint Evasion (Level 4 Ouroboros)
    try:
        ip = validate_url_for_ssrf(url)
        parsed = urlparse(url)
        pinned_url = url.replace(parsed.hostname, ip)
        proxy = config.proxy_url()
        proxies = {"http": proxy, "https": proxy} if proxy else None
        
        # Impersonate Chrome 120 to completely bypass Cloudflare/DataDome TLS checks
        resp = cffi_requests.get(
            pinned_url, 
            impersonate="chrome120", 
            headers={"Host": parsed.hostname}, 
            proxies=proxies,
            timeout=15.0, 
            allow_redirects=True,
            verify=True
        )
        if resp.status_code == 200:
            from .sources.base import strip_html
            return strip_html(resp.text)
    except Exception:
        pass
    return ""


_playwright_semaphore = threading.Semaphore(2)

def _playwright_worker(url: str, result_container: list[str]) -> None:
    """Playwright execution running in a separate thread with stealth."""
    if not _playwright_semaphore.acquire(timeout=20.0):
        result_container.append("ERROR: Playwright concurrency limit reached.")
        return
    try:
        from playwright.sync_api import sync_playwright
        from stealth_sync import stealth_sync
        
        with sync_playwright() as p:
            # Jitter before starting to prevent spike bans
            time.sleep(random.uniform(1.2, 3.8))
            
            # Launch headless browser
            proxy_url = config.proxy_url()
            proxy_settings = {"server": proxy_url} if proxy_url else None
            browser = p.chromium.launch(headless=True, proxy=proxy_settings)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            stealth_sync(page)
            
            # Wait for content to load
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # Give JS a second to render
            page.wait_for_timeout(2000)
            
            # Extract plain text from body
            body = page.query_selector("body")
            if body:
                text = body.inner_text()
                result_container.append(text)
            
            browser.close()
    except Exception as e:
        result_container.append(f"ERROR: {e}")
    finally:
        _playwright_semaphore.release()


def _scrape_with_playwright(url: str) -> str:
    """Launch Playwright in a new thread and wait for it to complete."""
    results: list[str] = []
    t = threading.Thread(target=_playwright_worker, args=(url, results))
    t.start()
    t.join(timeout=40.0)  # Max wait time 40s
    if results and not results[0].startswith("ERROR:"):
        return results[0].strip()
    return ""


def scrape_url_text(url: str) -> str:
    """Scrapes raw text from the given URL. Tries HTTPX first, then Playwright, then Firecrawl."""
    url = url.strip()
    validate_url_for_ssrf(url)

    # 1. Fast path (HTTPX / curl_cffi)
    text = _scrape_with_httpx(url)
    if len(text) > 800:
        return text

    # 2. JS-rendering/Dynamic path (Playwright)
    text_pw = _scrape_with_playwright(url)
    if text_pw:
        return text_pw
        
    # 3. Firecrawl MCP Fallback (Anti-Bot Bypass)
    from . import mcp_client
    try:
        fc_result = mcp_client.call_tool("firecrawl_scrape", {"url": url})
        if fc_result and "Error" not in fc_result and "Exception" not in fc_result:
            return fc_result
    except Exception as e:
        print(f"Firecrawl MCP fallback failed: {e}")

    # Fallback if all failed or returned very little
    if text:
        return text

    raise RuntimeError("Failed to scrape job page. The site may be protected or blocked.")


def parse_job_from_text(text: str, url: str) -> dict[str, Any]:
    """Uses LLM to extract structured job posting details from raw scraped text."""
    from . import llm
    from .sources.base import normalize
    from typing import Any

    prompt = (
        "Extract details from this scraped job posting text into JSON.\n\n"
        "FIELDS TO EXTRACT:\n"
        "- title (str): job title\n"
        "- company (str): hiring company name\n"
        "- location (str): e.g. 'Remote', 'New York', 'Remote (US/Canada)'\n"
        "- remote (bool): is it remote?\n"
        "- apply_url (str): direct application page link (if found, otherwise leave empty)\n"
        "- description (str): markdown/plain text of job description details (responsibilities, requirements)\n"
        "- salary_min (int/null): minimum salary\n"
        "- salary_max (int/null): maximum salary\n"
        "- currency (str): e.g. 'USD', 'EUR', or empty\n"
        "- tags (list of str): skills or tech stack mentioned (e.g. ['python', 'aws'])\n\n"
        "JOB POSTING TEXT:\n"
        "\"\"\"\n" + text[:6000] + "\n\"\"\""
    )
    
    data = llm.generate_json(prompt, system="You are an expert ATS parser. Return a JSON object with only the requested fields.", max_tokens=1500)
    if not isinstance(data, dict):
        data = {}

    return normalize(
        source="custom_url",
        source_job_id="",
        title=data.get("title", ""),
        company=data.get("company", ""),
        location=data.get("location", "Remote"),
        url=url,
        apply_url=data.get("apply_url") or url,
        description=data.get("description", text),
        salary_min=data.get("salary_min"),
        salary_max=data.get("salary_max"),
        currency=data.get("currency", ""),
        tags=data.get("tags", []),
        remote=bool(data.get("remote", True)),
        raw={"scraped_url": url}
    )


def scrape_jobs_with_apify(query: str, location: str, limit: int = 10) -> list[dict[str, Any]]:
    """Runs the Apify LinkedIn Jobs Scraper actor and returns a list of normalized job dicts."""
    from . import config
    from .sources.base import normalize
    import time
    
    token = config.get_secret("apify_api_token", "APIFY_API_TOKEN")
    if not token:
        raise ValueError("Apify API Token not configured. Please add it in the Setup page.")

    # Use the popular apify/linkedin-jobs-scraper actor
    actor_id = "apify/linkedin-jobs-scraper"
    run_url = f"https://api.apify.com/v2/acts/{actor_id}/runs"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Run payload parameters
    payload = {
        "queries": query,
        "location": location,
        "limit": limit
    }
    
    try:
        # Step 1: Start the run
        proxy = config.proxy_url()
        with httpx.Client(timeout=30.0, headers=headers, proxy=proxy if proxy else None) as client:
            run_resp = client.post(run_url, json=payload)
            if run_resp.status_code not in (200, 201):
                raise RuntimeError(f"Failed to start Apify actor: {run_resp.text}")
            
            run_data = run_resp.json().get("data", {})
            run_id = run_data.get("id")
            dataset_id = run_data.get("defaultDatasetId")
            
            if not run_id or not dataset_id:
                raise RuntimeError("Apify did not return run_id or dataset_id")

            # Step 2: Poll status (Max wait 5 minutes)
            status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
            max_polls = 60
            for _ in range(max_polls):
                status_resp = client.get(status_url)
                if status_resp.status_code == 200:
                    status = status_resp.json().get("data", {}).get("status")
                    if status == "SUCCEEDED":
                        break
                    elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
                        raise RuntimeError(f"Apify actor run failed with status: {status}")
                time.sleep(5)
            else:
                raise TimeoutError("Apify scraper run timed out after 5 minutes.")

            # Step 3: Fetch results
            dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
            results_resp = client.get(dataset_url)
            if results_resp.status_code != 200:
                raise RuntimeError(f"Failed to fetch Apify dataset: {results_resp.text}")
                
            items = results_resp.json()
            normalized_jobs = []
            
            for item in items:
                # Map typical fields returned by apify/linkedin-jobs-scraper
                title = item.get("positionName") or item.get("title") or "Unknown Title"
                company = item.get("companyName") or item.get("company") or "Unknown Company"
                job_url = item.get("jobUrl") or item.get("url") or ""
                desc = item.get("descriptionText") or item.get("description") or ""
                loc = item.get("location") or "Remote"
                
                # Try to clean/extract fields
                normalized = normalize(
                    source="linkedin_apify",
                    source_job_id=item.get("id") or "",
                    title=title,
                    company=company,
                    location=loc,
                    url=job_url,
                    apply_url=item.get("applyUrl") or job_url,
                    description=desc,
                    salary_min=item.get("salaryMin") or item.get("salary"),
                    salary_max=item.get("salaryMax") or item.get("salary"),
                    currency=item.get("salaryCurrency") or "USD",
                    tags=item.get("skills") or [],
                    remote="remote" in loc.lower(),
                    raw=item
                )
                normalized_jobs.append(normalized)
                
            return normalized_jobs
            
    except Exception as e:
        raise RuntimeError(f"Apify scraping failed: {e}")


def search_company_about_url(company_name: str) -> str:
    """Find a company's About Us page url using DuckDuckGo HTML search."""
    import re
    import urllib.parse
    query = f"{company_name} about us mission"
    search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    proxy = config.proxy_url()
    try:
        with httpx.Client(headers=HEADERS, timeout=10.0, proxy=proxy if proxy else None) as client:
            resp = client.get(search_url)
            if resp.status_code == 200:
                # Find all matches of /l/?uddg=...
                matches = re.findall(r'uddg=([^&"]+)', resp.text)
                for m in matches:
                    decoded_url = urllib.parse.unquote(m)
                    if decoded_url.startswith(("http://", "https://")):
                        parsed_url = urlparse(decoded_url)
                        domain = parsed_url.netloc.lower()
                        if not any(bad in domain for bad in ("duckduckgo.com", "google.com", "facebook.com", "twitter.com", "linkedin.com", "youtube.com", "instagram.com")):
                            return decoded_url
    except Exception as e:
        print(f"Error searching company about URL: {e}")
    return ""


def get_company_intelligence(company_name: str) -> dict[str, Any]:
    """Search for the company's About page, scrape it, and extract structured insights."""
    intel = {
        "company_name": company_name,
        "about_url": "",
        "scraped_text": "",
        "mission": "",
        "values": [],
        "milestones": [],
        "culture_summary": ""
    }
    
    if not company_name:
        return intel
        
    url = search_company_about_url(company_name)
    if not url:
        return intel
        
    intel["about_url"] = url
    try:
        text = scrape_url_text(url)
        intel["scraped_text"] = text[:4000]
    except Exception as e:
        print(f"Error scraping company URL {url}: {e}")
        return intel
        
    from . import llm
    if intel["scraped_text"] and llm.config.provider_ready():
        prompt = (
            f"Analyze this scraped 'About Us' or corporate website page for the company '{company_name}'.\n"
            "Extract the company's core mission, values, culture indicators, and any recent milestones/news.\n\n"
            f"SCRAPED WEBPAGE TEXT:\n\"\"\"\n{intel['scraped_text']}\n\"\"\"\n\n"
            "Return JSON with ONLY these exact fields:\n"
            "{\n"
            '  "mission": "Short statement of their mission/vision (1-2 sentences)",\n'
            '  "values": ["Value 1", "Value 2", "Value 3"] (key company values/principles),\n'
            '  "milestones": ["Milestone 1", "Milestone 2"] (recent product launches, growth, funding, or press events),\n'
            '  "culture_summary": "1-2 sentences summarizing their engineering or company culture"\n'
            "}"
        )
        try:
            prefs = llm.config.load_prefs()
            data = llm.generate_json(
                prompt,
                system="You are a corporate researcher extracting company profiles.",
                model=prefs.get("writing_model"),
                max_tokens=500
            )
            if isinstance(data, dict):
                intel.update({
                    "mission": data.get("mission", ""),
                    "values": data.get("values", []),
                    "milestones": data.get("milestones", []),
                    "culture_summary": data.get("culture_summary", "")
                })
        except Exception as e:
            print(f"Error parsing company intelligence with LLM: {e}")
            
    return intel


