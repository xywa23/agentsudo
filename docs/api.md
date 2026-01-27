# AgentSudo API Reference

Complete API documentation for AgentSudo v0.1.1+

---

## Core Module (`agentsudo.core`)

### `Agent`

The main identity class representing an AI agent with specific permissions.

```python
Agent(name: str, scopes: List[str], role: str = "worker", session_ttl: int = 3600)
```

**Parameters:**
- `name` (str): The display name of the agent (e.g., "SupportBot")
- `scopes` (List[str]): List of permission strings. Supports wildcards (e.g., `["read:*", "write:orders"]`)
- `role` (str, optional): Role identifier. Default: `"worker"`
- `session_ttl` (int, optional): Session timeout in seconds. Default: `3600` (1 hour)

**Attributes:**
- `id` (str): Unique UUID for the agent instance
- `name` (str): Agent name
- `scopes` (Set[str]): Set of permission scopes
- `role` (str): Agent role
- `session_ttl` (int): Session timeout duration
- `session_expires_at` (Optional[float]): Unix timestamp when session expires

**Methods:**

#### `start_session() -> AgentSession`
Returns a context manager that activates the agent's session.

```python
with agent.start_session():
    # Code runs with agent's permissions
    protected_function()
```

#### `has_scope(required_scope: str) -> bool`
Check if the agent has a specific scope. Supports wildcard matching.

**Parameters:**
- `required_scope` (str): The scope to check (e.g., `"read:users"`)

**Returns:**
- `bool`: `True` if agent has the scope (exact or wildcard match), `False` otherwise

**Examples:**
```python
agent = Agent(name="Bot", scopes=["read:*", "write:orders"])

agent.has_scope("read:users")    # True (matches read:*)
agent.has_scope("read:orders")   # True (matches read:*)
agent.has_scope("write:orders")  # True (exact match)
agent.has_scope("write:users")   # False
agent.has_scope("delete:orders") # False
```

---

### `AgentSession`

Context manager for agent sessions. Created by `Agent.start_session()`.

**Lifecycle:**
1. `__enter__`: Sets agent in context, starts session timer, logs session start
2. `__exit__`: Clears agent from context, logs session end

**Logging:**
Emits structured JSON logs:
```json
{"event": "session_start", "agent_name": "SupportBot", "expires_in_seconds": 3600}
{"event": "session_end", "agent_name": "SupportBot"}
```

---

## Guard Module (`agentsudo.guard`)

### `@sudo`

Decorator to enforce permissions on functions.

```python
@sudo(scope: str, on_deny: Union[str, Callable] = "raise")
def protected_function():
    pass
```

**Parameters:**
- `scope` (str): Required permission scope (e.g., `"write:refunds"`)
- `on_deny` (Union[str, Callable], optional): Behavior when permission is denied:
  - `"raise"` (default): Raise `PermissionDeniedError`
  - `"log"`: Log violation but allow execution (Audit Mode)
  - `Callable`: Custom approval function with signature:
    ```python
    def callback(agent: Agent, scope: str, context: dict) -> bool:
        # Return True to allow, False to deny
        pass
    ```

**Raises:**
- `PermissionDeniedError`: When:
  - No active agent session
  - Agent session expired
  - Agent lacks required scope (and `on_deny="raise"`)
  - Approval callback returns `False`

**Examples:**

#### Basic Usage
```python
@sudo(scope="read:users")
def get_user(user_id):
    return db.query(user_id)
```

#### Audit Mode
```python
@sudo(scope="write:database", on_deny="log")
def update_record(record_id):
    # Logs violation but executes anyway
    db.update(record_id)
```

#### Approval Callback
```python
def slack_approval(agent, scope, context):
    response = slack.ask_manager(f"Approve {agent.name} for {scope}?")
    return response == "yes"

@sudo(scope="delete:customer", on_deny=slack_approval)
def delete_customer(customer_id):
    db.delete(customer_id)
```

**Logging:**
Emits structured JSON logs at different levels:
- `DEBUG`: Successful authorization (not logged by default)
- `WARNING`: Audit violations, session expiry, no active session
- `ERROR`: Access denied, callback rejection

Example log:
```json
{
  "timestamp": "2025-11-24T23:30:00.000000",
  "action": "access_denied",
  "agent_id": "abc-123",
  "agent_name": "SupportBot",
  "scope": "delete:users",
  "function": "delete_user",
  "allowed": false
}
```

---

### `PermissionDeniedError`

Exception raised when an agent attempts an unauthorized action.

```python
class PermissionDeniedError(PermissionError):
    pass
```

**Inherits from:** `PermissionError`

**Common Messages:**
- `"Function 'delete_user' requires an active agent session. Use: with agent.start_session(): ..."`
- `"Agent session expired. Start a new session."`
- `"Agent 'SupportBot' missing required scope: 'delete:users'. Agent has: ['read:users', 'write:tickets']."`
- `"Action rejected by approval policy: delete:customer"`

---

## Integrations Module (`agentsudo.integrations`)

### `ScopedModel`

Pydantic base model that enforces permissions during instantiation.

```python
from agentsudo.integrations import ScopedModel

class MyModel(ScopedModel):
    _required_scope: ClassVar[str] = "write:refunds"
    
    order_id: str
    amount: float
```

**Usage:**
```python
agent = Agent(name="Bot", scopes=["write:refunds"])

with agent.start_session():
    # ✅ Allowed
    model = MyModel(order_id="123", amount=50.0)

agent2 = Agent(name="Bot2", scopes=["read:orders"])

with agent2.start_session():
    # ❌ Raises PermissionDeniedError
    model = MyModel(order_id="123", amount=50.0)
```

**Class Variables:**
- `_required_scope` (ClassVar[Optional[str]]): The scope required to instantiate this model

**Validation:**
Runs during Pydantic's `@model_validator(mode='after')` phase.

**Raises:**
- `PermissionDeniedError`: If no active session or agent lacks scope

**Requirements:**
- Requires `pydantic` to be installed: `pip install pydantic`

---

## Wildcard Scope Matching

AgentSudo supports Unix-style wildcard patterns using `fnmatch`:

| Pattern | Matches | Doesn't Match |
|---------|---------|---------------|
| `read:*` | `read:users`, `read:orders`, `read:anything` | `write:users` |
| `write:orders*` | `write:orders`, `write:orders_archive` | `write:users` |
| `*` | Everything | Nothing |
| `admin:*:delete` | `admin:users:delete`, `admin:orders:delete` | `admin:users:read` |

**Implementation:**
Uses Python's `fnmatch.fnmatch()` for pattern matching.

---

## Session Expiry

Sessions automatically expire after `session_ttl` seconds.

**Default:** 3600 seconds (1 hour)

**Behavior:**
- Session timer starts when `with agent.start_session():` is entered
- All `@sudo` decorated functions check expiry before execution
- Expired sessions raise `PermissionDeniedError`

**Example:**
```python
agent = Agent(
    name="TempBot",
    scopes=["read:*"],
    session_ttl=60  # 1 minute
)

with agent.start_session():
    read_data()  # ✅ Works
    time.sleep(61)
    read_data()  # ❌ PermissionDeniedError: session expired
```

---

## Logging Configuration

AgentSudo uses Python's `logging` module.

**Default Level:** `WARNING` (only shows violations/errors)

**Enable Debug Logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Structured JSON Output:**
All logs are JSON-formatted for SIEM integration:
```python
import json
import logging

# Parse logs programmatically
for line in log_file:
    event = json.loads(line)
    if event.get("action") == "access_denied":
        alert_security_team(event)
```

---

## Error Handling Best Practices

### 1. Catch Specific Exceptions
```python
from agentsudo import PermissionDeniedError

try:
    with agent.start_session():
        dangerous_function()
except PermissionDeniedError as e:
    logger.error(f"Permission denied: {e}")
    # Handle gracefully
```

### 2. Validate Agent Scopes Before Session
```python
required_scopes = ["write:refunds", "send:email"]

if all(agent.has_scope(s) for s in required_scopes):
    with agent.start_session():
        process_refund()
else:
    print("Agent missing required scopes")
```

### 3. Use Audit Mode for Rollout
```python
# Phase 1: Deploy with audit mode
@sudo(scope="write:db", on_deny="log")
def update_db():
    pass

# Phase 2: After monitoring, switch to blocking
@sudo(scope="write:db")  # on_deny="raise" is default
def update_db():
    pass
```

---

## Type Hints

AgentSudo is fully typed. Use with mypy/pyright:

```python
from agentsudo import Agent, sudo
from typing import List

def create_agent(name: str, scopes: List[str]) -> Agent:
    return Agent(name=name, scopes=scopes)

@sudo(scope="read:users")
def get_user(user_id: str) -> dict:
    return {"id": user_id}
```

---

## Version History

- **v0.1.1**: Documentation update
- **v0.1.0**: Initial release
  - Core `Agent` and `@sudo` decorator
  - Wildcard scope matching
  - Session expiry
  - Audit mode
  - Approval callbacks
  - Pydantic integration
  - Structured JSON logging
