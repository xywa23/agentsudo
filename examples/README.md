# AgentSudo Examples

This directory contains practical examples demonstrating AgentSudo's features.

## Running Examples

```bash
# Install agentsudo first
pip install agentsudo

# Run any example
python examples/basic_usage.py
```

## Available Examples

### 1. `basic_usage.py`
**What it demonstrates:**
- Creating agents with different permission levels
- Protecting functions with `@sudo` decorator
- Running code in agent sessions
- Permission denied scenarios

**Run:**
```bash
python examples/basic_usage.py
```

---

### 2. `wildcard_scopes.py`
**What it demonstrates:**
- Using wildcard patterns (`read:*`, `write:orders*`, `*`)
- Flexible permission matching
- God-mode agents

**Run:**
```bash
python examples/wildcard_scopes.py
```

---

### 3. `audit_mode.py`
**What it demonstrates:**
- Non-blocking audit mode (`on_deny="log"`)
- Logging violations without breaking execution
- Safe production rollout strategy

**Run:**
```bash
python examples/audit_mode.py
```

---

### 4. `approval_workflow.py`
**What it demonstrates:**
- Human-in-the-loop approval callbacks
- Custom approval logic
- Slack/Teams integration pattern

**Run:**
```bash
python examples/approval_workflow.py
```

---

### 5. `pydantic_integration.py`
**What it demonstrates:**
- Enforcing permissions on Pydantic models
- `ScopedModel` usage
- LangChain/LlamaIndex integration pattern

**Requirements:**
```bash
pip install pydantic
```

**Run:**
```bash
python examples/pydantic_integration.py
```

---

## Creating Your Own Examples

Feel free to contribute new examples! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

**Example template:**
```python
"""
Your Example Title

Brief description of what this demonstrates.
"""

from agentsudo import Agent, sudo

@sudo(scope="your:scope")
def your_function():
    print("Protected action")

def main():
    agent = Agent(name="YourBot", scopes=["your:scope"])
    
    with agent.start_session():
        your_function()

if __name__ == "__main__":
    main()
```
