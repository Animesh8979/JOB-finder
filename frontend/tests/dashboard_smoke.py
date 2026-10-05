"""Playwright smoke test for the React dashboard (mocked backend, no network).

Serves frontend/dist with Python's http.server and intercepts all API calls with
Playwright route mocks, so no real LLM calls, scraping, or applications happen.

Run:  .venv/Scripts/python.exe frontend/tests/dashboard_smoke.py
Exits 0 on success; prints failures and exits 1 otherwise.
"""
from __future__ import annotations

import http.server
import json
import socketserver
import subprocess
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

FRONTEND = Path(__file__).resolve().parent.parent
PORT = 4199

MOCK_JOBS = [
    {
        "id": 1, "title": "Senior Backend Engineer", "company": "Acme Corp",
        "location": "Remote", "remote": True, "url": "https://example.com/1",
        "description": "Python FastAPI PostgreSQL role with strong system design.",
        "match_score": 88, "match_reason": "Strong Python + API overlap",
        "status": "Saved", "posted_at": "2026-09-15T10:00:00",
    },
    {
        "id": 2, "title": "Data Platform Engineer", "company": "Globex",
        "location": "Remote (US)", "remote": True, "url": "https://example.com/2",
        "description": "Data pipelines, Airflow, and analytics engineering.",
        "match_score": 72, "match_reason": "Good data engineering fit",
        "status": "Saved", "posted_at": "2026-09-10T10:00:00",
    },
]
MOCK_ATS = {
    "survival_score": 76, "keyword_coverage_pct": 68.5, "hard_disqualifiers": [],
    "matched_ngrams": ["python", "fastapi"], "missing_ngrams": ["kubernetes"],
    "action_verb_score": 80, "metric_quantifier_count": 5,
    "strong_verbs_found": ["built", "led"], "recommendations": ["Add Kubernetes exposure."],
}
MOCK_SALARY = {
    "has_compensation": True, "role_matched": "backend", "offered_min": 120000,
    "offered_max": 160000, "offered_midpoint": 140000, "market_midpoint": 135000,
    "compa_ratio": 1.04, "market_tier": "strong", "leverage_assessment": "Above market.",
    "benchmarks": {"title": "Backend", "p25": 110000, "p50": 135000, "p75": 160000, "p90": 190000},
    "geo_arbitrage_multiplier": 1.1, "currency": "USD",
}


def _mock_json(route, payload, status=200):
    route.fulfill(status=status, content_type="application/json", body=json.dumps(payload))


def install_mock_routes(page):
    page.route("**/api/v2/jobs/1/ats_breakdown", lambda r: _mock_json(r, MOCK_ATS))
    page.route("**/api/v2/jobs/*/ats_breakdown", lambda r: _mock_json(r, MOCK_ATS))
    page.route("**/api/jobs/*/ats_breakdown", lambda r: _mock_json(r, MOCK_ATS))
    page.route("**/api/v2/jobs/*/salary_arbitrage", lambda r: _mock_json(r, MOCK_SALARY))
    page.route("**/api/jobs/*/salary_arbitrage", lambda r: _mock_json(r, MOCK_SALARY))
    page.route("**/api/v2/jobs*", lambda r: _mock_json(r, MOCK_JOBS))
    page.route("**/api/v2/runs*", lambda r: _mock_json(r, []))
    page.route("**/api/v2/search", lambda r: _mock_json(r, {"run_id": "mock-run", "kind": "search", "status": "queued"}))
    page.route("**/api/v2/events", lambda r: r.fulfill(status=200, content_type="text/event-stream", body=""))
    page.route("**/api/stream/events", lambda r: r.fulfill(status=200, content_type="text/event-stream", body=""))
    page.route("**/api/stats", lambda r: _mock_json(r, {"total_tailored": 3, "total_interview": 1}))
    page.route("**/api/status", lambda r: _mock_json(r, {"ai_key": True, "resume": True, "identity": True}))
    page.route("**/api/recruiter_score", lambda r: _mock_json(r, {"total": 84}))
    page.route("**/api/profile", lambda r: _mock_json(r, {"name": "Test Candidate", "skills": []}))
    page.route("**/api/preferences", lambda r: _mock_json(r, {"prefs": {}, "secrets": {}}))
    page.route("**/api/skills", lambda r: _mock_json(r, {"skills": [], "total": 0, "filtered_count": 0, "categories": {}}))


def serve_dist() -> tuple[socketserver.TCPServer, threading.Thread]:
    handler = lambda *args, **kw: http.server.SimpleHTTPRequestHandler(  # noqa: E731
        directory=str(FRONTEND / "dist"), *args, **kw
    )
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread



def main() -> int:
    from playwright.sync_api import expect

    if not (FRONTEND / "dist" / "index.html").exists():
        raise RuntimeError("Build the frontend with npm run build before this test.")
    server, thread = serve_dist()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 1000})
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                install_mock_routes(page)
                page.goto(f"http://127.0.0.1:{PORT}/", wait_until="domcontentloaded")
                expect(page.get_by_text("Best Matched Roles", exact=True)).to_be_visible()
                cards = page.locator('[role="button"][aria-label^="Open job:"]')
                expect(cards).to_have_count(2)
                print("PASS: dashboard mounts and renders job fixtures", flush=True)

                search = page.locator('#command-search')
                search.fill("Globex")
                expect(cards).to_have_count(1)
                expect(cards.first).to_contain_text("Data Platform Engineer")
                search.fill("no-matching-company")
                expect(page.get_by_text("No Jobs Found in Pipeline", exact=True)).to_be_visible()
                search.fill("")
                search.blur()
                expect(cards).to_have_count(2)
                print("PASS: filtering and empty state", flush=True)

                page.get_by_role("button", name="ATS Gap Matrix").first.click()
                expect(page.get_by_text("Adversarial ATS Simulator", exact=True)).to_be_visible()
                expect(page.get_by_text("76%", exact=True)).to_be_visible()
                expect(page.get_by_text("Add Kubernetes exposure.", exact=True)).to_be_visible()
                page.keyboard.press("Escape")
                expect(page.get_by_text("Adversarial ATS Simulator", exact=True)).to_have_count(0)
                # Blur so global navigation is tested, not focused-button activation.
                page.evaluate("document.activeElement?.blur()")
                page.keyboard.press("j")
                expect(page.locator('[aria-pressed="true"][aria-label^="Open job:"]')).to_have_attribute(
                    "aria-label", "Open job: Data Platform Engineer"
                )
                print("PASS: ATS JSON rendering, Escape and keyboard selection", flush=True)

                page.get_by_role("button", name="ATS Gap Matrix").first.focus()
                page.keyboard.press("Enter")
                expect(page.get_by_text("76%", exact=True)).to_be_visible()
                page.keyboard.press("Escape")
                print("PASS: keyboard activation of nested ATS action", flush=True)

                page.set_viewport_size({"width": 390, "height": 844})
                expect(search).to_be_visible()
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "Mobile horizontal overflow"
                shots = FRONTEND / "test-results"
                shots.mkdir(exist_ok=True)
                page.screenshot(path=str(shots / "dashboard-mobile.png"))
                page.set_viewport_size({"width": 1440, "height": 1000})
                page.screenshot(path=str(shots / "dashboard-desktop.png"))
                assert not errors, f"Browser runtime errors: {errors}"
                print("PASS: mobile layout and zero browser runtime errors", flush=True)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    print("ALL DASHBOARD SMOKE CHECKS PASSED", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
