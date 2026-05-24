# Environment Setup

## Backend

Create `backend/.env` from `backend/.env.example`.

```bash
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_DB_URL=
LLM_PROVIDER=groq
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant
GROQ_BASE_URL=https://api.groq.com/openai/v1
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash
```

`SUPABASE_DB_URL` is only needed when applying `supabase/schema.sql` and `supabase/seed.sql` from the local bootstrap script. Get it from Supabase Project Settings > Database > Connection string.

If your database password contains special characters such as `@`, `#`, `%`, `/`, or spaces, URL-encode them in `SUPABASE_DB_URL`. Also make sure `SUPABASE_DB_URL` and `SUPABASE_URL` belong to the same Supabase project.

```bash
cd backend
python scripts/bootstrap_supabase.py
```

If Supabase variables are omitted, the backend uses the bundled in-memory seed data. This is useful for local development and evaluator runs.

Groq is the preferred LLM provider for demo responses. Gemini remains an optional fallback if `GROQ_API_KEY` is not configured.

## Frontend

Create `frontend/.env` from `frontend/.env.example`.

```bash
VITE_API_BASE_URL=http://localhost:8000
```

For Vercel, set `VITE_API_BASE_URL` to the deployed Render or Railway backend URL.

## Supabase

Run these files in the Supabase SQL editor:

1. `supabase/schema.sql`
2. `supabase/seed.sql`

The backend expects the tables `drugs`, `drug_interactions`, `allergy_cross_reactivity`, `drug_aliases`, and `patients`.
