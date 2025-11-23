import pytest
from ai_sudo import Agent, sudo, PermissionDeniedError

# Fixtures
@pytest.fixture
def read_agent():
    return Agent(name="ReadBot", scopes=["read:db"])

@pytest.fixture
def admin_agent():
    return Agent(name="AdminBot", scopes=["read:db", "write:db"])

# Mock Functions
@sudo(scope="read:db")
def read_database():
    return "data"

@sudo(scope="write:db")
def write_database():
    return "written"

@sudo(scope="write:db", on_deny="log")
def write_audit_mode():
    return "written_audit"

# Tests
def test_no_session_raises_error():
    with pytest.raises(PermissionDeniedError, match="No active agent session"):
        read_database()

def test_authorized_access(read_agent):
    with read_agent.start_session():
        assert read_database() == "data"

def test_denied_access(read_agent):
    with read_agent.start_session():
        with pytest.raises(PermissionDeniedError, match="missing required scope"):
            write_database()

def test_audit_mode_allows_execution(read_agent):
    # ReadAgent does NOT have write:db, but on_deny="log" should allow it
    with read_agent.start_session():
        assert write_audit_mode() == "written_audit"

def test_callback_approval(read_agent):
    # Define a callback that approves everything
    def always_yes(agent, scope, func, args, kwargs):
        return True
        
    @sudo(scope="write:db", on_deny=always_yes)
    def write_callback():
        return "approved"
        
    with read_agent.start_session():
        assert write_callback() == "approved"

def test_callback_denial(read_agent):
    # Define a callback that denies everything
    def always_no(agent, scope, func, args, kwargs):
        return False
        
    @sudo(scope="write:db", on_deny=always_no)
    def write_callback():
        return "approved"
        
    with read_agent.start_session():
        with pytest.raises(PermissionDeniedError, match="Action rejected by approval policy"):
            write_callback()
