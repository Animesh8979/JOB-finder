"""Tests for the free-tier Ollama provider path in src/llm.py and src/config.py.

Follows the established matrix pattern (see tests/test_safe_selector.py /
test_recruiter_score.py):
- Pure-function routing tests with monkeypatched provider functions.
- No live Ollama server, no network, no installed `ollama` package required.
- One focused test_* function per behavioural guarantee.

Goal: proves that (a) the provider dispatcher routes to _ollama when
provider=="ollama", (b) the default model selection honors the
ollama_model prefs key, (c) provider_ready() returns False cleanly
when Ollama isn't installed/running (no crash, no hang), and (d)
the _ollama function raises a friendly LLMError when the server is down.
"""
from __future__ import annotations

import sys
import types
from typing import Any

import pytest


# --- Fixtures: stub out the vendor package and config ------------------------

def _stub_ollama_module(monkeypatch: pytest.MonkeyPatch, *, raise_on_chat: Exception | None = None,
                       chat_response: Any = None) -> types.ModuleType:
    """Install a fake `ollama` module in sys.modules and return it.

    The stub records the chat kwargs on the module so tests can assert on
    them. If raise_on_chat is set, client.chat() raises it (simulating a
    down server or missing model).
    """
    fake = types.ModuleType("ollama")

    class ResponseError(Exception):
        def __init__(self, error: str) -> None:
            super().__init__(error)
            self.error = error

    fake.ResponseError = ResponseError  # type: ignore[attr-defined]
    fake.last_chat_kwargs: dict[str, Any] = {}  # type: ignore[attr-defined]

    class FakeClient:
        def __init__(self, host: str = "") -> None:
            self.host = host

        def chat(self, **kwargs: Any) -> Any:
            fake.last_chat_kwargs.update(kwargs)
            fake.last_chat_kwargs["host"] = self.host
            if raise_on_chat is not None:
                raise raise_on_chat
            return chat_response or {"message": {"content": "stubbed reply"}}

        def list(self) -> Any:  # used by provider_ready probe
            if raise_on_chat is not None:
                raise raise_on_chat
            return {}

    fake.Client = FakeClient  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ollama", fake)
    return fake


def _set_provider(monkeypatch: pytest.MonkeyPatch, provider: str, ollama_model: str = "llama3.1:8b") -> None:
    """Monkeypatch config.provider() and load_prefs() for routing tests."""
    from src import config

    monkeypatch.setattr(config, "provider", lambda: provider)
    monkeypatch.setattr(
        config,
        "load_prefs",
        lambda: {
            "writing_model": "claude-sonnet-4-6",
            "gemini_model": "gemini-2.0-flash",
            "nvidia_model": "meta/llama-3.1-70b-instruct",
            "ollama_model": ollama_model,
            "provider": provider,
            "identity": {},
        },
    )


# --- Routing tests -----------------------------------------------------------

def test_generate_routes_to_ollama_when_provider_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    """Call generate() with provider=ollama -> _ollama runs, _claude never imported."""
    from src import llm

    fake = _stub_ollama_module(monkeypatch, chat_response={"message": {"content": "ollama says hi"}})
    _set_provider(monkeypatch, "ollama")

    # Sentinel: _claude should NOT be invoked. Replace it with a tripwire.
    def _tripwire(*args: Any, **kwargs: Any) -> str:
        raise AssertionError("_claude was called for provider=ollama")

    monkeypatch.setattr(llm, "_claude", _tripwire)
    monkeypatch.setattr(llm, "_gemini", _tripwire)
    monkeypatch.setattr(llm, "_nvidia", _tripwire)

    result = llm.generate("hello", model="llama3.1:8b")

    assert result == "ollama says hi"
    assert fake.last_chat_kwargs["model"] == "llama3.1:8b"
    assert fake.last_chat_kwargs["messages"][-1] == {"role": "user", "content": "hello"}


def test_generate_ollama_uses_default_model_when_model_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """generate(model=None) with provider=ollama falls back to prefs['ollama_model']."""
    from src import llm

    fake = _stub_ollama_module(monkeypatch, chat_response={"message": {"content": "ok"}})
    _set_provider(monkeypatch, "ollama", ollama_model="qwen2.5:7b")

    result = llm.generate("hello")

    assert result == "ok"
    assert fake.last_chat_kwargs["model"] == "qwen2.5:7b"


def test_generate_ollama_passes_system_and_cached_context(monkeypatch: pytest.MonkeyPatch) -> None:
    """cached_context + system are concatenated into one system message."""
    from src import llm

    fake = _stub_ollama_module(monkeypatch, chat_response={"message": {"content": "ok"}})
    _set_provider(monkeypatch, "ollama")

    llm.generate("prompt", system="SYS", cached_context="CTX", model="llama3.1:8b")

    msgs = fake.last_chat_kwargs["messages"]
    assert msgs[0] == {"role": "system", "content": "CTX\n\nSYS"}
    assert msgs[1] == {"role": "user", "content": "prompt"}


def test_generate_ollama_no_system_message_when_both_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """When system and cached_context are both empty, no system message is sent."""
    from src import llm

    fake = _stub_ollama_module(monkeypatch, chat_response={"message": {"content": "ok"}})
    _set_provider(monkeypatch, "ollama")

    llm.generate("prompt", model="llama3.1:8b")

    msgs = fake.last_chat_kwargs["messages"]
    assert msgs[0] == {"role": "user", "content": "prompt"}
    assert len(msgs) == 1


# --- Error handling tests ----------------------------------------------------

def test_ollama_raises_friendly_llmerror_on_connection_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """When the Ollama server is down, generate() raises LLMError with a clear message."""
    from src import llm

    # ConnectionRefusedError - simulates `ollama serve` not running.
    _stub_ollama_module(monkeypatch, raise_on_chat=ConnectionRefusedError("Connection refused"))
    _set_provider(monkeypatch, "ollama")

    with pytest.raises(llm.LLMError) as excinfo:
        llm.generate("hello", model="llama3.1:8b")
    assert "isn't running" in str(excinfo.value).lower() or "connect" in str(excinfo.value).lower()


def test_ollama_raises_llmerror_on_missing_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """If the `ollama` package isn't installed, generate() raises LLMError."""
    from src import llm

    # Force ImportError by removing the stub if present and making import fail.
    monkeypatch.setitem(sys.modules, "ollama", None)
    # Patch __import__ to raise ImportError for "ollama" only.
    real_import = __import__

    def _fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "ollama":
            raise ImportError("simulated missing package")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", _fake_import)
    _set_provider(monkeypatch, "ollama")

    with pytest.raises(llm.LLMError) as excinfo:
        llm.generate("hello", model="llama3.1:8b")
    assert "ollama" in str(excinfo.value).lower()


# --- provider_ready tests ----------------------------------------------------

def test_provider_ready_ollama_returns_false_when_server_down(monkeypatch: pytest.MonkeyPatch) -> None:
    """provider_ready() returns False (does NOT raise) when Ollama isn't running."""
    from src import config

    # No `ollama` module installed -> _ollama_ready must catch ImportError.
    monkeypatch.setitem(sys.modules, "ollama", None)
    real_import = __import__

    def _fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "ollama":
            raise ImportError("not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", _fake_import)
    monkeypatch.setattr(config, "provider", lambda: "ollama")

    assert config.provider_ready() is False


def test_provider_ready_ollama_returns_false_on_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """provider_ready() returns False on a connection error from client.list()."""
    from src import config

    fake = types.ModuleType("ollama")

    class FakeClient:
        def __init__(self, host: str = "") -> None:
            pass

        def list(self) -> Any:
            raise ConnectionRefusedError("no server")

    fake.Client = FakeClient  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ollama", fake)
    monkeypatch.setattr(config, "provider", lambda: "ollama")

    assert config.provider_ready() is False


def test_provider_ready_ollama_returns_true_when_server_up(monkeypatch: pytest.MonkeyPatch) -> None:
    """provider_ready() returns True when client.list() succeeds."""
    from src import config

    fake = types.ModuleType("ollama")

    class FakeClient:
        def __init__(self, host: str = "") -> None:
            pass

        def list(self) -> Any:
            return {"models": []}

    fake.Client = FakeClient  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ollama", fake)
    monkeypatch.setattr(config, "provider", lambda: "ollama")

    assert config.provider_ready() is True


# --- Prefs default test ------------------------------------------------------

def test_default_prefs_include_ollama_model() -> None:
    """DEFAULT_PREFS must include an ollama_model key (free-tier default)."""
    from src import config

    assert "ollama_model" in config.DEFAULT_PREFS
    # Default must be a non-empty string (the model name Ollama will pull).
    assert isinstance(config.DEFAULT_PREFS["ollama_model"], str)
    assert config.DEFAULT_PREFS["ollama_model"]
