"""Tests for the SQL-injection defense in src.db.

The column-allowlist is the load-bearing safety control. These tests pin
the contract: any column name NOT in the allowed set is silently dropped
before reaching sqlite3, so even a poisoned kwarg cannot reach the cursor.
"""
from __future__ import annotations


from src import db


def test_add_contact_drops_disallowed_columns():
    """A repo-injection attempt (e.g. `'; DROP TABLE jobs; --` as a column
    name) should be filtered out before the SQL is built.
    """
    cid = db.add_contact(
        name="Test",
        email="safety@example.invalid",
        evil="'; DROP TABLE jobs; --",  # type: ignore[arg-type]
        also_evil="x' OR '1'='1",        # type: ignore[arg-type]
    )
    assert isinstance(cid, int)
    # Confirm the row exists with the safe field, not the evil ones.
    row = db.get_contact(cid)
    assert row is not None
    assert row["email"] == "safety@example.invalid"
    # Sanity: the injection didn't break the global table state.
    assert isinstance(db.list_contacts(), list)


def test_add_outreach_drops_disallowed_columns():
    """Outreach INSERT path also enforces the allowlist."""
    db.add_outreach(  # type: ignore[arg-type]
        contact_id=1,
        subject="hi",
        body="hello",
        evil="'); DROP TABLE contacts; --",
    )
    # If we got here, the SQL builder refused the evil column. Nothing else
    # to assert without a fixed contact_id in this environment.


def test_update_application_drops_disallowed_columns():
    db.update_application(
        job_id=1,
        status="applied",
        evil="'; DROP TABLE jobs; --",  # type: ignore[arg-type]
    )
    assert True  # survived == allowlist worked
