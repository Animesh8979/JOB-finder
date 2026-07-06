"""Thin wrapper around the AI provider (Claude by default, Gemini optional).

Why this exists:
- One place to handle API keys, model choice, retries, and prompt caching.
- ``cached_context`` (your resume profile) is sent as a cached block so repeated
  calls — scoring many jobs, tailoring several resumes — only pay for it once.
- Callers never import the vendor SDK directly.
"""
from __future__ import annotations

import json
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
        import google.generativeai as genai
    except ImportError as e:
        raise LLMError(
            "Gemini selected but 'google-generativeai' isn't installed. "
            "Run:  pip install google-generativeai  (or switch provider back to Claude)."
        ) from e

    key = config.gemini_key()
    if not key:
        raise LLMError("No Gemini API key set. Add it on the Setup page or switch to Claude.")

    genai.configure(api_key=key)
    sys_instruction = "\n\n".join(p for p in (cached_context, system) if p) or None
    gmodel = genai.GenerativeModel(model_name=model, system_instruction=sys_instruction)
    resp = gmodel.generate_content(
        prompt,
        generation_config={"temperature": temperature, "max_output_tokens": max_tokens},
    )
    result = (resp.text or "").strip()
    del gmodel
    del key
    return result


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


# --- Public API --------------------------------------------------------------
def generate(
    prompt: str,
    *,
    system: str = "",
    cached_context: str = "",
    model: str | None = None,
    max_tokens: int = 2000,
    temperature: float = 0.4,
    retries: int = 3,
    use_mcp_tools: bool = False,
) -> str:
    """Run one completion and return the text. Raises ``LLMError`` on failure."""
    prefs = config.load_prefs()
    provider = config.provider()
    if model is None:
        if provider == "gemini":
            model = prefs["gemini_model"]
        elif provider == "nvidia":
            model = prefs["nvidia_model"]
        else:
            model = prefs["writing_model"]

    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            if provider == "gemini":
                result = _gemini(prompt, system, cached_context, model, max_tokens, temperature)
            elif provider == "nvidia":
                result = _nvidia(prompt, system, cached_context, model, max_tokens, temperature)
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
