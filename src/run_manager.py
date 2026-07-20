"""RunManager: Singleton manager for durable run lifecycle, status persistence, and SSE pub-sub.

Addresses SQLite WAL contention by decoupling high-frequency progress streaming (via in-memory asyncio.Queue pub-sub)
from durable state transitions stored in SQLite (`runs` and `run_events` tables).
"""
from __future__ import annotations

import asyncio
import json
import logging
import threading
import uuid
from datetime import datetime
from typing import Any, AsyncIterator

from . import db

logger = logging.getLogger("ai_job_finder.run_manager")

class RunManager:
    _instance: RunManager | None = None
    _lock = threading.Lock()

    def __init__(self):
        # List of active subscriber queues for SSE streaming
        self._subscribers: list[tuple[str | None, asyncio.Queue[dict[str, Any]]]] = []
        self._subscribers_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> RunManager:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def start_run(
        self,
        kind: str,
        request_data: dict[str, Any] | str | None = None,
        run_id: str | None = None,
        parent_run_id: str | None = None,
        idempotency_key: str | None = None
    ) -> dict[str, Any]:
        """Create and persist a new run, emitting a start event to subscribers."""
        if not run_id:
            run_id = f"run_{uuid.uuid4().hex[:12]}"
        
        req_json = (
            request_data if isinstance(request_data, str)
            else json.dumps(request_data or {}, ensure_ascii=False)
        )

        db.create_run(
            run_id=run_id,
            kind=kind,
            request_json=req_json,
            parent_run_id=parent_run_id,
            idempotency_key=idempotency_key
        )
        
        # Log initial event
        db.add_run_event(run_id, "INFO", f"Run started ({kind})")

        run_obj = db.get_run(run_id) or {
            "run_id": run_id,
            "kind": kind,
            "status": "queued",
            "progress_current": 0,
            "progress_total": 100
        }

        # Publish SSE update
        self.publish_event(run_id, "run_started", run_obj)
        return run_obj

    def update_progress(
        self,
        run_id: str,
        phase: str | None = None,
        message: str | None = None,
        current: int | None = None,
        total: int | None = None,
        status: str = "running",
        result_data: dict[str, Any] | str | None = None,
        error_message: str | None = None
    ) -> dict[str, Any] | None:
        """Update run status and progress, both persisting in DB and broadcasting over SSE."""
        res_json = (
            result_data if isinstance(result_data, str)
            else (json.dumps(result_data, ensure_ascii=False) if result_data is not None else None)
        )

        db.update_run_status(
            run_id=run_id,
            status=status,
            error_message=error_message,
            phase=phase,
            message=message,
            progress_current=current,
            progress_total=total,
            result_json=res_json
        )

        if message:
            level = "ERROR" if status == "failed" else ("INFO" if status in ("completed", "running") else "DEBUG")
            db.add_run_event(run_id, level, message)

        run_obj = db.get_run(run_id)
        if run_obj:
            event_type = (
                "run_completed" if status == "completed"
                else ("run_failed" if status == "failed" else "run_progress")
            )
            self.publish_event(run_id, event_type, run_obj)
        return run_obj

    def log_event(self, run_id: str, level: str, message: str, metadata: dict[str, Any] | None = None) -> None:
        """Log a structured run event without altering core run status."""
        meta_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
        db.add_run_event(run_id, level, message, metadata_json=meta_json)
        self.publish_event(
            run_id,
            "run_log",
            {
                "run_id": run_id,
                "level": level,
                "message": message,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat()
            }
        )

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        return db.get_run(run_id)

    def list_runs(self, limit: int = 50, status: str | None = None) -> list[dict[str, Any]]:
        return db.list_runs(limit=limit, status=status)

    def publish_event(self, run_id: str, event_type: str, data: dict[str, Any]) -> None:
        """Publish an event to all active in-memory subscriber queues matching the run_id."""
        payload = {
            "event": event_type,
            "run_id": run_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        with self._subscribers_lock:
            for filter_run_id, queue in self._subscribers:
                if filter_run_id is None or filter_run_id == run_id:
                    try:
                        queue.put_nowait(payload)
                    except asyncio.QueueFull:
                        # Drop if queue is backed up
                        pass
                    except Exception as e:
                        logger.debug("Failed to put event in queue: %s", e)

    async def subscribe(self, run_id: str | None = None) -> AsyncIterator[dict[str, Any]]:
        """Async generator yielding SSE events for the specified run_id (or all runs if None)."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        entry = (run_id, queue)
        with self._subscribers_lock:
            self._subscribers.append(entry)
        
        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            with self._subscribers_lock:
                if entry in self._subscribers:
                    self._subscribers.remove(entry)

def get_run_manager() -> RunManager:
    return RunManager.get_instance()
