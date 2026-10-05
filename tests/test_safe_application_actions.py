from src.ats_engines.schemas import load_schema, is_action_allowed, is_field_allowed
from src.auto_apply import ApplicationSession

def test_schema_loading():
    gh_schema = load_schema("greenhouse")
    assert gh_schema is not None
    assert gh_schema["engine"] == "greenhouse"

def test_action_allowlist():
    assert is_action_allowed("greenhouse", "fill") is True
    assert is_action_allowed("greenhouse", "upload") is True
    assert is_action_allowed("greenhouse", "submit") is False
    assert is_action_allowed("greenhouse", "evaluate") is False

def test_field_allowlist():
    assert is_field_allowed("greenhouse", "first_name") is True
    assert is_field_allowed("greenhouse", "linkedin") is True
    assert is_field_allowed("greenhouse", "ssn") is False
    assert is_field_allowed("greenhouse", "password") is False

def test_application_session_mutex():
    # Enforce single-active application session mutex (lock_token)
    session1 = ApplicationSession(job_id=123)
    acquired1 = session1.acquire()
    assert acquired1 is True
    
    # Second session for same job or any job should fail if one is active globally
    session2 = ApplicationSession(job_id=124)
    acquired2 = session2.acquire()
    assert acquired2 is False
    
    session1.release()
    
    # Now session2 can acquire
    acquired3 = session2.acquire()
    assert acquired3 is True
    session2.release()
