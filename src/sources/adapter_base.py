"""Base classes and cancellation token support for job source adapters."""
from __future__ import annotations

import abc
import threading
from typing import Any, Callable, Optional


class CancellationToken:
    """Thread-safe cancellation token for halting slow or timed-out adapters."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        """Signal that the operation should be cancelled."""
        self._event.set()

    def is_set(self) -> bool:
        """Check if cancellation has been requested."""
        return self._event.is_set()

    def is_cancelled(self) -> bool:
        """Alias for is_set()."""
        return self._event.is_set()

    def check(self) -> None:
        """Raise InterruptedError if cancelled."""
        if self._event.is_set():
            raise InterruptedError("Operation cancelled via CancellationToken.")


class SourceAdapter(abc.ABC):
    """Abstract base class for all job board source adapters."""

    @property
    @abc.abstractmethod
    def source_id(self) -> str:
        """Unique string identifier for this source (e.g., 'greenhouse')."""
        pass

    @abc.abstractmethod
    def fetch(
        self,
        query: str,
        limit: int,
        prefs: dict[str, Any],
        cancel_token: Optional[CancellationToken] = None,
    ) -> list[dict[str, Any]]:
        """Fetch normalized jobs from the source.

        Must respect cancel_token if provided by checking cancel_token.is_cancelled()
        during loops or slow operations.
        """
        pass


class ModuleSourceAdapter(SourceAdapter):
    """Wraps an existing function-based source module into a SourceAdapter."""

    def __init__(self, sid: str, module: Any) -> None:
        self._sid = sid
        self._module = module

    @property
    def source_id(self) -> str:
        return self._sid

    def fetch(
        self,
        query: str,
        limit: int,
        prefs: dict[str, Any],
        cancel_token: Optional[CancellationToken] = None,
    ) -> list[dict[str, Any]]:
        if cancel_token and cancel_token.is_cancelled():
            return []

        # Check if the module's fetch function accepts cancel_token
        fetch_fn = getattr(self._module, "fetch", None)
        if not fetch_fn:
            return []

        # Inspect if fetch accepts cancel_token kwarg
        import inspect
        try:
            sig = inspect.signature(fetch_fn)
            if "cancel_token" in sig.parameters:
                return fetch_fn(query, limit, prefs, cancel_token=cancel_token)
        except Exception:
            pass

        return fetch_fn(query, limit, prefs)
