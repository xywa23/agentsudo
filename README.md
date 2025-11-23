# 🛡️ AgentScope (ai-sudo)

**Mission:** The "Sudo" command for AI Agents.  
**One-Liner:** Open-source identity and permission management for non-human workers.

---

## The Problem
**The Enemy:** Hardcoded `.env` API keys (e.g., `STRIPE_SECRET_KEY`) shared by all agents.  
**The Solution:** Stop hardcoding keys. Use `ai-sudo` to enforce permissions and approval workflows in 1 line of Python.

## Installation

```bash
pip install ai-sudo
```

## Usage

### 1. Define the Agent Identity
```python
from ai_sudo import Agent, sudo

# Define an agent with specific permissions
support_bot = Agent(
    name="RefundBot_v1",
    scopes=["read:orders", "write:refunds"]
)
```

### 2. Protect your Tools (The "Sudo" Check)

#### A. Basic Blocking
```python
@sudo(scope="write:refunds")
def process_refund(order_id):
    # Raises PermissionDeniedError if scope is missing
    print(f"Processing refund for {order_id}")
```

#### B. Audit Mode (Non-Blocking)
Great for introducing AgentScope into existing production systems without breaking them.
```python
@sudo(scope="write:refunds", on_deny="log")
def process_refund_audit(order_id):
    # Logs a warning but ALLOWS execution
    pass
```

#### C. Human-in-the-Loop (Callbacks)
Require approval via Slack/Email before executing high-risk actions.
```python
def slack_approval(agent, scope, func, args, kwargs):
    # Return True to allow, False to deny
    return ask_slack_manager(f"Approve {agent.name} for {scope}?")

@sudo(scope="write:refunds", on_deny=slack_approval)
def process_refund_approved(order_id):
    pass
```

### 3. Pydantic Integration (Advanced)
Enforce scopes on your input schemas (ideal for LangChain/LlamaIndex).

```python
from ai_sudo.integrations import ScopedModel

class RefundParams(ScopedModel):
    _required_scope = "write:refunds"
    order_id: str
    amount: float

# If initialized by an unauthorized agent, this raises PermissionDeniedError immediately.
```

### 4. Run safely
```python
# Run code within the agent's session context
with support_bot.start_session():
    process_refund("order_123")
```

## Development & Testing

To contribute or run tests locally:

1. **Install test dependencies:**
   ```bash
   pip install ".[test]"
   ```

2. **Run the test suite:**
   ```bash
   pytest
   ```

   This runs all unit tests in `tests/` covering:
   - Core Identity & Context Management
   - Blocking, Audit, and Callback modes
   - Pydantic Integration

