import contextvars
import logging
import uuid
import time
import fnmatch
import json
import threading
from typing import List, Optional, Set, Callable, Any, Dict
from datetime import datetime

# Setup local logging
logging.basicConfig(level=logging.WARNING, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("agentsudo")

# Cloud telemetry configuration
_cloud_config: Dict[str, Any] = {
    "enabled": False,
    "api_key": None,
    "endpoint": "https://hosqsdopgfmfzxhjweyt.supabase.co/functions/v1/ingest-event",
    "async_send": True,
}

def configure_cloud(api_key: str, async_send: bool = True):
    """
    Configure AgentSudo to send telemetry to the cloud dashboard.
    
    :param api_key: Your project API key from the AgentSudo dashboard
    :param async_send: Send events asynchronously (default: True)
    
    Example:
        import agentsudo
        agentsudo.configure_cloud(api_key="as_your_api_key")
    """
    _cloud_config["enabled"] = True
    _cloud_config["api_key"] = api_key
    _cloud_config["async_send"] = async_send
    logger.info("AgentSudo cloud telemetry enabled")

def _send_cloud_event(event_data: dict):
    """Send event to cloud dashboard."""
    if not _cloud_config["enabled"] or not _cloud_config["api_key"]:
        return
    
    def send():
        try:
            import urllib.request
            import urllib.error
            import ssl
            
            # Create SSL context that doesn't verify certificates (for macOS compatibility)
            # In production, users should install certificates properly
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            data = json.dumps(event_data).encode('utf-8')
            req = urllib.request.Request(
                _cloud_config["endpoint"],
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": _cloud_config["api_key"],
                },
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
                if response.status != 200 and response.status != 201:
                    logger.warning(f"Cloud telemetry failed: {response.status}")
        except Exception as e:
            logger.debug(f"Cloud telemetry error: {e}")
    
    if _cloud_config["async_send"]:
        thread = threading.Thread(target=send, daemon=True)
        thread.start()
    else:
        send()

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
    
    # Send to cloud dashboard if configured
    if _cloud_config["enabled"]:
        cloud_event = {
            "agent_name": agent_name,
            "action": "permission_check",
            "scope": scope,
            "allowed": allowed,
            "function_name": func_name,
            "metadata": {
                "source": "sdk",
                "action_type": action,
                "sdk_agent_id": agent_id,  # Local SDK agent ID for correlation
            }
        }
        _send_cloud_event(cloud_event)

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
