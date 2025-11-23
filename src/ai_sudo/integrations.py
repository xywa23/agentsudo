from typing import Optional, ClassVar
from .core import get_current_agent, logger
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
        
        if not agent:
            logger.warning(f"⚠️  BLOCK | ScopedModel '{self.__class__.__name__}' instantiated outside Agent Session.")
            raise PermissionDeniedError("No active agent session found during model validation.")

        # 3. Enforce Scope
        if not agent.has_scope(required_scope):
            error_msg = f"Agent '{agent.name}' missing required scope: '{required_scope}' for model '{self.__class__.__name__}'"
            logger.error(f"⛔ DENY  | {error_msg}")
            raise PermissionDeniedError(error_msg)
            
        logger.info(f"✅ ALLOW | Agent: {agent.name} -> Scopes: {required_scope} -> Model: {self.__class__.__name__}")
        return self
