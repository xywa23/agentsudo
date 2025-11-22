# 🛡️ AgentScope (ai-sudo)

**Mission:** The "Sudo" command for AI Agents.  
**One-Liner:** Open-source identity and permission management for non-human workers.

---

## The Problem
**The Enemy:** Hardcoded `.env` API keys (e.g., `STRIPE_SECRET_KEY`) shared by all agents.  
**The Solution:** Stop hardcoding keys. Use `ai-sudo` to generate temporary, scoped keys in 1 line of Python.

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
```python
@sudo(scope="write:refunds")
def process_refund(order_id):
    # If the agent doesn't have "write:refunds", this raises PermissionDeniedError
    print(f"Processing refund for {order_id}")
```

### 3. Run safely
```python
# Run code within the agent's session context
with support_bot.start_session():
    process_refund("order_123")
```
# ai-sudo
