import contextvars
import logging
import uuid
from typing import List, Optional

# Setup local logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("ai-sudo")

# 1. The Context Variable
# Stores the current agent context for the executing thread.
_current_agent_ctx = contextvars.ContextVar("current_agent", default=None)

class Agent:
    def __init__(self, name: str, scopes: List[str], role: str = "worker"):
        self.id = str(uuid.uuid4())
        self.name = name
        self.scopes = set(scopes) # Use set for O(1) lookups
        self.role = role
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
        Currently supports exact string matching.
        """
        return required_scope in self.scopes

class AgentSession:
    def __init__(self, agent: Agent):
        self.agent = agent
        self.token = None

    def __enter__(self):
        # Set the global context to this agent
        self.token = _current_agent_ctx.set(self.agent)
        logger.info(f"🟢 Session STARTED | Agent: {self.agent.name} | ID: {self.agent.id}")
        return self.agent

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Reset the context when the 'with' block ends
        _current_agent_ctx.reset(self.token)
        logger.info(f"🔴 Session ENDED   | Agent: {self.agent.name}")

def get_current_agent() -> Optional[Agent]:
    return _current_agent_ctx.get()
