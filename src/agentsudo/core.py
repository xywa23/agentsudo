import contextvars
import logging
import uuid
import time
import fnmatch
import json
from typing import List, Optional, Set, Callable, Any
from datetime import datetime

# Setup local logging
logging.basicConfig(level=logging.WARNING, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("agentsudo")

# 1. The Context Variable
# Stores the current agent context for the executing thread.
_current_agent_ctx = contextvars.ContextVar("current_agent", default=None)

def _log_action(action: str, agent_id: str, agent_name: str, scope: str, func_name: str, allowed: bool, level: int = logging.INFO):
    """Log in structured JSON format for audit/compliance."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "agent_id": agent_id,
        "agent_name": agent_name,
        "scope": scope,
        "function": func_name,
        "allowed": allowed
    }
    
    # Log as JSON for programmatic parsing
    logger.log(level, json.dumps(log_entry))

class Agent:
    def __init__(self, name: str, scopes: List[str], role: str = "worker", session_ttl: int = 3600):
        self.id = str(uuid.uuid4())
        self.name = name
        self.scopes = set(scopes) # Use set for O(1) lookups
        self.role = role
        self.session_ttl = session_ttl # seconds
        self.session_expires_at: Optional[float] = None
        self._token = None

    def start_session(self):
        """
        Context Manager to start an agent session.
        Usage: with agent.start_session(): ...
        """
        return AgentSession(self)

    def has_scope(self, required_scope: str) -> bool:
        """
        Check if the agent has the required scope.
        Supports wildcards: 'write:*' matches 'write:refunds', 'write:emails', etc.
        """
        # Exact match
        if required_scope in self.scopes:
            return True
        
        # Wildcard match
        for scope in self.scopes:
            if fnmatch.fnmatch(required_scope, scope):
                return True
        
        return False

class AgentSession:
    def __init__(self, agent: Agent):
        self.agent = agent
        self.token = None

    def __enter__(self):
        # Set expiry
        self.agent.session_expires_at = time.time() + self.agent.session_ttl
        
        # Set the global context to this agent
        self.token = _current_agent_ctx.set(self.agent)
        
        # Structured Log (INFO)
        logger.info(json.dumps({
            "event": "session_start",
            "agent_name": self.agent.name,
            "expires_in_seconds": self.agent.session_ttl
        }))
        
        return self.agent

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Reset the context when the 'with' block ends
        _current_agent_ctx.reset(self.token)
        self.agent.session_expires_at = None
        
        # Structured Log (INFO)
        logger.info(json.dumps({
            "event": "session_end",
            "agent_name": self.agent.name
        }))

def get_current_agent() -> Optional[Agent]:
    return _current_agent_ctx.get()
