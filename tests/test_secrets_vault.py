"""Tests for the secrets vault hardening in src/config.py.

Matrix pattern (matches test_llm_ollama.py):
- No network, no real user data (conftest isolates SECRETS_PATH/FERNET_KEY_PATH
  into tmp_path).
- One focused test_* function per behavioural guarantee.

Guarantees under test:
(a) set_secrets -> get_secret round-trips via Fernet encryption (ciphertext at rest).
(b) get_secret FAILS CLOSED: a corrupt vault entry raises ValueError instead of
    returning ciphertext-as-key.
(c) get_secret fails closed when the Fernet key file is missing/deleted.
(d) get_secret still falls back to env vars when the vault has no entry.
(e) migrate_env_secrets moves plaintext .env values into the encrypted vault,
    is idempotent, and never writes plaintext to secrets.json.
"""
from __future__ import annotations

import json

import pytest

from src import config


# --- (a) Round-trip: secrets are encrypted at rest ---------------------------

def test_set_then_get_secret_roundtrips_encrypted() -> None:
    config.set_secrets({"anthropic_api_key": "sk-test-123"})
    assert config.get_secret("anthropic_api_key", "ANTHROPIC_API_KEY") == "sk-test-123"

    # At rest, the vault must NOT contain the plaintext value.
    raw = json.loads(config.SECRETS_PATH.read_text(encoding="utf-8"))
    stored = raw["anthropic_api_key"]
    assert stored != "sk-test-123"
    assert "sk-test-123" not in stored  # no plaintext substring either


# --- (b) Corrupt vault entry: fail closed ------------------------------------

def test_corrupt_vault_entry_raises_instead_of_returning_ciphertext(monkeypatch: pytest.MonkeyPatch) -> None:
    config._get_fernet()  # ensure a valid vault key exists first
    config.SECRETS_PATH.write_text(json.dumps({"gemini_api_key": "not-valid-fernet-ciphertext"}), encoding="utf-8")
    with pytest.raises(ValueError, match="could not be decrypted"):
        config.get_secret("gemini_api_key", "GEMINI_API_KEY")


# --- (c) Missing Fernet key: fail closed -------------------------------------

def test_missing_fernet_key_raises_rather_than_leaking_vault_contents(monkeypatch: pytest.MonkeyPatch) -> None:
    config.set_secrets({"nvidia_api_key": "nvapi-test"})
    # Simulate the key file being lost/corrupted.
    config.FERNET_KEY_PATH.unlink()
    (config.DATA_DIR / ".fernet_key").write_bytes(b"garbage-not-a-fernet-key")
    with pytest.raises(ValueError, match="encryption"):
        config.get_secret("nvidia_api_key", "NVIDIA_API_KEY")


def test_get_secret_does_not_regenerate_key_over_existing_vault(monkeypatch: pytest.MonkeyPatch) -> None:
    """A lost vault key must NOT be silently regenerated: that would make the
    existing ciphertext permanently undecryptable while pretending all is well."""
    config.set_secrets({"some_key": "some-value"})
    original_key = config.FERNET_KEY_PATH.read_bytes()
    config.FERNET_KEY_PATH.unlink()  # key "lost"
    with pytest.raises(ValueError):
        config.get_secret("some_key")
    # No new key file was created behind the caller's back.
    assert not config.FERNET_KEY_PATH.exists()
    # (cleanup so the fixture tmp dir doesn't matter, but restore for clarity)
    config.FERNET_KEY_PATH.write_bytes(original_key)


def test_malformed_vault_json_raises_instead_of_acting_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """A damaged vault must never be treated as empty — that would let a write
    overwrite real entries with a fresh key. Fail loudly instead."""
    config.SECRETS_PATH.write_text("this is not json{{{", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid secrets vault"):
        config.get_secret("some_key")
    with pytest.raises(ValueError, match="Invalid secrets vault"):
        config.set_secrets({"some_key": "value"})


# --- (d) Env fallback still works when vault is empty ------------------------

def test_env_var_fallback_when_vault_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADZUNA_APP_ID", "env-only-id")
    assert config.adzuna_creds()[0] == "env-only-id"


# --- (e) migrate_env_secrets --------------------------------------------------

def test_migrate_env_secrets_moves_plaintext_into_encrypted_vault(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_MIGRATE_KEY", "plaintext-secret")
    migrated = config.migrate_env_secrets({"TEST_MIGRATE_KEY": "test_migrate_key"})
    assert migrated == {"test_migrate_key": "test_migrate_key"}

    # Value decrypts to the original...
    assert config.get_secret("test_migrate_key") == "plaintext-secret"
    # ...and is NOT stored in plaintext.
    raw = json.loads(config.SECRETS_PATH.read_text(encoding="utf-8"))
    assert "plaintext-secret" not in raw["test_migrate_key"]


def test_migrate_env_secrets_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_MIGRATE_KEY2", "value-2")
    key_map = {"TEST_MIGRATE_KEY2": "test_migrate_key2"}
    first = config.migrate_env_secrets(key_map)
    second = config.migrate_env_secrets(key_map)
    assert first, "first migration should move the key"
    assert not second, "second migration should skip keys already in the vault"
    assert config.get_secret("test_migrate_key2") == "value-2"


def test_migrate_env_secrets_overwrites_corrupt_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    config._get_fernet()  # Test corrupt ciphertext with an available encryption key.
    config.SECRETS_PATH.write_text(json.dumps({"test_migrate_key3": "corrupt"}), encoding="utf-8")
    monkeypatch.setenv("TEST_MIGRATE_KEY3", "fresh-value")
    migrated = config.migrate_env_secrets({"TEST_MIGRATE_KEY3": "test_migrate_key3"})
    assert migrated
    assert config.get_secret("test_migrate_key3") == "fresh-value"


# --- (f) set_secrets refuses plaintext writes when the vault key is gone ------

def test_set_secrets_refuses_plaintext_when_vault_key_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "_get_fernet", lambda **kwargs: None)
    with pytest.raises(ValueError, match="plaintext"):
        config.set_secrets({"some_key": "secret-value"})
    # Nothing may have been written in plaintext.
    if config.SECRETS_PATH.exists():
        assert "secret-value" not in config.SECRETS_PATH.read_text(encoding="utf-8")


def test_set_secrets_does_not_mint_replacement_key_over_existing_vault(monkeypatch: pytest.MonkeyPatch) -> None:
    """If the vault has entries but the key file is lost, a write must fail —
    NOT silently generate a fresh key that strands every existing entry."""
    config.set_secrets({"existing_key": "existing-value"})
    config.FERNET_KEY_PATH.unlink()  # key lost; vault file still present
    with pytest.raises(ValueError, match="already"):
        config.set_secrets({"another_key": "new-value"})
    # The old ciphertext entry must be untouched (still decryptable once the
    # real key is restored).
    raw = json.loads(config.SECRETS_PATH.read_text(encoding="utf-8"))
    assert "existing_key" in raw
    assert "another_key" not in raw


def test_set_secrets_allows_fresh_vault_when_no_key_and_no_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    """Empty vault + missing key = normal first-run; write must bootstrap the vault."""
    assert not config.SECRETS_PATH.exists() or not json.loads(config.SECRETS_PATH.read_text(encoding="utf-8"))
    config.set_secrets({"fresh_key": "fresh-value"})
    assert config.get_secret("fresh_key") == "fresh-value"


def test_migrate_env_secrets_refuses_when_key_lost_over_existing_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    """Same protection as set_secrets: existing vault entries + lost key must
    NOT trigger migration that mints a replacement key over them."""
    config.set_secrets({"protected_key": "protected-value"})
    config.FERNET_KEY_PATH.unlink()  # key lost; vault still holds entries
    monkeypatch.setenv("TEST_MIGRATE_KEY4", "new-value")
    migrated = config.migrate_env_secrets({"TEST_MIGRATE_KEY4": "test_migrate_key4"})
    assert not migrated, "migration must not run over a keyless vault with entries"
    raw = json.loads(config.SECRETS_PATH.read_text(encoding="utf-8"))
    assert "test_migrate_key4" not in raw
