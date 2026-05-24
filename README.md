# MedGuard AI

## Deterministic Clinical Safety Middleware with Constrained AI Orchestration

MedGuard AI is a clinical drug safety platform designed around deterministic medication validation, database-backed safety rules, and constrained AI-assisted communication. It is not a generic medical chatbot. The system treats the clinical database as the source of truth, runs deterministic safety engines before any AI response is trusted, and uses the LLM only for explanation, comparison, and safe medication-name clarification.

The core objective is to demonstrate how AI can be placed behind clinical safety infrastructure instead of being allowed to independently reason about medication safety.

## Project Overview

MedGuard AI validates patient-specific medication decisions through a deterministic backend before generating a clinician-facing response. A doctor can ask whether a medication is safe, request a full medication review, calculate clinical risk scores, or ask general patient-context questions. The backend classifies the query, resolves medication entities conservatively, executes deterministic safety engines, generates structured constraints, and then asks the configured LLM to explain the result within those constraints.

The platform is intentionally built as middleware:

- The database contains validated clinical facts.
- The deterministic engines make safety decisions.
- The LLM improves usability and explanation quality.
- Unknown or ambiguous medication names fail safely.
- AI responses are visibly compared against deterministic safe responses.

## Core Problem Statement

Generic medical AI systems can produce fluent but unsafe answers. In medication safety workflows, that creates serious risks:

- hallucinated drug facts
- missed drug interactions
- unsafe recommendations for allergic patients
- incorrect renal dosing advice
- overconfident answers for unknown medications
- silent guessing when a drug name is misspelled or abbreviated

Medication safety requires deterministic validation. A language model can help communicate, but it must not be the authority deciding whether a drug is safe. MedGuard AI addresses that risk by routing all safety-critical decisions through database-driven rule engines before the AI response layer is used.

## System Philosophy

MedGuard AI follows a strict safety contract:

```text
Database = clinical truth
Deterministic engine = safety validation
LLM = explanation layer
```

The LLM never determines medication safety.

The LLM is restricted from:

- deciding drug interactions
- approving medications
- overriding HARD_BLOCK alerts
- inventing unknown-drug safety information
- silently selecting ambiguous medication candidates
- replacing renal, allergy, interaction, or score engines

The LLM is allowed to:

- explain deterministic findings
- improve conversational wording
- ask clarification questions for likely medication-name matches
- show how a generic AI response differs from a constrained safe response

## Full Architecture Flow

```text
Doctor Query
  -> Intent Classifier
  -> Entity Resolver
  -> Deterministic Safety Engines
  -> Clinical Score Calculators
  -> Constraint Generator
  -> Safe AI Response
  -> Frontend Clinical Dashboard
```

Detailed routing:

```text
Doctor Query
  -> Intent Classifier
      -> DRUG_QUERY
          -> Entity Resolver
          -> Clarification if ambiguous
          -> Interaction Engine
          -> Allergy Engine
          -> Renal Engine
          -> Constraint Generator
          -> Safe AI Response

      -> REVIEW_QUERY
          -> Full Medication Review
          -> Existing Interaction Scan
          -> Allergy and Renal Review
          -> Constraint Generator
          -> Safe AI Response

      -> CALCULATOR_QUERY
          -> Calculator Engine
          -> Deterministic Clinical Scores
          -> Safe AI Response

      -> HEALTH_QUERY / GENERAL_QUERY
          -> Patient Context Summary
          -> Deterministic clinical context injection
          -> Safe AI Response
```

## Core Features

- Drug interaction checking against validated interaction rows.
- Allergy and cross-reactivity validation.
- Renal dosing and contraindication checks.
- Full medication review mode for proactive medication audits.
- Rule-based intent classification.
- Hybrid deterministic and AI-assisted typo clarification workflow.
- Deterministic CKD-EPI 2021 eGFR and CHA2DS2-VASc calculators.
- Generic AI versus Safe AI side-by-side comparison.
- "Why Safe AI Differed" explanation section.
- Fail-safe unknown-drug handling.
- Structured clinical audit logging.
- O(1) interaction cache for normalized drug-pair lookup.
- Professional clinical dashboard for patient safety review.

## Innovation: Hybrid Deterministic + AI-Assisted Entity Resolution

The entity resolver is designed to recover from real clinician input without allowing unsafe guessing.

Resolution stages:

1. Exact database match.
2. Alias match.
3. Conservative fuzzy match.
4. AI-assisted clarification fallback.
5. Safe unknown-drug exit.

This enables practical typo and abbreviation handling while preserving deterministic safety boundaries.

Examples:

```text
clarith
  -> Did you mean Clarithromycin or Azithromycin?

augment
  -> Did you mean Amoxicillin-Clavulanate?

gaba
  -> Did you mean Gabapentin?

met
  -> Did you mean Metformin, Metoprolol, or Methotrexate?
```

The resolver does not silently choose one candidate. The doctor must confirm the intended medication before the deterministic safety pipeline executes.

## Intent Classification

Intent classification is lightweight, rule-based, and deterministic. AI is not used for intent routing.

### DRUG_QUERY

Used when the doctor asks about prescribing, adding, starting, dosing, or checking a specific medication.

Examples:

```text
Can I prescribe Clarithromycin?
Can I add Gabapentin?
Is Amoxicillin safe?
```

Flow:

```text
DRUG_QUERY -> Entity Resolver -> Clarification if needed -> Safety Pipeline
```

### REVIEW_QUERY

Used for full medication audits and high-risk medication review requests.

Examples:

```text
Review this patient's medications.
Any dangerous interactions?
Are there high-risk combinations already present?
```

Flow:

```text
REVIEW_QUERY -> Full Medication Review -> Existing Risk Summary
```

### CALCULATOR_QUERY

Used for deterministic clinical score requests.

Examples:

```text
What is this patient's stroke risk?
Calculate CHA2DS2-VASc.
What is the renal function?
```

Flow:

```text
CALCULATOR_QUERY -> Calculator Engine -> Score Cards -> Safe Explanation
```

### HEALTH_QUERY / GENERAL_QUERY

Used for patient-context questions that are not medication lookups.

Examples:

```text
How severe is this patient's kidney disease?
Summarize this patient's main clinical risks.
```

Flow:

```text
HEALTH_QUERY -> Patient Context -> Deterministic Score Context -> Safe Explanation
```

## Deterministic Safety Engines

### Interaction Engine

Checks proposed and existing medications against normalized database interaction pairs. Interactions are loaded into an in-memory cache on FastAPI startup, enabling O(1) lookup for a normalized key such as:

```text
atorvastatin::clarithromycin
```

### Allergy Engine

Checks direct allergy conflicts and class-level cross-reactivity, including high-risk allergy situations such as penicillin anaphylaxis with beta-lactam exposure.

### Renal Engine

Evaluates renal dosing and contraindication rules using patient labs and drug-specific renal metadata. The engine flags medications requiring renal dose adjustment or avoidance in reduced kidney function.

### Calculator Engine

Runs deterministic clinical score calculations and injects the results into safety context and frontend score cards.

## Clinical Calculators

Clinical calculators are mathematically deterministic and do not involve AI.

### CKD-EPI 2021 eGFR

Calculates estimated glomerular filtration rate using patient age, sex, and serum creatinine. The result is used for renal dosing checks and kidney disease context.

### CHA2DS2-VASc

Calculates stroke risk for atrial fibrillation context using structured patient history and demographics. The result supports anticoagulation risk discussion and patient safety explanation.

## Clarification Workflow

When a medication name is incomplete, misspelled, or ambiguous, the resolver returns a structured clarification state:

```json
{
  "status": "needs_clarification",
  "candidates": ["Clarithromycin", "Azithromycin"]
}
```

The frontend displays a clarification modal:

```text
Did you mean:

( ) Clarithromycin
( ) Azithromycin

[Confirm]
```

Only after the doctor confirms a candidate does the backend run deterministic medication validation.

## Fail-Safe Logic

MedGuard AI prioritizes zero false negatives over aggressive matching.

Unknown drugs are never auto-approved. If no reasonable match exists, the system returns a safety warning:

```text
Drug not found in validated clinical database.
Manual pharmacist review recommended.
```

Fail-safe behavior includes:

- no hallucinated drug substitutions
- no silent candidate selection
- no downstream medication safety validation for unvalidated drugs
- no AI override of HARD_BLOCK alerts
- deterministic alert prioritization before AI explanation

Severity priority:

```text
HARD_BLOCK = 10
SEVERE     = 8
MODERATE   = 5
MINOR      = 2
```

## Tech Stack

### Frontend

- React
- Vite
- Tailwind CSS
- Lucide React icons

### Backend

- FastAPI
- Pydantic
- Uvicorn
- deterministic Python safety engines

### Database

- Supabase PostgreSQL
- SQL schema and seed files in `supabase/`

### LLM

- Groq API
- `llama-3.1-8b-instant`
- optional Gemini fallback in the backend client

### Deployment

- Frontend: Vercel or Render static site
- Backend: Render or Railway
- Database: Supabase

## Database Schema

The core database tables are:

### `drugs`

Stores validated medications, normalized drug names, drug classes, and renal dosing metadata.

### `drug_interactions`

Stores normalized drug-pair interactions with severity, mechanism, clinical effect, and management guidance.

### `drug_aliases`

Stores aliases, abbreviations, and common alternate medication names for deterministic entity resolution.

### `allergy_cross_reactivity`

Stores class-level allergy cross-reactivity rules and clinical guidance.

### `patients`

Stores patient demographics, diagnoses, current medications, allergies, labs, vitals, and structured history.

## API Documentation

Base URL in local development:

```text
http://localhost:8000
```

### Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "interaction_cache_pairs": 32
}
```

### List Patients

```http
POST /api/patients
```

Returns the seeded patient registry used by the frontend dashboard.

### Safety Check

```http
POST /api/safety-check
```

Example request:

```json
{
  "patient": {
    "id": "P-1001",
    "name": "Maya Srinivasan",
    "age": 72,
    "sex": "female",
    "race": "unspecified",
    "weight_kg": 58,
    "diagnoses": ["Atrial fibrillation", "CKD stage 3b", "Type 2 diabetes"],
    "medications": ["Warfarin", "Atorvastatin", "Metformin", "Lisinopril"],
    "allergies": ["Penicillin anaphylaxis"],
    "labs": {
      "serum_creatinine_mg_dl": 1.7,
      "potassium_mmol_l": 4.9,
      "inr": 2.4
    },
    "vitals": {},
    "history": {
      "hypertension": true,
      "diabetes": true,
      "stroke_tia": false,
      "vascular_disease": false
    }
  },
  "query": "Can I prescribe Clarithromycin for this patient's respiratory infection?",
  "proposed_drug": null
}
```

Example response shape:

```json
{
  "intent": "DRUG_QUERY",
  "resolved_drug": {
    "status": "resolved",
    "resolved_name": "Clarithromycin",
    "confidence": 1.0,
    "match_type": "exact",
    "candidates": []
  },
  "alerts": [
    {
      "type": "DRUG_INTERACTION",
      "severity": "SEVERE",
      "title": "Clarithromycin + Atorvastatin",
      "mechanism": "CYP3A4 inhibition increases statin exposure",
      "recommendation": "Avoid combination or choose a safer alternative.",
      "importance": 8
    }
  ],
  "scores": {},
  "constraints": "Deterministic safety constraints...",
  "review_summary": {},
  "why_safe_ai_changed": ["Severe safety signal detected"]
}
```

### Generic AI Comparison

```http
POST /api/ask-generic
```

Returns an unconstrained AI draft for comparison. This is intentionally shown as a contrast, not as the safety authority.

### Safe AI Response

```http
POST /api/ask-safe
```

Returns an AI response constrained by deterministic safety findings.

### Refresh Clinical Cache

```http
POST /api/admin/refresh-clinical-cache
```

Reloads interaction data and repository-backed clinical data after database updates.

## Frontend UI

The frontend is an ICU-style clinical dashboard focused on safety review rather than chatbot interaction.

Key UI areas:

- Patient registry and patient summary panel.
- Current medications, allergies, diagnoses, labs, and risk context.
- Deterministic safety check input.
- Severity-prioritized safety alerts.
- Clinical score cards for renal and stroke-risk context.
- Generic AI versus Safe AI comparison.
- "Why Safe AI Differed" explanation.
- Clarification modal for ambiguous medication names.
- Query history for assessment walkthroughs.

The visual hierarchy prioritizes HARD_BLOCK and SEVERE alerts first so the most important clinical risks are immediately visible.

## Testing

Run backend tests:

```powershell
cd backend
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

Run frontend production build:

```powershell
cd frontend
npm run build
```

The test suite covers:

- severe drug interaction detection
- penicillin allergy hard blocks
- renal dosing warnings
- full medication review workflow
- typo and abbreviation clarification
- ambiguous medication handling
- unknown-drug fail-safe behavior
- deterministic calculator routing
- general patient question routing
- override attempt logging
- assessment scenario coverage

## Installation Guide

### Backend Setup

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Optional Windows helper:

```powershell
cd backend
.\scripts\run_backend.ps1
```

### Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

### Environment Variables

Create `backend/.env` from `backend/.env.example`:

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

Create `frontend/.env` from `frontend/.env.example`:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

### Supabase Setup

Run these files in the Supabase SQL editor:

```text
supabase/schema.sql
supabase/seed.sql
```

For local bootstrap with a database connection string:

```powershell
cd backend
python scripts/bootstrap_supabase.py
```

If Supabase variables are omitted, the backend uses bundled in-memory seed data. This supports local evaluation and assessment demonstrations.

## Deployment Guide

The repository includes `render.yaml` for Render blueprint deployment.

### Backend Deployment

Backend start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Required backend environment variables:

```bash
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
LLM_PROVIDER=groq
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

### Frontend Deployment

For Vercel or Render static deployment:

```bash
npm run build
```

Output directory:

```text
dist
```

Required frontend environment variable:

```bash
VITE_API_BASE_URL=https://your-backend-url
```

## Screenshots

Add screenshots here during final submission packaging.

### Dashboard

```markdown
![MedGuard dashboard](docs/screenshots/dashboard.png)
```

### Safety Alerts

```markdown
![Severity-prioritized alerts](docs/screenshots/safety-alerts.png)
```

### AI Comparison

```markdown
![Generic AI versus Safe AI](docs/screenshots/ai-comparison.png)
```

### Clarification Modal

```markdown
![Medication clarification modal](docs/screenshots/clarification-modal.png)
```

## Scalability and Production Shape

MedGuard AI is modular by design:

- API routes are separated from deterministic engines.
- Safety engines are independently testable.
- Clinical facts live in Supabase and bundled seed data.
- Interaction lookup uses a startup cache and normalized O(1) pair keys.
- Alert prioritization is centralized and deterministic.
- AI orchestration is constrained by generated safety prompts.
- Full medication review runs across the current profile without requiring a proposed new drug.

The system can be extended by adding validated database rows, new deterministic engines, additional calculators, and more structured alert types without changing the safety philosophy.

## Assessment Readiness

MedGuard AI demonstrates:

- deterministic safety guarantees
- constrained AI orchestration
- typo-aware but confirmation-required medication resolution
- database-backed medication validation
- patient-specific risk evaluation
- generic AI versus safety-constrained AI contrast
- production-shaped deployment structure
- clear fail-safe behavior for unknown drugs

## Healthcare Disclaimer

This project is an educational deterministic clinical safety prototype and is not intended for autonomous real-world medical use.

It does not replace licensed clinicians, pharmacists, institutional clinical decision support systems, or validated production medical software. All medication decisions require qualified professional review and local clinical governance.
