import pytest
from ai_sudo import Agent, PermissionDeniedError

try:
    from ai_sudo.integrations import ScopedModel
    from pydantic import ValidationError
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

@pytest.mark.skipif(not HAS_PYDANTIC, reason="Pydantic not installed")
def test_scoped_model_permission():
    class SensitiveData(ScopedModel):
        _required_scope = "read:secret"
        secret: str

    agent_allowed = Agent(name="Spy", scopes=["read:secret"])
    agent_denied = Agent(name="Civilian", scopes=[])

    # 1. Test Allowed
    with agent_allowed.start_session():
        model = SensitiveData(secret="top_secret")
        assert model.secret == "top_secret"

    # 2. Test Denied
    with agent_denied.start_session():
        with pytest.raises(PermissionDeniedError, match="missing required scope"):
            SensitiveData(secret="top_secret")

@pytest.mark.skipif(not HAS_PYDANTIC, reason="Pydantic not installed")
def test_scoped_model_no_session():
    class SensitiveData(ScopedModel):
        _required_scope = "read:secret"
        secret: str
        
    with pytest.raises(PermissionDeniedError, match="No active agent session"):
        SensitiveData(secret="fail")
