"""HackerNews Who Is Hiring integration via Algolia and Firebase."""
import time
from typing import Any
from . import base, client

def fetch(query: str, limit: int, prefs: dict[str, Any]) -> list[dict[str, Any]]:
    """Fetch jobs from the latest HackerNews 'Who is hiring?' thread."""
    jobs_out = []
    
    try:
        # 1. Find the latest thread via Algolia
        search_url = 'https://hn.algolia.com/api/v1/search?query="who is hiring"&tags=ask_hn&restrictSearchableAttributes=title'
        search_resp = client.get_json(search_url)
        if not search_resp or not search_resp.get("hits"):
            return []
            
        latest_thread_id = search_resp["hits"][0]["objectID"]
        
        # 2. Fetch thread items via Firebase
        thread_url = f"https://hacker-news.firebaseio.com/v0/item/{latest_thread_id}.json"
        thread_resp = client.get_json(thread_url)
        if not thread_resp or not thread_resp.get("kids"):
            return []
            
        kids = thread_resp["kids"][:30]  # Limit to top 30 comments
        
        for kid_id in kids:
            item_url = f"https://hacker-news.firebaseio.com/v0/item/{kid_id}.json"
            item = client.get_json(item_url)
            if not item or not item.get("text"):
                continue
                
            text = item["text"]
            # Try to extract company and title from the first line
            first_line = text.split("<p>")[0].split("\n")[0]
            
            company = ""
            title = ""
            if "|" in first_line:
                parts = first_line.split("|")
                company = base.strip_html(parts[0]).strip()
                title = base.strip_html(" | ".join(parts[1:])).strip()
            else:
                company = "HN Poster"
                title = base.strip_html(first_line).strip()[:100]
                
            # Skip if title is empty or generic
            if not title or len(title) < 5:
                continue
                
            if query and query.lower() not in text.lower():
                continue
                
            remote = "remote" in text.lower()
            
            jobs_out.append(base.normalize(
                source="hackernews",
                source_job_id=str(kid_id),
                title=title,
                company=company,
                location="Remote" if remote else "Various",
                url=f"https://news.ycombinator.com/item?id={kid_id}",
                apply_url=f"https://news.ycombinator.com/item?id={kid_id}",
                description=base.strip_html(text),
                posted_at=client.iso_from_unix(item.get("time")) if item.get("time") else "",
                remote=remote,
                raw={"hn_id": kid_id},
            ))
            if len(jobs_out) >= limit:
                break
                
            time.sleep(0.1)  # Be gentle with Firebase API
            
    except Exception as e:
        print(f"Error fetching from hackernews: {e}")
        
    return jobs_out
