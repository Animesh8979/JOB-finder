import os
import pytest
from pathlib import Path

# Globally force test mode BEFORE any app code is imported
os.environ["JOBFINDER_TEST_MODE"] = "1"

@pytest.fixture(autouse=True)
def db_isolation(monkeypatch, tmp_path):
    """
    Ensure all tests use a temporary isolated database and directories.
    This prevents test suites from overwriting the real user's jobs or profile.
    """
    # Create isolated dirs
    isolated_data = tmp_path / "data"
    isolated_data.mkdir()
    isolated_db = isolated_data / "test_jobfinder.db"
    
    # Patch config variables
    monkeypatch.setattr("src.config.DATA_DIR", isolated_data)
    monkeypatch.setattr("src.config.DB_PATH", isolated_db)
    
    outputs_dir = isolated_data / "outputs"
    profiles_dir = isolated_data / "profiles"
    outputs_dir.mkdir()
    profiles_dir.mkdir()
    
    monkeypatch.setattr("src.config.OUTPUTS_DIR", outputs_dir)
    monkeypatch.setattr("src.config.PROFILES_DIR", profiles_dir)
    
    # Clear any cached connections in db module
    import src.db as db
    if hasattr(db._local, "conn") and db._local.conn is not None:
        try:
            db._local.conn.close()
        except:
            pass
        delattr(db._local, "conn")
        
    db.init_db()  # Ensure tables are created for tests
    
    yield
    
    # Cleanup DB connection to release lock
    if hasattr(db._local, "conn") and db._local.conn is not None:
        try:
            db._local.conn.close()
        except:
            pass
        delattr(db._local, "conn")
