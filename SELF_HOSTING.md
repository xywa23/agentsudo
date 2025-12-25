# Self-Hosting AgentSudo

This guide explains how to self-host the AgentSudo dashboard on your own infrastructure.

## Overview

AgentSudo consists of two main components:

1. **Python SDK** (`agentsudo`) - The permission engine for your AI agents
2. **Dashboard** - Web UI for managing agents, viewing analytics, and monitoring permissions

The dashboard requires:
- **Supabase** (or compatible PostgreSQL + Auth) for database and authentication
- **Node.js 18+** for the Next.js frontend

---

## Quick Start (Local Development)

### Prerequisites

- Docker & Docker Compose
- Node.js 18+
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/xywa23/agentsudo.git
cd agentsudo

# Run the setup script
./setup.sh

# Start the dashboard
cd dashboard
npm run dev
```

The dashboard will be available at http://localhost:3000

---

## Option 1: Supabase Cloud (Recommended)

The easiest way to self-host is using Supabase Cloud for the backend.

### 1. Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Note your project URL and anon key from Settings → API

### 2. Run the Database Migration

In the Supabase SQL Editor, run the contents of:
```
supabase/migrations/001_initial_schema.sql
```

This creates all required tables, RLS policies, and functions.

### 3. Configure the Dashboard

Create `dashboard/.env.local`:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### 4. Deploy the Dashboard

**Vercel (Recommended):**
```bash
cd dashboard
npx vercel
```

**Or build and run anywhere:**
```bash
cd dashboard
npm run build
npm start
```

---

## Option 2: Fully Self-Hosted (Docker)

For complete control, you can run everything locally using Docker.

### 1. Start Services

```bash
docker compose up -d
```

This starts:
- PostgreSQL database (port 54322)
- Supabase Auth (port 54324)
- Supabase REST API (port 54325)
- Supabase Studio (port 54323)
- Kong API Gateway (port 54321)

### 2. Run Migrations

The migrations in `supabase/migrations/` are automatically applied on first start.

### 3. Start the Dashboard

```bash
cd dashboard
npm install
npm run dev
```

### 4. Access

- **Dashboard:** http://localhost:3000
- **Supabase Studio:** http://localhost:54323
- **API Gateway:** http://localhost:54321

---

## Option 3: Supabase CLI (Best for Development)

The Supabase CLI provides the best local development experience.

### 1. Install Supabase CLI

```bash
# macOS
brew install supabase/tap/supabase

# npm
npm install -g supabase

# Or see: https://supabase.com/docs/guides/cli
```

### 2. Initialize and Start

```bash
cd dashboard
npx supabase init
npx supabase start
```

### 3. Link to Your Project (Optional)

To sync with a cloud project:
```bash
npx supabase link --project-ref your-project-id
npx supabase db push
```

---

## Environment Variables

See the [Environment Variables documentation](https://agentsudo.dev/docs/self-hosting/environment) for complete details.

### Quick Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | Yes |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon/public key | Yes |
| `SUPABASE_SERVICE_KEY` | Service role key (admin) | For Docker |
| `JWT_SECRET` | JWT signing secret | For Docker |
| `OPENAI_API_KEY` | For AI Playground feature | No |

Copy `.env.example` to `.env` and fill in your values.

---

## Database Schema

The dashboard uses these tables:

| Table | Description |
|-------|-------------|
| `projects` | User projects with API keys |
| `agents` | AI agents with scopes/permissions |
| `events` | Permission check events from SDK |
| `sessions` | Agent session tracking |

All tables have Row Level Security (RLS) enabled. Users can only access their own data.

---

## Deployment Options

### Vercel

```bash
cd dashboard
npx vercel --prod
```

Set environment variables in the Vercel dashboard.

### Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/agentsudo)

### Render

1. Create a new Web Service
2. Connect your GitHub repo
3. Set build command: `cd dashboard && npm install && npm run build`
4. Set start command: `cd dashboard && npm start`
5. Add environment variables

### Docker

```bash
cd dashboard
docker build -t agentsudo-dashboard .
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co \
  -e NEXT_PUBLIC_SUPABASE_ANON_KEY=your-key \
  agentsudo-dashboard
```

---

## Connecting the Python SDK

Once your dashboard is running, connect the SDK:

```python
from agentsudo import Agent

# Create an agent (matches one in your dashboard)
agent = Agent(
    name="SupportBot",
    scopes=["read:orders", "write:refunds"],
    # Optional: Enable cloud telemetry to send events to dashboard
    # api_key="as_xxx"  # Get from dashboard
)

with agent.start_session():
    # Your agent code here
    pass
```

---

## Troubleshooting

### Database connection issues

1. Ensure Supabase is running: `docker compose ps`
2. Check logs: `docker compose logs supabase-db`
3. Verify connection string in `.env.local`

### Authentication not working

1. Check `NEXT_PUBLIC_SUPABASE_URL` is correct
2. Ensure `NEXT_PUBLIC_SUPABASE_ANON_KEY` matches your project
3. For local dev, email confirmation is auto-enabled

### RLS policies blocking access

1. Ensure you're logged in (check browser console)
2. Verify the user owns the project they're accessing
3. Check Supabase logs for policy violations

---

## Support

- 📚 [Documentation](https://agentsudo.dev/docs)
- 🐛 [Report Issues](https://github.com/xywa23/agentsudo/issues)
- 💬 [Discussions](https://github.com/xywa23/agentsudo/discussions)
