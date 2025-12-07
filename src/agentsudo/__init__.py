from .core import Agent, get_current_agent
from .guard import sudo, PermissionDeniedError

# FastAPI adapter (import only when needed)
# Usage: from agentsudo.adapters.fastapi import AgentSudoMiddleware, require_scope

__all__ = ["Agent", "sudo", "PermissionDeniedError", "get_current_agent"]
