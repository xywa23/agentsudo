import functools
from typing import Union, Callable, Any
from .core import get_current_agent, logger

class PermissionDeniedError(PermissionError):
    """Raised when an agent attempts an action without scope."""
    pass

def sudo(scope: str, on_deny: Union[str, Callable] = "raise"):
    """
    Decorator to enforce agent permissions.
    
    :param scope: The required permission string (e.g. "read:db")
    :param on_deny: Behavior when permission is denied.
                    - "raise" (default): Raise PermissionDeniedError
                    - "log": Log a warning and ALLOW (Audit Mode)
                    - callable: Function(agent, scope, func, args, kwargs) -> bool
                                Returns True to allow, False to deny.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 1. Identify the Agent
            agent = get_current_agent()

            if not agent:
                # Strictly enforce agent session requirements
                logger.warning(f"⚠️  BLOCK | Function '{func.__name__}' called outside an Agent Session.")
                raise PermissionDeniedError("No active agent session found.")

            # 2. Check Permissions
            if agent.has_scope(scope):
                # Authorized
                logger.info(f"✅ ALLOW | Agent: {agent.name} -> Scopes: {scope} -> Func: {func.__name__}")
                return func(*args, **kwargs)
            
            # 3. Handle Denial / Audit / Callback
            error_msg = f"Agent '{agent.name}' missing required scope: '{scope}'"
            
            if on_deny == "log":
                # Audit Mode: Log violation but PROCEED
                logger.warning(f"👀 AUDIT | [VIOLATION] {error_msg} -> Proceeding (Audit Mode)")
                return func(*args, **kwargs)
            
            elif callable(on_deny):
                # Custom Callback (e.g. Slack approval)
                logger.info(f"⏳ HOLD  | Triggering approval callback for {agent.name}...")
                allowed = on_deny(agent, scope, func, args, kwargs)
                
                if allowed:
                    logger.info(f"✅ APPROVE | Callback authorized action.")
                    return func(*args, **kwargs)
                else:
                    logger.error(f"⛔ DENY  | Callback rejected action.")
                    raise PermissionDeniedError(f"Action rejected by approval policy: {scope}")

            else:
                # Default: Block and Raise
                logger.error(f"⛔ DENY  | {error_msg}")
                raise PermissionDeniedError(error_msg)

        return wrapper
    return decorator
