"""
AgentSudo FastAPI Adapter

Middleware and dependencies for protecting FastAPI endpoints.

Usage:
    from fastapi import FastAPI, Depends
    from agentsudo import Agent
    from agentsudo.adapters.fastapi import (
        AgentSudoMiddleware,
        require_scope,
        get_current_agent,
        AgentContext
    )
    
    app = FastAPI()
    
    # Option 1: Middleware (extracts agent from headers)
    app.add_middleware(AgentSudoMiddleware, agent_header="X-Agent-ID")
    
    # Option 2: Dependency injection
    @app.post("/refunds")
    async def process_refund(
        agent: Agent = Depends(require_scope("write:refunds"))
    ):
        return {"status": "refund processed", "agent": agent.name}
    
    # Option 3: Manual context
    @app.post("/emails")
    async def send_email(ctx: AgentContext = Depends()):
        with ctx.require("write:email"):
            return {"status": "email sent"}
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Union
from functools import wraps

from ..core import Agent, get_current_agent as core_get_current_agent, logger, _log_action
from ..guard import PermissionDeniedError

# Lazy import FastAPI/Starlette
try:
    from fastapi import Depends, HTTPException, Request, Response
    from fastapi.security import APIKeyHeader
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.types import ASGIApp
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    BaseHTTPMiddleware = object
    Request = None
    Response = None


def _check_fastapi():
    """Raise helpful error if FastAPI is not installed."""
    if not FASTAPI_AVAILABLE:
        raise ImportError(
            "FastAPI is required for this adapter. "
            "Install it with: pip install fastapi"
        )


# In-memory agent registry (for demo/simple use cases)
# In production, you'd look up agents from a database
_agent_registry: Dict[str, Agent] = {}


def register_agent(agent: Agent, agent_id: Optional[str] = None) -> str:
    """
    Register an agent for use with FastAPI middleware.
    
    Args:
        agent: The Agent instance to register
        agent_id: Optional custom ID (defaults to agent.id)
        
    Returns:
        The agent ID used for registration
    """
    aid = agent_id or agent.id
    _agent_registry[aid] = agent
    return aid


def get_agent(agent_id: str) -> Optional[Agent]:
    """Get a registered agent by ID."""
    return _agent_registry.get(agent_id)


class AgentSudoMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that extracts agent context from request headers.
    
    The middleware looks for an agent ID in the specified header and
    establishes an agent session for the duration of the request.
    
    Example:
        app = FastAPI()
        app.add_middleware(
            AgentSudoMiddleware,
            agent_header="X-Agent-ID",
            agent_lookup=lambda id: database.get_agent(id)
        )
    """
    
    def __init__(
        self,
        app: "ASGIApp",
        agent_header: str = "X-Agent-ID",
        agent_lookup: Optional[Callable[[str], Optional[Agent]]] = None,
        on_missing_agent: str = "error",  # "error" | "allow" | "log"
    ):
        """
        Args:
            app: The FastAPI/Starlette application
            agent_header: Header name containing the agent ID
            agent_lookup: Function to look up Agent by ID (defaults to registry)
            on_missing_agent: Behavior when no agent header is present
        """
        _check_fastapi()
        super().__init__(app)
        self.agent_header = agent_header
        self.agent_lookup = agent_lookup or get_agent
        self.on_missing_agent = on_missing_agent
    
    async def dispatch(self, request: "Request", call_next) -> "Response":
        agent_id = request.headers.get(self.agent_header)
        
        if not agent_id:
            if self.on_missing_agent == "error":
                return Response(
                    content=f"Missing required header: {self.agent_header}",
                    status_code=401
                )
            elif self.on_missing_agent == "log":
                logger.warning(f"Request without agent header: {request.url.path}")
            # Allow request to proceed without agent context
            return await call_next(request)
        
        agent = self.agent_lookup(agent_id)
        
        if not agent:
            return Response(
                content=f"Unknown agent: {agent_id}",
                status_code=401
            )
        
        # Execute request within agent session
        with agent.start_session():
            # Store agent in request state for dependency access
            request.state.agent = agent
            response = await call_next(request)
        
        return response


def require_scope(
    scope: str,
    on_deny: Union[str, Callable] = "raise"
) -> Callable:
    """
    FastAPI dependency that requires a specific scope.
    
    Args:
        scope: Required permission scope
        on_deny: Behavior when permission denied
        
    Returns:
        A FastAPI dependency that validates the scope
        
    Example:
        @app.post("/refunds")
        async def process_refund(
            agent: Agent = Depends(require_scope("write:refunds"))
        ):
            return {"agent": agent.name}
    """
    _check_fastapi()
    
    async def dependency(request: "Request") -> Agent:
        # Try to get agent from request state (set by middleware)
        agent = getattr(request.state, 'agent', None)
        
        # Fallback to context var
        if not agent:
            agent = core_get_current_agent()
        
        if not agent:
            raise HTTPException(
                status_code=401,
                detail="No agent context. Use AgentSudoMiddleware or establish session manually."
            )
        
        if agent.has_scope(scope):
            _log_action("endpoint_access_granted", agent.id, agent.name, scope, request.url.path, True, level=logging.DEBUG)
            return agent
        
        error_msg = f"Agent '{agent.name}' missing scope '{scope}' for endpoint '{request.url.path}'"
        
        if on_deny == "log":
            _log_action("endpoint_audit_violation", agent.id, agent.name, scope, request.url.path, False, level=logging.WARNING)
            return agent
        elif callable(on_deny):
            context = {"endpoint": request.url.path, "method": request.method}
            if on_deny(agent, scope, context):
                _log_action("endpoint_callback_approved", agent.id, agent.name, scope, request.url.path, True, level=logging.INFO)
                return agent
            else:
                _log_action("endpoint_callback_denied", agent.id, agent.name, scope, request.url.path, False, level=logging.ERROR)
                raise HTTPException(status_code=403, detail=f"Action rejected by approval policy")
        else:
            _log_action("endpoint_access_denied", agent.id, agent.name, scope, request.url.path, False, level=logging.ERROR)
            raise HTTPException(status_code=403, detail=error_msg)
    
    return dependency


def get_current_agent_dependency() -> Callable:
    """
    FastAPI dependency to get the current agent (without scope check).
    
    Example:
        @app.get("/whoami")
        async def whoami(agent: Agent = Depends(get_current_agent_dependency())):
            return {"agent": agent.name, "scopes": list(agent.scopes)}
    """
    _check_fastapi()
    
    async def dependency(request: "Request") -> Optional[Agent]:
        agent = getattr(request.state, 'agent', None)
        if not agent:
            agent = core_get_current_agent()
        return agent
    
    return dependency


class AgentContext:
    """
    A context manager for manual scope checking in FastAPI endpoints.
    
    Example:
        @app.post("/multi-action")
        async def multi_action(request: Request):
            ctx = AgentContext(request)
            
            with ctx.require("read:data"):
                data = fetch_data()
            
            with ctx.require("write:logs"):
                log_action(data)
            
            return {"status": "done"}
    """
    
    def __init__(self, request: "Request"):
        _check_fastapi()
        self.request = request
        self._agent = getattr(request.state, 'agent', None) or core_get_current_agent()
    
    @property
    def agent(self) -> Optional[Agent]:
        """Get the current agent."""
        return self._agent
    
    def require(self, scope: str, on_deny: str = "raise"):
        """
        Context manager that checks a scope before executing.
        
        Args:
            scope: Required permission scope
            on_deny: Behavior when denied ("raise" or "log")
        """
        return _ScopeContext(self._agent, scope, self.request.url.path, on_deny)
    
    def has_scope(self, scope: str) -> bool:
        """Check if the current agent has a scope."""
        if not self._agent:
            return False
        return self._agent.has_scope(scope)


class _ScopeContext:
    """Internal context manager for scope checking."""
    
    def __init__(self, agent: Optional[Agent], scope: str, endpoint: str, on_deny: str):
        self.agent = agent
        self.scope = scope
        self.endpoint = endpoint
        self.on_deny = on_deny
    
    def __enter__(self):
        if not self.agent:
            raise HTTPException(status_code=401, detail="No agent context")
        
        if self.agent.has_scope(self.scope):
            _log_action("context_access_granted", self.agent.id, self.agent.name, self.scope, self.endpoint, True, level=logging.DEBUG)
            return self.agent
        
        if self.on_deny == "log":
            _log_action("context_audit_violation", self.agent.id, self.agent.name, self.scope, self.endpoint, False, level=logging.WARNING)
            return self.agent
        
        _log_action("context_access_denied", self.agent.id, self.agent.name, self.scope, self.endpoint, False, level=logging.ERROR)
        raise HTTPException(
            status_code=403,
            detail=f"Agent '{self.agent.name}' missing scope '{self.scope}'"
        )
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def sudo_endpoint(scope: str, on_deny: Union[str, Callable] = "raise"):
    """
    Decorator to protect a FastAPI endpoint with scope requirements.
    
    This is an alternative to using Depends(require_scope(...)).
    
    Example:
        @app.post("/refunds")
        @sudo_endpoint(scope="write:refunds")
        async def process_refund(request: Request):
            return {"status": "done"}
    """
    _check_fastapi()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the Request object in args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get('request')
            
            if not request:
                raise HTTPException(
                    status_code=500,
                    detail="@sudo_endpoint requires Request parameter"
                )
            
            agent = getattr(request.state, 'agent', None) or core_get_current_agent()
            
            if not agent:
                raise HTTPException(status_code=401, detail="No agent context")
            
            if agent.has_scope(scope):
                _log_action("endpoint_access_granted", agent.id, agent.name, scope, request.url.path, True, level=logging.DEBUG)
                return await func(*args, **kwargs)
            
            error_msg = f"Agent '{agent.name}' missing scope '{scope}'"
            
            if on_deny == "log":
                _log_action("endpoint_audit_violation", agent.id, agent.name, scope, request.url.path, False, level=logging.WARNING)
                return await func(*args, **kwargs)
            elif callable(on_deny):
                context = {"endpoint": request.url.path, "method": request.method}
                if on_deny(agent, scope, context):
                    _log_action("endpoint_callback_approved", agent.id, agent.name, scope, request.url.path, True, level=logging.INFO)
                    return await func(*args, **kwargs)
                else:
                    _log_action("endpoint_callback_denied", agent.id, agent.name, scope, request.url.path, False, level=logging.ERROR)
                    raise HTTPException(status_code=403, detail="Action rejected by approval policy")
            else:
                _log_action("endpoint_access_denied", agent.id, agent.name, scope, request.url.path, False, level=logging.ERROR)
                raise HTTPException(status_code=403, detail=error_msg)
        
        return wrapper
    return decorator
