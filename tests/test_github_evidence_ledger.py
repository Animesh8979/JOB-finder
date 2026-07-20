"""Tests for GitHub Evidence Ledger Engine."""
from src.github_evidence_ledger import extract_github_handle, build_github_evidence_ledger


def test_extract_github_handle():
    assert extract_github_handle("https://github.com/torvalds") == "torvalds"
    assert extract_github_handle("github.com/animesh8979/ai-job-finder") == "animesh8979"
    assert extract_github_handle("octocat") == "octocat"
    assert extract_github_handle("") == ""


def test_build_github_evidence_ledger_invalid():
    res = build_github_evidence_ledger("")
    assert res["verified"] is False
    assert res["handle"] == ""
