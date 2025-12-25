# AgentSudo Dashboard

Next.js dashboard and documentation site for AgentSudo.

## Features

- 📚 Documentation site at `/docs`
- 🎮 Interactive playground at `/playground`
- 🎨 Beautiful UI with shadcn/ui components
- 🔐 User authentication (coming soon)
- 📊 Analytics dashboard (coming soon)

## Status

The dashboard is currently in **preview mode**. The documentation and playground are live, while the full dashboard features (agent management, analytics) are coming soon.

## Prerequisites

- Node.js 18+ 
- Supabase project configured (see `ENV_LOCAL_CONFIG.txt`)

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Copy the content from `ENV_SETUP.md` into `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) - you'll be redirected to login.

## Usage

### First Time Setup

1. Visit http://localhost:3000
2. Click "Sign up" to create an account
3. After registration, you'll be logged in automatically
4. Create your first project
5. Create agents with specific scopes
6. Copy the API key to use in your Python SDK

### Project Structure

```
dashboard/
├── app/
│   ├── page.tsx              # Home (redirects to dashboard/login)
│   ├── login/page.tsx        # Login page
│   ├── register/page.tsx     # Registration page
│   └── dashboard/page.tsx    # Main dashboard
├── components/ui/            # shadcn/ui components
├── lib/
│   ├── api.ts               # API client
│   └── utils.ts             # Utilities
└── ENV_SETUP.md             # Environment setup guide
```

## Tech Stack

- **Framework:** Next.js 15 (App Router)
- **UI:** shadcn/ui + Tailwind CSS
- **Language:** TypeScript
- **API Client:** Fetch API with custom wrapper

## Development

### Adding New Components

```bash
npx shadcn@latest add [component-name]
```

### Type Safety

All API responses are typed. See `lib/api.ts` for type definitions.

### Building for Production

```bash
npm run build
npm start
```

## Deployment

### Vercel (Recommended)

1. Push to GitHub
2. Import project in Vercel
3. Set environment variable:
   - `NEXT_PUBLIC_API_URL`: Your production API URL
4. Deploy

### Other Platforms

Build the app and deploy the `.next` folder:

```bash
npm run build
```

## Documentation

The documentation is built with MDX and located in `content/docs/`. Key pages:

- **Introduction** - Overview of AgentSudo
- **Getting Started** - Installation and quick start
- **Python SDK** - Agents, scopes, integrations
- **Dashboard** - Overview and playground

## Troubleshooting

### Styling Issues
- Run `npm install` to ensure all dependencies are installed
- Clear `.next` folder and rebuild

## Related

- **Python SDK:** See `../agentsudo/README.md`
- **GitHub Issues:** https://github.com/xywa23/agentsudo/issues
