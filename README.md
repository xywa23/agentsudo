# 🛡️ agentsudo

**The "sudo" command for AI agents.**

[![PyPI version](https://badge.fury.io/py/agentsudo.svg)](https://pypi.org/project/agentsudo/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Stop giving your AI agents root access to everything.

---

## The Problem

Right now, your AI agents are running with God-mode access:
```python
# ❌ BEFORE: All agents share one API key
STRIPE_API_KEY = "sk_live_..."  # Root access to everything

agent.charge_customer(1000000)  # Any agent can do ANYTHING
agent.delete_database()         # No permission checks
agent.email_all_customers()     # No oversight
```

When an agent hallucinates, it's catastrophic.

---

## The Solution
```python
# ✅ AFTER: Each agent gets scoped permissions
from agentsudo import Agent, sudo

support_bot = Agent(
    name="SupportBot",
    scopes=["read:orders", "write:refunds"]
)

@sudo(scope="write:refunds")
def issue_refund(order_id, amount):
    print(f"Refunding ${amount}")

# Support bot can issue refunds
with support_bot.start_session():
    issue_refund("order_123", 50)  # ✅ Allowed

# But analytics bot cannot
analytics_bot = Agent(name="Analytics", scopes=["read:orders"])

with analytics_bot.start_session():
    issue_refund("order_123", 50)  # ❌ PermissionDeniedError
```

---

## Installation
```bash
pip install agentsudo
```

Requires Python 3.9+

---

## Quick Start

### 1. Define Agent Identities
```python
from agentsudo import Agent

# Create agents with different permission levels
admin_agent = Agent(
    name="AdminBot",
    scopes=["read:*", "write:*", "delete:*"]  # Wildcard permissions
)

support_agent = Agent(
    name="SupportBot",
    scopes=["read:orders", "write:refunds"]
)

readonly_agent = Agent(
    name="AnalyticsBot",
    scopes=["read:*"]  # Read-only access
)
```

### 2. Protect Functions with `@sudo`
```python
from agentsudo import sudo

@sudo(scope="write:refunds")
def process_refund(order_id):
    print(f"Processing refund for {order_id}")

@sudo(scope="delete:database")
def drop_table(table_name):
    print(f"Dropping table {table_name}")
```

### 3. Run Code in Agent Sessions
```python
# Admin can do everything
with admin_agent.start_session():
    process_refund("order_123")  # ✅ Allowed
    drop_table("customers")      # ✅ Allowed

# Support can only refund
with support_agent.start_session():
    process_refund("order_456")  # ✅ Allowed
    drop_table("customers")      # ❌ PermissionDeniedError

# Analytics can only read
with readonly_agent.start_session():
    process_refund("order_789")  # ❌ PermissionDeniedError
```

---

## Features

### 🔒 **Audit Mode** (Non-Blocking)

Perfect for rolling out to production without breaking existing systems:
```python
@sudo(scope="write:database", on_deny="log")
def update_record(record_id):
    # Logs violation but ALLOWS execution
    pass
```

### 👤 **Human-in-the-Loop** (Approval Workflows)

Require human approval for high-risk actions:
```python
def slack_approval(agent, scope, context):
    # Send Slack message to manager
    response = ask_slack(f"Approve {agent.name} for {scope}?")
    return response == "yes"

@sudo(scope="delete:customer", on_deny=slack_approval)
def delete_customer(customer_id):
    print(f"Deleting customer {customer_id}")
```

### 🎯 **Pydantic Integration**

Enforce permissions on data models (perfect for LangChain/LlamaIndex):
```python
from agentsudo.integrations import ScopedModel

class RefundRequest(ScopedModel):
    _required_scope = "write:refunds"
    order_id: str
    amount: float

# Raises PermissionDeniedError if agent lacks scope
request = RefundRequest(order_id="123", amount=50.0)
```

### ⏱️ **Session Expiry**

Sessions automatically expire (like JWT tokens):
```python
agent = Agent(
    name="TempBot",
    scopes=["read:*"],
    session_ttl=3600  # 1 hour
)
```

### 🌐 **Wildcard Scopes**

Use wildcards for flexible permissions:
```python
agent = Agent(
    name="PowerUser",
    scopes=[
        "read:*",        # Read anything
        "write:orders*", # Write to orders, orders_archive, etc.
    ]
)
```

---

## Real-World Example
```python
from agentsudo import Agent, sudo

# E-commerce support bot
support_bot = Agent(
    name="CustomerSupportBot",
    scopes=[
        "read:customers",
        "read:orders",
        "write:refunds",
        "send:email"
    ]
)

@sudo(scope="write:refunds")
def issue_refund(order_id, amount):
    # Call Stripe API
    stripe.Refund.create(charge=order_id, amount=amount)

@sudo(scope="send:email")
def notify_customer(customer_id, message):
    # Send email via SendGrid
    sendgrid.send(to=customer_id, body=message)

# Bot can issue refunds and notify customers
with support_bot.start_session():
    issue_refund("ch_12345", 5000)
    notify_customer("cust_67890", "Your refund is processed")
```

---

## Why AgentSudo?

| Without AgentSudo | With AgentSudo |
|-------------------|----------------|
| ❌ All agents share root API keys | ✅ Each agent has unique identity |
| ❌ Can't tell which agent did what | ✅ Full audit trail |
| ❌ No permission boundaries | ✅ Fine-grained scopes |
| ❌ Agents can do anything | ✅ Principle of least privilege |
| ❌ No approval workflows | ✅ Human-in-the-loop for risky actions |

---

## Documentation

- [Full Documentation](https://github.com/xywa23/agentsudo/wiki) _(coming soon)_
- [Examples](https://github.com/xywa23/agentsudo/tree/main/examples) _(coming soon)_
- [API Reference](https://github.com/xywa23/agentsudo/blob/main/docs/api.md) _(coming soon)_

---

## Roadmap

- [ ] Dashboard (cloud-hosted control plane)
- [ ] Rate limiting per agent
- [ ] Budget limits (cost controls)
- [ ] Slack/Teams integration for approvals
- [ ] Pre-built integrations (Salesforce, Gmail, etc.)
- [ ] Multi-agent orchestration

---

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Support

- 🐛 [Report a bug](https://github.com/xywa23/agentsudo/issues)
- 💡 [Request a feature](https://github.com/xywa23/agentsudo/issues)
- 💬 [Discussions](https://github.com/xywa23/agentsudo/discussions)

---

Made with ❤️ by [@xywa23](https://github.com/xywa23)

**⭐ Star this repo if you find it useful!**