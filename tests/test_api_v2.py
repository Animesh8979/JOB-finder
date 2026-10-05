"""tests/test_api_v2.py: Unit tests for durable RunManager and /api/v2 endpoints."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from server import app
from src.run_manager import get_run_manager

@pytest.fixture
def client():
    return TestClient(app)

def test_run_manager_lifecycle():
    rm = get_run_manager()
    run = rm.start_run("test_kind", {"sample": "request"})
    run_id = run["run_id"]
    assert run["status"] == "queued"
    
    rm.update_progress(run_id, phase="fetching", message="Fetching data", current=25, total=100)
    updated = rm.get_run(run_id)
    assert updated is not None
    assert updated["phase"] == "fetching"
    assert updated["progress_current"] == 25
    
    rm.update_progress(run_id, status="completed", message="Done", current=100, total=100, result_data={"items": 5})
    final_run = rm.get_run(run_id)
    assert final_run["status"] == "completed"

def test_api_v2_runs_endpoints(client):
    res = client.get("/api/v2/runs")
    assert res.status_code == 200
    runs = res.json()
    assert isinstance(runs, list)

def test_api_v2_jobs_endpoints(client):
    res = client.get("/api/v2/jobs?limit=10")
    assert res.status_code == 200
    jobs = res.json()
    assert isinstance(jobs, list)

def test_api_v2_trigger_search(client):
    payload = {
        "query": "Backend Engineer Python",
        "remote_only": True,
        "sources": ["remoteok"]
    }
    res = client.post("/api/v2/search", json=payload, headers={"Origin": "http://localhost:5173"})
    assert res.status_code == 200
    run_data = res.json()
    assert run_data["kind"] == "search"
    assert run_data["run_id"].startswith("run_")
