# API Reference

## Core

### `Agent`

The main identity class.

**Parameters:**
- `name` (str): The display name of the agent.
- `scopes` (List[str]): A list of permission strings.
- `role` (str): Optional role name (default: "worker").

**Methods:**
- `start_session()`: Returns a context manager that activates the agent.
- `has_scope(required_scope)`: Returns `True` if agent has the scope.

### `AgentSession`

The context manager returned by `Agent.start_session()`. 

**Methods:**
- `__enter__`: Sets the context var.
- `__exit__`: Resets the context var.

## Guard

### `@sudo`

Decorator to enforce permissions on functions.

**Parameters:**
- `scope` (str): The required scope string (e.g. "read:orders").

**Raises:**
- `PermissionDeniedError`: If no agent is active or if the agent lacks the scope.
