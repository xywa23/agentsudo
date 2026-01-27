# Usage Guide

This guide covers advanced usage patterns for `ai-sudo`.

## Managing Permissions

You can create agents with multiple permissions:

```python
from ai_sudo import Agent

# Admin agent with full access
admin = Agent(
    name="SuperAdmin",
    scopes=["read:users", "write:users", "delete:users", "billing:manage"]
)
```

## Context Management

The `Agent.start_session()` context manager handles the `contextvars` switching automatically. This is thread-safe and async-friendly.

```python
import asyncio

async def async_task():
    with agent.start_session():
        # Context is preserved even across await points
        await perform_action()
```
