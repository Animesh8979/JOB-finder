"""Thin wrapper around the AI provider (Claude by default, Gemini optional).

Why this exists:
- One place to handle API keys, model choice, retries, and prompt caching.
- ``cached_context`` (your resume profile) is sent as a cached block so repeated
  calls — scoring many jobs, tailoring several resumes — only pay for it once.
- Callers never import the vendor SDK directly.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Any

from . import config


class LLMError(RuntimeError):
    """Friendly, user-facing error (shown directly in the UI)."""


def _retryable(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(s in msg for s in ("overloaded", "rate", "429", "500", "502", "503", "timeout", "timed out"))


# --- Claude ------------------------------------------------------------------
def _claude(prompt: str, system: str, cached_context: str, model: str,
            max_tokens: int, temperature: float, use_mcp_tools: bool = False) -> str:
    try:
        import anthropic
    except ImportError as e:  # pragma: no cover
        raise LLMError("The 'anthropic' package isn't installed. Run setup.bat again.") from e

    key = config.anthropic_key()
    if not key:
        raise LLMError(
            "No Anthropic API key set. Open the Setup page and paste your key "
            "(get one at https://console.anthropic.com/settings/keys)."
        )

    client = anthropic.Anthropic(api_key=key)

    # Build the system blocks. The (large, reused) cached_context gets a cache marker.
    system_blocks: list[dict[str, Any]] = []
    if cached_context:
        system_blocks.append({
            "type": "text",
            "text": cached_context,
            "cache_control": {"type": "ephemeral"},
        })
    if system:
        system_blocks.append({"type": "text", "text": system})

    messages = [{"role": "user", "content": prompt}]

    # --- MCP Tools (best-effort, fully silent) ---
    tools: list[dict[str, Any]] = []
    if use_mcp_tools:
        try:
            from .mcp_client import get_available_tools, start_servers
            tools_def = get_available_tools()
            if not tools_def:
                start_servers()
                tools_def = get_available_tools()
            tools = [
                {"name": t["name"], "description": t["description"], "input_schema": t["input_schema"]}
                for t in tools_def
            ]
        except Exception:
            tools = []  # Silently continue without tools

    # --- Execution (with optional tool loop) ---
    MAX_TOOL_STEPS = 5
    step_count = 0
    result = ""
    while step_count < MAX_TOOL_STEPS:
        step_count += 1
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_blocks or system,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        resp = client.messages.create(**kwargs)
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason == "tool_use" and tools:
            from .mcp_client import call_tool
            tool_results = []
            for block in resp.content:
                if getattr(block, "type", "") == "tool_use":
                    try:
                        result_text = call_tool(block.name, block.input) or ""
                    except Exception:
                        result_text = ""
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_text,
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            result = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
            break

    if not result:
        result = "".join(
            b.text for b in resp.content if getattr(b, "type", "") == "text"
        ).strip() or "Error: Maximum tool usage steps reached."

    del client
    del key
    return result


# --- Gemini (optional) -------------------------------------------------------
def _gemini(prompt: str, system: str, cached_context: str, model: str,
            max_tokens: int, temperature: float) -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        raise LLMError(
            "Gemini selected but 'google-genai' isn't installed. "
            "Run:  pip install google-genai  (or switch provider back to Claude)."
        ) from e

    key = config.gemini_key()
    if not key:
        raise LLMError("No Gemini API key set. Add it on the Setup page or switch to Claude.")

    client = genai.Client(api_key=key)
    sys_instruction = "\n\n".join(p for p in (cached_context, system) if p) or None
    
    config_dict = {"temperature": temperature, "max_output_tokens": max_tokens}
    if sys_instruction:
        config_dict["system_instruction"] = sys_instruction

    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(**config_dict)
    )
    result = (resp.text or "").strip()
    del client
    del key
    return result


# --- Ollama (free, local, no key) -------------------------------------------
# Free-tier-first provider path: Ollama runs a local GGUF server on the user's
# machine (MIT license, one-line `winget install Ollama.Ollama`). No API key,
# no credit card, no cloud backend - the request never leaves the machine.
# Models cache to %OLLAMA_MODELS% (redirected to D:\ollama_models by
# _env_d_disk.bat for the "no C disk" constraint).
def _ollama(prompt: str, system: str, cached_context: str, model: str,
            max_tokens: int, temperature: float) -> str:
    try:
        import ollama
    except ImportError as e:  # pragma: no cover
        raise LLMError(
            "Ollama selected but the 'ollama' package isn't installed. "
            "Run:  pip install ollama   (and install the Ollama desktop server "
            "from https://ollama.com - it's free and local)."
        ) from e

    # No key check - Ollama is local and keyless. We DO verify the server is up.
    system_text = ""
    if cached_context:
        system_text += f"{cached_context}\n\n"
    if system:
        system_text += system

    messages: list[dict[str, Any]] = []
    if system_text:
        messages.append({"role": "system", "content": system_text})
    messages.append({"role": "user", "content": prompt})

    target_model = model or "llama3.1:8b"
    try:
        client = ollama.Client(host=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"))
        resp = client.chat(
            model=target_model,
            messages=messages,
            options={"temperature": temperature, "num_predict": max_tokens},
        )
    except ollama.ResponseError as e:  # model missing or server error
        raise LLMError(f"Ollama error: {e.error}") from e
    except Exception as e:  # connection refused / server not running
        msg = str(e).lower()
        if "connection" in msg or "refused" in msg or "winerror 10061" in msg:
            raise LLMError(
                "Ollama server isn't running. Start it (e.g. `ollama serve` or "
                "launch the Ollama desktop app), then retry."
            ) from e
        raise LLMError(f"Failed to connect to Ollama: {e}") from e

    content = resp.get("message", {}).get("content", "") if isinstance(resp, dict) else ""
    # Newer ollama python SDK returns an object with .message.content.
    if not content:
        content = getattr(getattr(resp, "message", None), "content", "") or ""
    return content.strip()


# --- Nvidia NIM (optional) ---------------------------------------------------
def _nvidia(prompt: str, system: str, cached_context: str, model: str,
            max_tokens: int, temperature: float) -> str:
    key = config.get_secret("nvidia_api_key", "NVIDIA_API_KEY")
    if not key:
        raise LLMError("No Nvidia NIM API key set. Add it on the Setup page.")

    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    
    system_text = ""
    if cached_context:
        system_text += f"{cached_context}\n\n"
    if system:
        system_text += system
        
    messages = []
    if system_text:
        messages.append({"role": "system", "content": system_text})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model or "meta/llama-3.1-405b-instruct",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    import httpx
    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=30.0)
        if resp.status_code == 200:
            data = resp.json()
            result = data["choices"][0]["message"]["content"].strip()
            del key
            return result
        else:
            raise LLMError(f"Nvidia NIM API error ({resp.status_code}): {resp.text}")
    except Exception as e:
        if isinstance(e, LLMError):
            raise
        raise LLMError(f"Failed to connect to Nvidia NIM: {e}")

# --- Nara Router (optional) --------------------------------------------------
def _nara(prompt: str, system: str, cached_context: str, model: str,
          max_tokens: int, temperature: float) -> str:
    key = os.getenv("NARA_API_KEY")
    if not key:
        raise LLMError("No Nara API key set.")

    url = "https://router.bynara.id/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    
    system_text = ""
    if cached_context:
        system_text += f"{cached_context}\n\n"
    if system:
        system_text += system
        
    messages = []
    if system_text:
        messages.append({"role": "system", "content": system_text})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model or "mimo-v2.5-pro",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    import httpx
    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=30.0)
        if resp.status_code == 200:
            data = resp.json()
            result = data["choices"][0]["message"]["content"].strip()
            return result
        else:
            raise LLMError(f"Nara API error ({resp.status_code}): {resp.text}")
    except Exception as e:
        if isinstance(e, LLMError):
            raise
        raise LLMError(f"Failed to connect to Nara: {e}")


# --- Auto Rotator State ------------------------------------------------------
_COOLDOWNS: dict[str, float] = {}

def _get_auto_pool() -> list[dict[str, str]]:
    """Returns list of active keys live from .env."""
    import os
    from dotenv import dotenv_values
    
    # Read live from .env so no restart is required
    env = dotenv_values(".env")
    pool = []
    
    if env.get("NVIDIA_API_KEY_1"):
        pool.append({"id": "NVIDIA_1", "provider": "nvidia", "key": env.get("NVIDIA_API_KEY_1"), "model": "meta/llama-3.1-70b-instruct"})
    if env.get("NVIDIA_API_KEY_2"):
        pool.append({"id": "NVIDIA_2", "provider": "nvidia", "key": env.get("NVIDIA_API_KEY_2"), "model": "mistralai/mixtral-8x22b-instruct-v0.1"})
    if env.get("NARA_API_KEY"):
        pool.append({"id": "NARA", "provider": "nara", "key": env.get("NARA_API_KEY"), "model": "mimo-v2.5-pro"})
    if env.get("GEMINI_API_KEY"):
        pool.append({"id": "GEMINI", "provider": "gemini", "key": env.get("GEMINI_API_KEY"), "model": "gemini-2.0-flash"})
        
    # Append Ollama only if it is actually installed and running
    from src import config
    if config._ollama_ready():
        pool.append({"id": "OLLAMA", "provider": "ollama", "key": "local", "model": "llama3.1:8b"})
        
    return pool


# --- Public API --------------------------------------------------------------
def provider_ready() -> bool:
    """Return True if any LLM provider is configured or running locally."""
    from src import config
    return config.provider_ready() or len(_get_auto_pool()) > 0


def generate(
    prompt: str,
    *,
    system: str = "",
    cached_context: str = "",
    model: str | None = None,
    max_tokens: int = 2000,
    temperature: float = 0.4,
    retries: int = 5,
    use_mcp_tools: bool = False,
) -> str:
    """Run one completion and return the text. Raises ``LLMError`` on failure."""
    prefs = config.load_prefs()
    provider = config.provider()
    if model is None:
        if provider == "gemini":
            model = prefs.get("gemini_model", "gemini-2.0-flash")
        elif provider == "nvidia":
            model = prefs.get("nvidia_model", "meta/llama-3.1-70b-instruct")
        elif provider == "ollama":
            model = prefs.get("ollama_model", "llama3.1:8b")
        elif provider == "nara":
            model = "mimo-v2.5-pro"
        elif provider != "auto":
            model = prefs.get("writing_model", "claude-sonnet-4-6")

    # Auto Rotator Path
    if provider == "auto":
        pool = _get_auto_pool()
        if not pool:
            raise LLMError("Auto provider selected but no keys found in .env (NVIDIA_API_KEY_1, NARA_API_KEY, etc).")
        
        last_exc: Exception | None = None
        for _ in range(retries):
            # Pick next available key
            now = time.time()
            available = [k for k in pool if _COOLDOWNS.get(k["id"], 0) < now]
            if not available:
                raise LLMError("All providers are currently rate-limited (in cooldown). Try again in 60 seconds.")
            
            # Simple round-robin by picking the one with oldest cooldown (or 0)
            target = sorted(available, key=lambda k: _COOLDOWNS.get(k["id"], 0))[0]
            
            try:
                import os
                if target["provider"] == "gemini":
                    # override key in os.environ temporarily for this call (since _gemini relies on it or config)
                    os.environ["GEMINI_API_KEY"] = target["key"]
                    result = _gemini(prompt, system, cached_context, target["model"], max_tokens, temperature)
                elif target["provider"] == "nvidia":
                    os.environ["NVIDIA_API_KEY"] = target["key"]
                    result = _nvidia(prompt, system, cached_context, target["model"], max_tokens, temperature)
                elif target["provider"] == "nara":
                    os.environ["NARA_API_KEY"] = target["key"]
                    result = _nara(prompt, system, cached_context, target["model"], max_tokens, temperature)
                elif target["provider"] == "ollama":
                    result = _ollama(prompt, system, cached_context, target["model"], max_tokens, temperature)
                else:
                    raise LLMError(f"Unsupported provider in auto pool: {target['provider']}")
                
                return result
            except Exception as e:
                msg = str(e).lower()
                last_exc = e
                # Check for rate limit, out of credits, or timeouts/deprecated models
                if any(k in msg for k in ["429", "quota", "too many", "rate limit", "402", "insufficient credits", "410", "gone", "end of life", "not found"]):
                    # Cooldown for 60 seconds (or practically skip it until next round)
                    _COOLDOWNS[target["id"]] = time.time() + 60
                    continue # instantly retry with next available
                elif _retryable(e):
                    # For timeouts and network errors, put on a shorter 30s cooldown and rotate
                    _COOLDOWNS[target["id"]] = time.time() + 30
                    time.sleep(1.0)
                    continue
                else:
                    raise # hard fail

        raise LLMError(f"AI auto-routing failed after trying available providers: {last_exc}")

    # Standard Path
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            if provider == "gemini":
                result = _gemini(prompt, system, cached_context, model, max_tokens, temperature)
            elif provider == "nvidia":
                result = _nvidia(prompt, system, cached_context, model, max_tokens, temperature)
            elif provider == "nara":
                result = _nara(prompt, system, cached_context, model, max_tokens, temperature)
            elif provider == "ollama":
                result = _ollama(prompt, system, cached_context, model, max_tokens, temperature)
            else:
                result = _claude(prompt, system, cached_context, model, max_tokens, temperature, use_mcp_tools)
                
            return result
        except LLMError:
            raise  # configuration problems shouldn't be retried
        except Exception as e:  # transient/network
            last_exc = e
            if attempt < retries - 1 and _retryable(e):
                time.sleep(1.5 * (attempt + 1))
                continue
            break
    raise LLMError(f"AI request failed: {last_exc}")


def extract_json(text: str) -> Any:
    """Best-effort: pull a JSON object/array out of an LLM response."""
    text = text.strip()
    # Strip code fences if present.
    fence = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    # Grab the first {...} or [...] span.
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start = text.find(open_ch)
        end = text.rfind(close_ch)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                continue
    raise LLMError("Could not parse a JSON response from the AI. Try again.")


def generate_json(prompt: str, **kwargs: Any) -> Any:
    """Like ``generate`` but instructs the model to return JSON and parses it."""
    kwargs.setdefault("temperature", 0.2)
    sys = kwargs.pop("system", "")
    sys = (sys + "\n\nRespond with ONLY valid JSON. No prose, no code fences.").strip()
    return extract_json(generate(prompt, system=sys, **kwargs))
