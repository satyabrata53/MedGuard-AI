# Deployment Runbook

## Preflight

Local verification:

```powershell
cd backend
.\venv\Scripts\python.exe -m unittest discover -s tests -v

cd ..\frontend
npm run build
```

Do not commit `backend/.env`, `backend/venv`, `frontend/node_modules`, or `frontend/dist`.

## Supabase

In the Supabase SQL editor, run:

1. `supabase/schema.sql`
2. `supabase/seed.sql`

If you already have live demo data, be careful: the seed script resets the seeded tables.

## Render Blueprint

The root `render.yaml` defines:

- `medguard-ai-backend`: FastAPI service
- `medguard-ai-frontend`: static Vite site

In Render:

1. Push this project to GitHub.
2. Create a new Blueprint from the repository.
3. Add backend secrets:

```bash
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
GROQ_API_KEY=
```

4. Confirm these backend defaults:

```bash
LLM_PROVIDER=groq
GROQ_MODEL=llama-3.1-8b-instant
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

5. After the backend URL is created, set the frontend env var:

```bash
VITE_API_BASE_URL=https://your-render-backend-url
```

6. Redeploy the frontend service.

## Separate Frontend Deployment

If using Vercel for the frontend:

1. Import `frontend/` as the Vercel project root.
2. Build command: `npm run build`
3. Output directory: `dist`
4. Set:

```bash
VITE_API_BASE_URL=https://your-render-or-railway-backend-url
```

## Smoke Test After Deploy

Open:

```text
https://your-backend-url/health
```

Then test these UI queries:

- `Can I prescribe Clarithromycin for this patient's respiratory infection?`
- `Can I prescribe clarith?`
- `Review this patient's medications for dangerous interactions and contraindications.`
- `What is this patient's stroke risk?`
- `How severe is this patient's kidney disease?`
