"""Central configuration: paths, API keys, model choices, and user preferences.

Design goals (this tool is meant for a non-coder):
- Everything can be set INSIDE the app on the Setup page. No file editing required.
- A `.env` file is also supported for people who prefer it.
- API keys live in ``data/secrets.json`` (git-ignored). Non-secret settings live in
  ``data/preferences.json``. The parsed resume lives in ``data/profile.json``.
- Getters read from disk on each call, so changes made in the app apply immediately
  without restarting.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from cryptography.fernet import Fernet

# --- Paths -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUTS_DIR = DATA_DIR / "outputs"
DB_PATH = DATA_DIR / "jobfinder.db"
PROFILE_PATH = DATA_DIR / "profile.json"  # Legacy single profile path
PROFILES_DIR = DATA_DIR / "profiles"
PREFS_PATH = DATA_DIR / "preferences.json"
SECRETS_PATH = DATA_DIR / "secrets.json"
FERNET_KEY_PATH = DATA_DIR / ".fernet_key"
ENV_PATH = ROOT / ".env"

# Avoid import-time side-effects during tests
if not os.environ.get("JOBFINDER_TEST_MODE"):
    # Ensure data directories exist on import.
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    # Load .env if present (used only as a fallback for secrets).
    load_dotenv(ENV_PATH)


# --- Small JSON helpers ------------------------------------------------------
def _load_json(path: Path, default: Any) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def _save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# --- Secrets (API keys) ------------------------------------------------------
def _get_fernet(create_if_missing: bool = True) -> Fernet | None:
    """Return the vault cipher. Never regenerates a key when one already exists
    (per Fernet docs, losing the original key makes existing ciphertext
    permanently undecryptable — silently replacing it would destroy the vault).
    Returns None when no key exists and create_if_missing is False, or when the
    key file is unreadable/corrupt."""
    try:
        if not FERNET_KEY_PATH.exists():
            if not create_if_missing:
                return None
            key = Fernet.generate_key()
            FERNET_KEY_PATH.write_bytes(key)
            return Fernet(key)
        return Fernet(FERNET_KEY_PATH.read_bytes())
    except Exception:
        return None

def _load_secrets() -> dict[str, str]:
    """Read the vault strictly: damaged data must never look like an empty vault."""
    try:
        raw = SECRETS_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except (OSError, UnicodeError):
        raise ValueError("Cannot read secrets vault; restore it before retrying.") from None
    try:
        secrets = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError("Invalid secrets vault JSON; restore it before retrying.") from None
    if not isinstance(secrets, dict) or any(
        not isinstance(value, str) for value in secrets.values()
    ):
        raise ValueError("Invalid secrets vault structure; expected an object of strings.")
    return secrets


def get_secret(key: str, env_var: str | None = None) -> str:
    """Return a secret from data/secrets.json, falling back to an env var.

    Fail-closed: a value stored in the vault that cannot be decrypted is treated
    as corrupt ciphertext and raises, instead of being returned as if it were a
    usable key (silently sending ciphertext to an API provider).
    """
    secrets = _load_secrets()
    val = str(secrets.get(key, "") or "").strip()
    if val:
        f = _get_fernet(create_if_missing=False)
        if f:
            try:
                return f.decrypt(val.encode("utf-8")).decode("utf-8")
            except Exception as e:
                raise ValueError(
                    f"Secret '{key}' in data/secrets.json could not be decrypted "
                    f"(vault key mismatch or corrupt entry). Re-enter it on the "
                    f"Setup page to re-encrypt it. Original error: {e}"
                ) from e
        # No Fernet key available at all: do not return raw vault contents.
        raise ValueError(
            f"Secret '{key}' is present in data/secrets.json but the encryption "
            f"key (data/.fernet_key) is unreadable. Restore that key file or "
            f"re-enter the secret on the Setup page."
        )
    return (os.getenv(env_var or key.upper()) or "").strip()


def migrate_env_secrets(env_keys: dict[str, str] | None = None) -> dict[str, str]:
    """One-time migration: move plaintext keys from .env into the encrypted vault.

    Returns the dict of key names that were migrated. Idempotent — keys already
    in the vault are left untouched. Does NOT delete .env (the owner should
    rotate the exposed keys, then remove the file manually).
    """
    default_map = {
        "NVIDIA_API_KEY": "nvidia_api_key",
        "NARA_API_KEY": "nara_api_key",
        "GEMINI_API_KEY": "gemini_api_key",
        "APIFY_API_TOKEN": "apify_api_token",
        "ANTHROPIC_API_KEY": "anthropic_api_key",
        "ADZUNA_APP_ID": "adzuna_app_id",
        "ADZUNA_APP_KEY": "adzuna_app_key",
    }
    key_map = env_keys or default_map
    migrated: dict[str, str] = {}
    secrets = _load_secrets()
    # Migration bootstraps the vault (creates the key if absent); reads must not.
    # But when entries exist, only the ORIGINAL key can keep them readable.
    has_entries = any(str(v or "").strip() for v in secrets.values())
    f = _get_fernet(create_if_missing=not has_entries)
    if f is None:
        return migrated
    for env_name, vault_name in key_map.items():
        env_val = (os.getenv(env_name) or "").strip()
        if not env_val:
            continue
        # Skip if a (decryptable) value already exists in the vault.
        existing = str(secrets.get(vault_name, "") or "").strip()
        if existing:
            try:
                f.decrypt(existing.encode("utf-8"))
                continue  # already migrated
            except Exception:
                pass  # corrupt entry — overwrite it
        secrets[vault_name] = f.encrypt(env_val.encode("utf-8")).decode("utf-8")
        migrated[vault_name] = vault_name
    if migrated:
        _save_json(SECRETS_PATH, secrets)
    return migrated


def set_secrets(updates: dict[str, str]) -> None:
    """Store secrets in data/secrets.json, encrypted with the Fernet vault key.

    Fail-closed on write: if the vault key is unavailable, refuse to store the
    value as plaintext (which would silently weaken the vault).
    """
    secrets = _load_secrets()
    # If the vault already holds entries, its original key is REQUIRED: creating
    # a fresh key here would strand every existing entry as undecryptable.
    has_entries = any(str(v or "").strip() for v in secrets.values())
    f = _get_fernet(create_if_missing=not has_entries)
    for k, v in updates.items():
        v = (v or "").strip()
        if v:
            if f is None:
                if has_entries:
                    # Vault already holds entries but the key is lost — refuse.
                    raise ValueError(
                        f"Cannot store secret '{k}': the encryption key "
                        f"(data/.fernet_key) is missing, and the vault already "
                        f"contains entries that need that key. Restore the key "
                        f"file or clear data/secrets.json before retrying."
                    )
                raise ValueError(
                    f"Cannot store secret '{k}': the encryption key "
                    f"(data/.fernet_key) is unreadable. Refusing to write "
                    f"plaintext secrets. Fix or delete data/.fernet_key and retry."
                )
            v = f.encrypt(v.encode("utf-8")).decode("utf-8")
        secrets[k] = v
    _save_json(SECRETS_PATH, secrets)


def anthropic_key() -> str:
    return get_secret("anthropic_api_key", "ANTHROPIC_API_KEY")


def gemini_key() -> str:
    return get_secret("gemini_api_key", "GEMINI_API_KEY")


def adzuna_creds() -> tuple[str, str]:
    return (
        get_secret("adzuna_app_id", "ADZUNA_APP_ID"),
        get_secret("adzuna_app_key", "ADZUNA_APP_KEY"),
    )

def database_url() -> str:
    # Use postgres URL from env or secrets, fallback to None (which implies SQLite)
    return get_secret("database_url", "DATABASE_URL") or "postgresql://ai_jobs:ai_jobs_password@127.0.0.1:5432/ai_jobs_db"

def redis_url() -> str:
    return get_secret("redis_url", "REDIS_URL") or "redis://127.0.0.1:6379/0"

def proxy_url() -> str:
    return get_secret("proxy_url", "PROXY_URL")


# --- Preferences (non-secret settings) ---------------------------------------
DEFAULT_PREFS: dict[str, Any] = {
    "provider": (os.getenv("PROVIDER") or "claude").lower(),
    "identity": {
        "full_name": os.getenv("FULL_NAME", ""),
        "email": os.getenv("EMAIL_ADDRESS", ""),
        "phone": os.getenv("PHONE", ""),
        "location": os.getenv("LOCATION", "Remote"),
        "linkedin": os.getenv("LINKEDIN_URL", ""),
        "physical_address": os.getenv("PHYSICAL_ADDRESS", "123 Business Rd, Suite 100, City, ST 12345"),
    },
    # Job-search filters
    "titles": [],            # e.g. ["Backend Engineer", "Python Developer"]
    "keywords": [],          # skills/terms to match against postings
    "seniority": "",         # "Intern" | "Junior" | "Mid" | "Senior" | ""
    "min_salary": 0,         # 0 = no minimum
    "exclude": [],           # words that disqualify a posting (e.g. "clearance")
    "greenhouse_boards": ["stripe", "figma", "notion", "airbnb", "coinbase", "datadog", "plaid", "ramp", "brex", "vercel"],
    "lever_boards": ["netflix", "twitch", "github"],
    "sources": ["remotive", "remoteok", "arbeitnow", "himalayas", "jobicy", "adzuna", "greenhouse", "lever", "weworkremotely", "hackernews"],
    # Outreach
    "outreach_daily_cap": int(os.getenv("OUTREACH_DAILY_CAP", "15") or "15"),
    # Local Chrome Session (Optional)
    "chrome_user_data_dir": "",
    # Models (override here if you want)
    "scoring_model": "claude-haiku-4-5-20251001",
    "writing_model": "claude-sonnet-4-6",
    "gemini_model": "gemini-2.0-flash",
    "nvidia_model": "meta/llama-3.1-70b-instruct",
    # Ollama = free-tier local LLM. Default to llama3.1:8b (Apache-2.0 weights,
    # ~4.7GB GGUF Q4). User can swap via prefs. Other free options:
    # "qwen2.5:7b" (Apache-2.0), "gemma3:4b" (Gemma terms), "phi3:mini" (MIT).
    "ollama_model": os.environ.get("OLLAMA_MODEL", "llama3.1:8b"),
}


def load_prefs() -> dict[str, Any]:
    saved = _load_json(PREFS_PATH, {})
    prefs = dict(DEFAULT_PREFS)
    prefs.update(saved or {})
    # Make sure nested identity always has all keys.
    identity = dict(DEFAULT_PREFS["identity"])
    identity.update(prefs.get("identity") or {})
    prefs["identity"] = identity
    return prefs


def save_prefs(prefs: dict[str, Any]) -> None:
    _save_json(PREFS_PATH, prefs)


def provider() -> str:
    return (load_prefs().get("provider") or "claude").lower()


def identity() -> dict[str, str]:
    return load_prefs()["identity"]


# --- Parsed resume profile ---------------------------------------------------
def list_profiles() -> list[str]:
    """Return names of all saved profile files."""
    return [p.stem for p in PROFILES_DIR.glob("*.json")]

import re

def _validate_profile_name(name: str) -> str:
    """Ensure name doesn't contain path traversal characters."""
    if not re.match(r'^[\w\-\.]+$', name) or ".." in name:
        raise ValueError("Invalid profile name")
    return name

def load_profile(name: str | None = None) -> dict[str, Any]:
    """Load a named profile, or the active one."""
    if name is None:
        name = load_prefs().get("active_profile", "default")
    name = _validate_profile_name(name)
    path = PROFILES_DIR / f"{name}.json"
    if path.exists():
        return _load_json(path, {})
    # Fallback: migrate legacy single profile.json if it exists
    return _load_json(PROFILE_PATH, {})

def save_profile(data: dict[str, Any], name: str | None = None) -> None:
    if name is None:
        name = load_prefs().get("active_profile", "default")
    name = _validate_profile_name(name)
    _save_json(PROFILES_DIR / f"{name}.json", data)


# --- Readiness checks --------------------------------------------------------
def provider_ready() -> bool:
    """True if the selected AI provider is ready to serve requests."""
    p = provider()
    if p == "auto":
        return True
    if p == "gemini":
        return bool(gemini_key())
    if p == "nvidia":
        return bool(get_secret("nvidia_api_key", "NVIDIA_API_KEY"))
    if p == "ollama":
        # Ollama is keyless + local. "Ready" means the server is up and the
        # selected model is pulled. We do a lightweight best-effort probe and
        # treat any failure as not-ready (UI will nudge the user to start it).
        return _ollama_ready()
    return bool(anthropic_key())


def _ollama_ready() -> bool:
    """Best-effort Ollama server probe. Never raises; False = not ready."""
    try:
        try:
            import ollama  # type: ignore
        except ImportError:
            return False
        host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
        client = ollama.Client(host=host)
        # Heartbeat: list local models. If the server is down this raises, and
        # we return False. We do NOT require the target model to be pulled -
        # the first chat request will prompt the pull.
        client.list()
        return True
    except Exception:
        return False


def readiness() -> dict[str, bool]:
    """Quick status used by the dashboard to nudge setup steps."""
    return {
        "ai_key": provider_ready(),
        "resume": bool(load_profile()),
        "identity": bool(identity().get("full_name")),
    }
