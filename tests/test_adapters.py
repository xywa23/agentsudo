"""
Tests for AgentSudo FastAPI Adapter
"""

import pytest
from agentsudo import Agent, PermissionDeniedError


def _fastapi_available():
    """Check if FastAPI is installed."""
    try:
        import fastapi
        return True
    except ImportError:
        return False


class TestFastAPIRegistry:
    """Test the agent registry."""
    
    @pytest.mark.skipif(not _fastapi_available(), reason="FastAPI not installed")
    def test_agent_registry(self):
        """Test agent registration and lookup."""
        from agentsudo.adapters.fastapi import register_agent, get_agent, _agent_registry
        
        # Clear registry
        _agent_registry.clear()
        
        agent = Agent(name="TestBot", scopes=["read:*"])
        
        # Register with custom ID
        aid = register_agent(agent, "test-001")
        assert aid == "test-001"
        
        # Lookup
        found = get_agent("test-001")
        assert found is agent
        
        # Unknown agent
        assert get_agent("unknown") is None


@pytest.mark.skipif(not _fastapi_available(), reason="FastAPI not installed")
class TestFastAPIIntegration:
    """Integration tests for FastAPI adapter."""
    
    @pytest.fixture
    def reader_agent(self):
        return Agent(name="ReaderBot", scopes=["read:data", "read:weather"])
    
    def test_fastapi_middleware(self, reader_agent):
        """Test FastAPI middleware and require_scope."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI, Depends
        from agentsudo.adapters.fastapi import (
            AgentSudoMiddleware,
            require_scope,
            register_agent,
        )
        
        app = FastAPI()
        register_agent(reader_agent, "reader-001")
        
        app.add_middleware(
            AgentSudoMiddleware,
            agent_header="X-Agent-ID",
            on_missing_agent="error"
        )
        
        @app.get("/weather")
        async def weather(agent = Depends(require_scope("read:weather"))):
            return {"weather": "sunny", "agent": agent.name}
        
        client = TestClient(app)
        
        # Without header - blocked
        response = client.get("/weather")
        assert response.status_code == 401
        
        # With valid agent - allowed
        response = client.get("/weather", headers={"X-Agent-ID": "reader-001"})
        assert response.status_code == 200
        assert response.json()["agent"] == "ReaderBot"
