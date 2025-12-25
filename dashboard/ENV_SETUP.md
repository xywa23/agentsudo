# Environment Variables Setup

Copy this content into your `.env.local` file:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## For Production

When deploying to production (Vercel, etc.), set:

```bash
NEXT_PUBLIC_API_URL=https://your-api-domain.com
```

## Notes

- `NEXT_PUBLIC_` prefix makes the variable available in the browser
- The API URL should point to your FastAPI backend
- No trailing slash on the URL
