import functools
from .core import get_current_agent, logger

class PermissionDeniedError(PermissionError):
    """Raised when an agent attempts an action without scope."""
    pass

def sudo(scope: str):
    """
    Decorator to enforce agent permissions.
    If the current agent lacks the 'scope', the function will NOT run.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 1. Identify the Agent
            agent = get_current_agent()

            if not agent:
                # Decide behavior: Block if no agent? Or allow humans (no context)?
                # For strict security, we block.
                logger.warning(f"⚠️  BLOCK | Function '{func.__name__}' called outside an Agent Session.")
                raise PermissionDeniedError("No active agent session found.")

            # 2. Check Permissions
            if agent.has_scope(scope):
                # ✅ Authorized
                logger.info(f"✅ ALLOW | Agent: {agent.name} -> Scopes: {scope} -> Func: {func.__name__}")
                return func(*args, **kwargs)
            else:
                # ❌ Denied
                error_msg = f"Agent '{agent.name}' missing required scope: '{scope}'"
                logger.error(f"⛔ DENY  | {error_msg}")
                raise PermissionDeniedError(error_msg)

        return wrapper
    return decorator
