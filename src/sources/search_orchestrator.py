"""Search Orchestrator with parallel source execution, timeouts, and canonical deduplication."""
from __future__ import annotations

import concurrent.futures
import re
import threading
import time
from typing import Any, Callable, Optional
from .adapter_base import CancellationToken, ModuleSourceAdapter, SourceAdapter
from . import aggregate


class CanonicalDeduplicator:
    """Canonical deduplication engine across disparate job boards."""

    @staticmethod
    def canonicalize_text(text: str) -> str:
        """Strip punctuation, corporate suffixes, and extra whitespace."""
        if not text:
            return ""
        s = text.lower()
        # Remove common company suffixes like Inc, LLC, Corp, Ltd, B.V., GmbH
        s = re.sub(
            r"\b(inc\.?|llc\.?|corp\.?|ltd\.?|co\.?|b\.v\.?|gmbh)\b",
            "",
            s,
            flags=re.IGNORECASE,
        )
        # Remove non-alphanumeric characters except basic whitespace
        s = re.sub(r"[^a-z0-9\s]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    @classmethod
    def deduplicate(cls, jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Deduplicate jobs by dedupe_key first, then by canonical title+company."""
        seen_keys: set[str] = set()
        seen_canonical: set[tuple[str, str]] = set()
        deduped: list[dict[str, Any]] = []

        for job in jobs:
            key = job.get("dedupe_key")
            if key and key in seen_keys:
                continue

            # Also check canonical title + company pair
            c_title = cls.canonicalize_text(job.get("title", ""))
            c_comp = cls.canonicalize_text(job.get("company", ""))
            
            # Only use title+company dedupe if both have substantive length
            if len(c_title) > 3 and len(c_comp) > 2:
                pair = (c_title, c_comp)
                if pair in seen_canonical:
                    continue
                seen_canonical.add(pair)

            if key:
                seen_keys.add(key)
            deduped.append(job)

        return deduped


class SearchOrchestrator:
    """Orchestrates parallel fetching across enabled sources with strict timeouts."""

    def __init__(
        self,
        source_timeout_sec: float = 12.0,
        global_timeout_sec: float = 45.0,
        max_workers: int = 8,
    ) -> None:
        self.source_timeout_sec = source_timeout_sec
        self.global_timeout_sec = global_timeout_sec
        self.max_workers = max_workers

    def get_adapters(self, prefs: dict[str, Any]) -> list[SourceAdapter]:
        """Resolve SourceAdapter instances for all enabled sources."""
        prefs = aggregate._inject_ats_defaults(prefs)
        enabled = prefs.get("sources") or list(aggregate.REGISTRY)
        adapters: list[SourceAdapter] = []

        for sid in enabled:
            mod = aggregate.REGISTRY.get(sid)
            if not mod:
                continue
            
            # Check if mod has an adapter class or instance
            adapter_cls = getattr(mod, f"{sid.capitalize()}Adapter", None)
            if adapter_cls and isinstance(adapter_cls, type) and issubclass(adapter_cls, SourceAdapter):
                adapters.append(adapter_cls())
            else:
                adapters.append(ModuleSourceAdapter(sid, mod))

        return adapters

    def _fetch_single_source(
        self,
        adapter: SourceAdapter,
        query: str,
        limit: int,
        prefs: dict[str, Any],
        token: CancellationToken,
    ) -> tuple[str, list[dict[str, Any]], Optional[str], float]:
        """Fetch from a single adapter, tracking duration and errors."""
        start = time.time()
        try:
            jobs = adapter.fetch(query, limit, prefs, cancel_token=token)
            duration_ms = (time.time() - start) * 1000.0
            return (adapter.source_id, jobs, None, duration_ms)
        except Exception as e:
            duration_ms = (time.time() - start) * 1000.0
            return (adapter.source_id, [], str(e), duration_ms)

    def fetch_parallel(
        self,
        prefs: dict[str, Any],
        per_source_limit: int = 50,
        on_source_complete: Optional[Callable[[str, int, Optional[str], float], None]] = None,
    ) -> tuple[list[dict[str, Any]], dict[str, str]]:
        """Fetch jobs in parallel across enabled sources with per-source and global timeouts.

        Returns:
            tuple[list[dict[str, Any]], dict[str, str]]: (deduplicated jobs, {source_id: error_msg})
        """
        query = aggregate.build_query(prefs)
        prefs = aggregate._inject_ats_defaults(prefs)
        adapters = self.get_adapters(prefs)

        if not adapters:
            return [], {}

        collected_jobs: list[dict[str, Any]] = []
        errors: dict[str, str] = {}
        global_start = time.time()
        future_to_adapter = {}
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        try:
            for adapter in adapters:
                token = CancellationToken()
                start_time = time.time()
                timer = threading.Timer(self.source_timeout_sec, token.cancel)
                timer.start()
                fut = executor.submit(
                    self._fetch_single_source,
                    adapter,
                    query,
                    per_source_limit,
                    prefs,
                    token,
                )
                future_to_adapter[fut] = (adapter, token, start_time, timer)

            # Check futures until all complete or timeout
            pending = set(future_to_adapter.keys())
            while pending:
                elapsed_global = time.time() - global_start
                if elapsed_global >= self.global_timeout_sec:
                    break
                
                # Wait for up to 0.1s for any future to complete
                done, _ = concurrent.futures.wait(pending, timeout=0.05, return_when=concurrent.futures.FIRST_COMPLETED)
                for fut in done:
                    pending.remove(fut)
                    adapter, token, start_time, timer = future_to_adapter[fut]
                    timer.cancel()
                    try:
                        sid, jobs, err, duration_ms = fut.result(timeout=0)
                        if err:
                            errors[sid] = err
                        else:
                            valid_jobs = [j for j in jobs if aggregate.base.matches_filters(j, prefs)]
                            collected_jobs.extend(valid_jobs)
                        if on_source_complete:
                            on_source_complete(sid, len(jobs), err, duration_ms)
                    except Exception as e:
                        errors[adapter.source_id] = str(e)
                        if on_source_complete:
                            on_source_complete(adapter.source_id, 0, str(e), (time.time() - start_time) * 1000.0)

                # Check if any pending futures have exceeded their source_timeout_sec
                for fut in list(pending):
                    adapter, token, start_time, timer = future_to_adapter[fut]
                    if time.time() - start_time >= self.source_timeout_sec:
                        pending.remove(fut)
                        token.cancel()
                        timer.cancel()
                        errors[adapter.source_id] = f"Source timed out after {self.source_timeout_sec}s"
                        if on_source_complete:
                            on_source_complete(adapter.source_id, 0, errors[adapter.source_id], self.source_timeout_sec * 1000.0)

            # Handle any remaining pending futures (global timeout)
            for fut in pending:
                adapter, token, start_time, timer = future_to_adapter[fut]
                token.cancel()
                timer.cancel()
                errors[adapter.source_id] = f"Global search timeout reached ({self.global_timeout_sec}s)"
                if on_source_complete:
                    on_source_complete(adapter.source_id, 0, errors[adapter.source_id], self.global_timeout_sec * 1000.0)

        finally:
            for fut, (adapter, token, start_time, timer) in future_to_adapter.items():
                token.cancel()
                timer.cancel()
            executor.shutdown(wait=False, cancel_futures=True)

        # Run Canonical Deduplication
        deduped = CanonicalDeduplicator.deduplicate(collected_jobs)
        return deduped, errors
