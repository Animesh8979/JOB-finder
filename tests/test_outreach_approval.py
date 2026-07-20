"""Tests for HITL Outreach Approval Queue (AOS v5.0 guardrail)."""
from __future__ import annotations

import pytest
from src import db


def test_outreach_approval_lifecycle(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Use temporary sqlite db for isolation
    db_file = tmp_path / "test_outreach.db"
    monkeypatch.setattr("src.config.DB_PATH", db_file)
    db.init_db()
    
    # 1. Create a contact and an outreach draft
    cid = db.add_contact(name="Jane Doe", email="jane@example.com", company="Tech Corp")
    oid = db.add_outreach(contact_id=cid, subject="Hello Jane", body="Loved your post on ASTs", status="draft")
    
    item = db.get_outreach(oid)
    assert item is not None
    assert item["status"] == "draft"
    assert item["sent_at"] is None
    
    # 2. Approve the draft
    db.update_outreach(oid, "approved")
    item_approved = db.get_outreach(oid)
    assert item_approved["status"] == "approved"
    assert item_approved["sent_at"] is None
    
    # 3. Mark as sent
    db.update_outreach(oid, "sent")
    item_sent = db.get_outreach(oid)
    assert item_sent["status"] == "sent"
    assert item_sent["sent_at"] is not None
    
    # 4. Reject another draft
    oid2 = db.add_outreach(contact_id=cid, subject="Spammy follow up", body="Did you see my email?", status="draft")
    db.update_outreach(oid2, "rejected")
    item_rejected = db.get_outreach(oid2)
    assert item_rejected["status"] == "rejected"
