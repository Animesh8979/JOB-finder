"""Unit tests for SearchOrchestrator, CancellationToken, and CanonicalDeduplicator."""
import time
from typing import Any, Optional
import pytest

from src.sources.adapter_base import CancellationToken, SourceAdapter
from src.sources.search_orchestrator import CanonicalDeduplicator, SearchOrchestrator
from src.sources import aggregate


class MockFastAdapter(SourceAdapter):
    @property
    def source_id(self) -> str:
        return "fast_mock"

    def fetch(
        self,
        query: str,
        limit: int,
        prefs: dict[str, Any],
        cancel_token: Optional[CancellationToken] = None,
    ) -> list[dict[str, Any]]:
        return [
            {
                "dedupe_key": "fast_mock:1",
                "source": "fast_mock",
                "title": "Senior Python Engineer",
                "company": "Stripe Inc.",
                "description": "Great python role with API design.",
                "tags": ["python"],
            }
        ]


class MockSlowAdapter(SourceAdapter):
    @property
    def source_id(self) -> str:
        return "slow_mock"

    def fetch(
        self,
        query: str,
        limit: int,
        prefs: dict[str, Any],
        cancel_token: Optional[CancellationToken] = None,
    ) -> list[dict[str, Any]]:
        # Deliberately ignores cancel_token (like a stuck socket read) and
        # sleeps past BOTH source_timeout_sec (0.4s) and global_timeout_sec
        # (1.0s). This guarantees the orchestrator - not this adapter - decides
        # the outcome, so "slow_mock times out" is deterministic instead of a
        # race between cooperative-cancel and the orchestrator's deadline poll.
        time.sleep(6.0)
        return []


class MockErrorAdapter(SourceAdapter):
    @property
    def source_id(self) -> str:
        return "error_mock"

    def fetch(
        self,
        query: str,
        limit: int,
        prefs: dict[str, Any],
        cancel_token: Optional[CancellationToken] = None,
    ) -> list[dict[str, Any]]:
        raise RuntimeError("Simulated API failure in error_mock")


def test_cancellation_token_lifecycle():
    token = CancellationToken()
    assert not token.is_cancelled()
    assert not token.is_set()

    token.cancel()
    assert token.is_cancelled()
    assert token.is_set()

    with pytest.raises(InterruptedError):
        token.check()


def test_canonical_deduplicator_text():
    raw = "  Senior Python Developer, LLC. (Remote) "
    canon = CanonicalDeduplicator.canonicalize_text(raw)
    assert "llc" not in canon
    assert canon == "senior python developer remote"


def test_canonical_deduplicate_jobs():
    jobs = [
        {
            "dedupe_key": "source1:abc",
            "source": "source1",
            "title": "Senior Backend Engineer",
            "company": "Acme Corp.",
        },
        {
            # Exact same title & company across different source and dedupe_key
            "dedupe_key": "source2:xyz",
            "source": "source2",
            "title": "Senior Backend Engineer",
            "company": "Acme, Inc",
        },
        {
            # Different company, should remain
            "dedupe_key": "source3:123",
            "source": "source3",
            "title": "Senior Backend Engineer",
            "company": "Beta LLC",
        },
    ]

    deduped = CanonicalDeduplicator.deduplicate(jobs)
    assert len(deduped) == 2
    sources = [j["source"] for j in deduped]
    assert "source1" in sources
    assert "source3" in sources
    assert "source2" not in sources


def test_search_orchestrator_fetch_parallel(monkeypatch):
    orchestrator = SearchOrchestrator(
        source_timeout_sec=1.5,
        global_timeout_sec=4.0,
        max_workers=4,
    )

    # Monkeypatch get_adapters to return our custom mock adapters
    def mock_get_adapters(prefs):
        return [MockFastAdapter(), MockSlowAdapter(), MockErrorAdapter()]

    monkeypatch.setattr(orchestrator, "get_adapters", mock_get_adapters)

    jobs, errors = orchestrator.fetch_parallel({"exclude": ["java"]})

    # Fast adapter job should be present
    assert len(jobs) == 1
    assert jobs[0]["source"] == "fast_mock"

    # Slow adapter should timeout
    assert "slow_mock" in errors
    assert "timed out" in errors["slow_mock"].lower()

    # Error adapter should report the error
    assert "error_mock" in errors
    assert "simulated api failure" in errors["error_mock"].lower()


def test_aggregate_fetch_all_uses_orchestrator():
    prefs = {
        "sources": ["remotive"],
        "titles": ["Python"],
        "exclude": [],
    }
    jobs, errors = aggregate.fetch_all(prefs, per_source_limit=2)
    assert isinstance(jobs, list)
    assert isinstance(errors, dict)
