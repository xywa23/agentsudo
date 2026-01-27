from typing import Optional, ClassVar
import logging
from .core import get_current_agent, logger, _log_action
from .guard import PermissionDeniedError

try:
    from pydantic import BaseModel, model_validator
except ImportError:
    raise ImportError("Pydantic is required for ScopedModel. Run `pip install pydantic`.")

class ScopedModel(BaseModel):
    """
    A Pydantic Model that enforces agent permissions upon instantiation.
    
    Usage:
        class RefundParams(ScopedModel):
            order_id: str
            
            # Define the scope required to instantiate this model
            _required_scope: ClassVar[str] = "write:refunds"
            
    """
    # Using ClassVar to avoid Pydantic thinking it's a field
    _required_scope: ClassVar[Optional[str]] = None

    @model_validator(mode='after')
    def check_permissions(self):
        # 1. Check if a scope is defined on the class
        required_scope = getattr(self, "_required_scope", None)
        
        if not required_scope:
            return self

        # 2. Identify Agent
        agent = get_current_agent()
        model_name = self.__class__.__name__
        
        if not agent:
            logger.warning(f"BLOCK | ScopedModel '{model_name}' instantiated outside Agent Session.")
            raise PermissionDeniedError(
                f"ScopedModel '{model_name}' requires an active agent session. "
                f"Use: with agent.start_session(): ..."
            )

        # 3. Enforce Scope
        if not agent.has_scope(required_scope):
            error_msg = (
                f"Agent '{agent.name}' missing required scope: '{required_scope}' for model '{model_name}'. "
                f"Agent has: {list(agent.scopes)}."
            )
            
            _log_action("model_access_denied", agent.id, agent.name, required_scope, model_name, False, level=logging.ERROR)
            raise PermissionDeniedError(error_msg)
            
        _log_action("model_access_granted", agent.id, agent.name, required_scope, model_name, True, level=logging.DEBUG)
        return self
