import functools
import time
import logging
from typing import Union, Callable, Any
from .core import get_current_agent, logger, _log_action

class PermissionDeniedError(PermissionError):
    """Raised when an agent attempts an action without scope."""
    pass

def _send_cloud_telemetry(agent_name: str, action: str, scope: str, function_name: str, allowed: bool):
    """Send telemetry to cloud if configured (non-blocking)."""
    try:
        from .cloud import send_telemetry
        send_telemetry(
            agent_name=agent_name,
            action=action,
            scope=scope,
            allowed=allowed,
            function_name=function_name,
        )
    except ImportError:
        pass  # Cloud module not available
    except Exception:
        pass  # Don't let telemetry errors affect the main flow

def sudo(scope: str, on_deny: Union[str, Callable] = "raise"):
    """
    Decorator to enforce agent permissions.
    
    :param scope: The required permission string (e.g. "read:db")
    :param on_deny: Behavior when permission is denied.
                    - "raise" (default): Raise PermissionDeniedError
                    - "log": Log a warning and ALLOW (Audit Mode)
                    - callable: Function(agent, scope, context) -> bool
                                Returns True to allow, False to deny.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 1. Identify the Agent
            agent = get_current_agent()

            if not agent:
                logger.warning(f"BLOCK | Function '{func.__name__}' called outside an Agent Session.")
                raise PermissionDeniedError(
                    f"Function '{func.__name__}' requires an active agent session. "
                    f"Use: with agent.start_session(): ..."
                )

            # 2. Check Session Expiry
            if agent.session_expires_at and time.time() > agent.session_expires_at:
                logger.warning(f"BLOCK | Agent '{agent.name}' session expired.")
                raise PermissionDeniedError("Agent session expired. Start a new session.")

            # 3. Check Permissions
            if agent.has_scope(scope):
                # Authorized - Log at DEBUG level (not to spam)
                _log_action("access_granted", agent.id, agent.name, scope, func.__name__, True, level=logging.DEBUG)
                # Send to cloud dashboard
                _send_cloud_telemetry(agent.name, "permission_check", scope, func.__name__, True)
                return func(*args, **kwargs)
            
            # 4. Handle Denial / Audit / Callback
            error_msg = (
                f"Agent '{agent.name}' missing required scope: '{scope}'. "
                f"Agent has: {list(agent.scopes)}."
            )
            
            if on_deny == "log":
                # Audit Mode: Log violation but PROCEED
                _log_action("audit_violation", agent.id, agent.name, scope, func.__name__, False, level=logging.WARNING)
                _send_cloud_telemetry(agent.name, "audit_violation", scope, func.__name__, False)
                return func(*args, **kwargs)
            
            elif callable(on_deny):
                # Custom Callback
                # Simplified context for the callback
                context = {
                    "function": func.__name__,
                    "args": args,
                    "kwargs": kwargs
                }
                
                allowed = on_deny(agent, scope, context)
                
                if allowed:
                    _log_action("callback_approved", agent.id, agent.name, scope, func.__name__, True, level=logging.INFO)
                    _send_cloud_telemetry(agent.name, "callback_approved", scope, func.__name__, True)
                    return func(*args, **kwargs)
                else:
                    _log_action("callback_denied", agent.id, agent.name, scope, func.__name__, False, level=logging.ERROR)
                    _send_cloud_telemetry(agent.name, "callback_denied", scope, func.__name__, False)
                    raise PermissionDeniedError(f"Action rejected by approval policy: {scope}")

            else:
                # Default: Block and Raise
                _log_action("access_denied", agent.id, agent.name, scope, func.__name__, False, level=logging.ERROR)
                _send_cloud_telemetry(agent.name, "permission_denied", scope, func.__name__, False)
                raise PermissionDeniedError(error_msg)

        return wrapper
    return decorator
