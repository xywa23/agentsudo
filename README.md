# 🛡️ AgentSudo

**The permission layer for AI agents.**

[![PyPI version](https://badge.fury.io/py/agentsudo.svg)](https://pypi.org/project/agentsudo/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AgentSudo is a lightweight permission engine for AI agents. Enforce scopes, approvals, and safe tool use across LangChain, LlamaIndex, FastAPI, and custom agents.

**Think of it as Auth0 for AI agents.**

---

## 🚀 Quick Start

### Install the SDK

```bash
pip install agentsudo
```

### Basic Usage

```python
from agentsudo import Agent, sudo

# Create an agent with specific permissions
support_bot = Agent(
    name="SupportBot",
    scopes=["read:orders", "write:refunds"]
)

@sudo(scope="write:refunds")
def issue_refund(order_id, amount):
    print(f"Refunding ${amount}")

# Agent can only call functions it has permission for
with support_bot.start_session():
    issue_refund("order_123", 50)  # ✅ Allowed
```

---

## 📦 Repository Structure

This is a monorepo containing:

| Directory | Description |
|-----------|-------------|
| [`sdk/`](./sdk) | Python SDK - the core permission engine |
| [`dashboard/`](./dashboard) | Next.js dashboard for managing agents |
| [`supabase/`](./supabase) | Database schema and migrations |
| [`docs/`](./docs) | Technical documentation |

---

## 🖥️ Self-Hosting

You can self-host the full AgentSudo stack (SDK + Dashboard).

### Quick Start

```bash
# Clone the repo
git clone https://github.com/xywa23/agentsudo.git
cd agentsudo

# Run setup
./setup.sh

# Start the dashboard
cd dashboard && npm run dev
```

### With Docker

```bash
docker compose up -d
```

See [SELF_HOSTING.md](./SELF_HOSTING.md) for detailed instructions.

---

## 📚 Documentation

- **[SDK Documentation](./sdk/README.md)** - Python SDK usage
- **[Self-Hosting Guide](./SELF_HOSTING.md)** - Deploy on your infrastructure
- **[Architecture](./docs/ARCHITECTURE.md)** - System design
- **[Roadmap](./docs/ROADMAP.md)** - Planned features

---

## ✨ Features

- **🔒 Scoped Permissions** - Fine-grained control over what agents can do
- **👤 Human-in-the-Loop** - Approval workflows for high-risk actions
- **📊 Audit Logging** - Track every permission check
- **🔌 Framework Agnostic** - Works with LangChain, LlamaIndex, FastAPI, or plain Python
- **🌐 Dashboard** - Visual management and monitoring (self-hostable)

---

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](./sdk/CONTRIBUTING.md) first.

---

## 📄 License

MIT License - see [LICENSE](./LICENSE) for details.

---

## 💬 Support

- 🐛 [Report a bug](https://github.com/xywa23/agentsudo/issues)
- 💡 [Request a feature](https://github.com/xywa23/agentsudo/issues)
- 💬 [Discussions](https://github.com/xywa23/agentsudo/discussions)

---

Made with ❤️ by [@xywa23](https://github.com/xywa23)

**⭐ Star this repo if you find it useful!**
