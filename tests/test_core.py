import pytest
from ai_sudo.core import Agent, get_current_agent

def test_agent_initialization():
    agent = Agent(name="TestBot", scopes=["read:db"])
    assert agent.name == "TestBot"
    assert "read:db" in agent.scopes
    assert agent.id is not None

def test_agent_session_context():
    agent = Agent(name="ContextBot", scopes=[])
    
    # Before session, no agent should be present
    assert get_current_agent() is None
    
    with agent.start_session():
        # Inside session, agent should be present
        current = get_current_agent()
        assert current is not None
        assert current.name == "ContextBot"
        assert current.id == agent.id
        
    # After session, context should be cleared
    assert get_current_agent() is None

def test_nested_sessions():
    # Although not a primary use case, let's see how contextvars behave
    # (Should replace the outer context)
    agent1 = Agent(name="Bot1", scopes=[])
    agent2 = Agent(name="Bot2", scopes=[])
    
    with agent1.start_session():
        assert get_current_agent().name == "Bot1"
        
        with agent2.start_session():
            assert get_current_agent().name == "Bot2"
            
        # Should return to Bot1
        assert get_current_agent().name == "Bot1"
