# MedGuard AI Complete Project Documentation

## 1. Project Summary

MedGuard AI is a deterministic clinical safety middleware platform with constrained AI orchestration. The system is designed to check patient-specific medication safety using database-backed rules and deterministic engines before any AI-generated explanation is shown.

This is not a generic healthcare chatbot. The LLM is not responsible for deciding whether a medication is safe. The LLM is used only after deterministic checks have created a safety result or when the user needs help clarifying an ambiguous medication name.

Core principle:

```text
Database truth -> deterministic safety validation -> constrained AI explanation
```

## 2. What The System Does

MedGuard AI supports multiple clinical query types:

- Proposed drug safety checks.
- Full current-medication review.
- Existing dangerous interaction detection.
- Allergy and cross-reactivity checks.
- Renal dosing checks.
- Deterministic clinical score calculations.
- AI-assisted but confirmation-required drug-name clarification.
- Unknown-drug safe failure.
- Generic AI versus Safe AI comparison.

Example doctor queries:

```text
Can I prescribe Clarithromycin?
Review this patient's medications for dangerous interactions.
What is this patient's stroke risk?
How severe is this patient's kidney disease?
Can I add clarith?
```

## 3. System Philosophy

The system separates responsibilities very strictly:

```text
Database = validated clinical truth
Deterministic engines = safety decision layer
LLM = explanation and clarification layer
Frontend = clinical review interface
```

The LLM never determines medication safety.

The LLM cannot:

- approve a medication
- override a hard block
- invent drug interaction facts
- bypass deterministic validation
- silently choose an ambiguous medication
- replace allergy, renal, interaction, or calculator engines

The LLM can:

- explain deterministic alerts
- phrase safe responses more naturally
- compare generic AI with constrained Safe AI
- ask clarification questions using validated candidate names

## 4. High-Level Architecture

```text
Doctor Query
  -> Frontend Dashboard
  -> FastAPI Backend
  -> Intent Classifier
  -> Entity Resolver, when medication-specific
  -> Deterministic Safety Engines
  -> Clinical Calculator Engine
  -> Constraint Generator
  -> Generic AI and Safe AI Comparison
  -> Frontend Alert Display
```

Detailed backend flow:

```text
POST /api/safety-check
  -> SafetyOrchestrator.check()
      -> IntentClassifier.classify()
      -> route by intent
      -> EntityResolver.resolve(), if DRUG_QUERY
      -> InteractionEngine
      -> AllergyEngine
      -> RenalEngine
      -> CalculatorEngine
      -> ConstraintGenerator
      -> SafetyCheckResponse
```

## 5. Intent Routing

The intent classifier is deterministic and keyword/rule based. AI is not used to decide the route.

### DRUG_QUERY

Used when the doctor asks about adding, prescribing, starting, dosing, or checking a medication.

Examples:

```text
Can I prescribe Clarithromycin?
Can I add Gabapentin?
Is Amoxicillin safe?
```

Flow:

```text
DRUG_QUERY -> Entity Resolver -> Deterministic Safety Pipeline
```

### REVIEW_QUERY

Used when the doctor asks for a current medication audit or existing high-risk combinations.

Examples:

```text
Review this patient's medications.
Any dangerous interactions?
Are there high-risk combinations already present?
```

Flow:

```text
REVIEW_QUERY -> Full Medication Review -> Existing Interaction/Renal/Allergy Summary
```

### CALCULATOR_QUERY

Used when the doctor asks for clinical score or risk calculation.

Examples:

```text
What is this patient's stroke risk?
Calculate CHA2DS2-VASc.
What is the eGFR?
```

Flow:

```text
CALCULATOR_QUERY -> Calculator Engine -> Deterministic Scores
```

### GENERAL_QUERY

Used for general patient-context questions that are not medication lookup requests.

Examples:

```text
How severe is this patient's kidney disease?
Summarize this patient's main clinical risks.
```

Flow:

```text
GENERAL_QUERY -> Patient Context -> Safe AI explanation with deterministic score context
```

## 6. Entity Resolution Logic

The resolver converts doctor-entered medication text into validated database medication names.

Resolution order:

1. Exact DB match.
2. Alias match.
3. Prefix and partial matching.
4. Conservative fuzzy matching.
5. AI-assisted clarification text.
6. Safe unknown-drug exit.

Important safety rule:

The system never silently guesses a drug. If there are multiple likely candidates, it returns `needs_clarification` and the frontend asks the doctor to confirm.

Examples:

```text
clarith
  -> Did you mean Clarithromycin or Azithromycin?

met
  -> Did you mean Metformin, Metoprolol, or Methotrexate?

gaba
  -> Did you mean Gabapentin?

zzqnotadrug
  -> Drug not found in validated clinical database.
```

Structured response example:

```json
{
  "status": "needs_clarification",
  "resolved_name": null,
  "confidence": 0.78,
  "match_type": "partial",
  "candidates": ["Clarithromycin", "Azithromycin"]
}
```

After confirmation, the frontend sends the selected medication as `proposed_drug`, and the backend runs the deterministic safety pipeline.

## 7. Deterministic Safety Engines

### Interaction Engine

Checks the proposed medication against the patient's current medications. It also supports full review mode for existing medication interactions.

Drug pairs are normalized and stored as sorted keys:

```text
clarithromycin::atorvastatin
```

All interactions are preloaded during startup into an in-memory cache, so each pair lookup is O(1).

### Allergy Engine

Checks patient allergies against the proposed medication and drug class cross-reactivity rules.

Example:

```text
Penicillin anaphylaxis + Amoxicillin-Clavulanate
  -> HARD_BLOCK
```

### Renal Engine

Uses patient kidney function and drug renal metadata to generate renal warnings.

Example:

```text
CKD stage 3b + Gabapentin 300mg TDS
  -> renal dose adjustment warning
```

### Calculator Engine

Calculates clinical scores deterministically:

- CKD-EPI 2021 eGFR
- CHA2DS2-VASc stroke risk score

AI is not involved in these calculations.

### Constraint Generator

Converts deterministic findings into a structured safety constraint block. The Safe AI response must follow this block.

## 8. Alert Prioritization

Alerts are sorted by importance:

```text
HARD_BLOCK = 10
SEVERE     = 8
MODERATE   = 5
MINOR      = 2
```

The frontend shows the highest-risk alerts first.

## 9. Full Medication Review Mode

Full medication review checks all current patient medications, even when no new drug is proposed.

It can detect:

- existing drug-drug interactions
- renal risks in current medication list
- allergy conflicts
- monitoring requirements
- severe system-wide safety findings

Example query:

```text
Review this patient's medications for dangerous interactions and contraindications.
```

This should not trigger drug lookup. It should run a medication audit.

## 10. AI Response Design

The frontend displays two AI responses:

### Generic AI

This response is intentionally less constrained. It shows what a generic AI might say without deterministic safety middleware.

### Safe AI

This response receives deterministic constraints generated by the backend. It must obey hard blocks, warnings, renal rules, allergy rules, and unknown-drug fail-safe logic.

The UI also shows:

```text
Why Safe AI Differed
```

This explains the deterministic reasons the Safe AI response changed.

## 11. Fail-Safe Behavior

The system fails closed.

If a drug is unknown:

```text
Drug not found in validated clinical database.
Manual pharmacist review recommended.
```

If a drug is ambiguous:

```text
Please confirm the intended medication before safety validation.
```

If the LLM fails:

```text
The deterministic fallback response is used.
```

Unknown drugs are never approved. AI cannot invent safety data for unknown medications.

## 12. Backend Routes

### `GET /health`

Health check route.

Returns:

```json
{
  "status": "ok",
  "interaction_cache_pairs": 32
}
```

### `POST /api/patients`

Returns patient registry data for the frontend.

Used by:

```text
frontend/src/components/PatientSelector.jsx
```

### `POST /api/safety-check`

Main safety orchestration endpoint.

Request contains:

- patient object
- doctor query
- optional proposed drug

Returns:

- alerts
- scores
- resolved drug state
- intent
- constraints
- review summary
- why Safe AI changed

### `POST /api/ask-generic`

Calls the configured LLM in generic mode for comparison.

This is not the safety authority.

### `POST /api/ask-safe`

Calls the configured LLM with deterministic constraints.

This is the AI response the system wants clinicians to trust more, because it is constrained by deterministic findings.

### `POST /api/admin/refresh-clinical-cache`

Reloads clinical data and rebuilds the interaction cache after database changes.

## 13. Database Design

Supabase PostgreSQL stores the production clinical data.

### `drugs`

Stores validated medications:

- generic name
- normalized name
- drug class
- renal dosing metadata

### `drug_interactions`

Stores validated interaction pairs:

- drug A normalized
- drug B normalized
- severity
- mechanism
- clinical effect
- management

### `drug_aliases`

Stores aliases and abbreviations:

- alias
- actual validated drug

### `allergy_cross_reactivity`

Stores class-level allergy cross-reactivity:

- allergy class
- cross-reactive class
- percentage
- guidance

### `patients`

Stores patient context:

- demographics
- diagnoses
- current medications
- allergies
- labs
- vitals
- clinical history

## 14. Frontend Behavior

The frontend is a clinical dashboard, not a chat page.

Main UI areas:

- patient selector
- patient clinical summary
- current medication list
- allergies and labs
- deterministic safety query input
- safety alert panel
- deterministic score cards
- Generic AI versus Safe AI comparison
- "Why Safe AI Differed" panel
- safety pipeline display
- clarification modal
- query history

When the user submits a query:

```text
App.jsx
  -> api.safetyCheck()
  -> render alerts and scores
  -> if clarification needed, open ClarificationModal
  -> call api.askGeneric()
  -> call api.askSafe()
  -> update response comparison
```

## 15. File-by-File Documentation

## Root Files

### `README.md`

Main evaluator-facing project documentation. Explains project purpose, safety philosophy, architecture, setup, deployment, testing, and disclaimer.

### `architecture.md`

Technical architecture document. Explains runtime flow, file structure, deterministic engines, entity resolution, cache behavior, deployment shape, and safety contract.

### `document.md`

Complete handover document. Explains every major feature, file, route, and system behavior.

### `.gitignore`

Prevents sensitive and generated files from being committed:

- `.env`
- backend virtual environment
- logs
- frontend `node_modules`
- frontend `dist`

### `render.yaml`

Render deployment blueprint for backend and frontend services.

## Backend Files

### `backend/requirements.txt`

Python dependency list for Render/local backend deployment.

Important dependencies:

- FastAPI
- Uvicorn
- Pydantic
- Supabase client
- httpx
- psycopg
- python-dotenv
- google-generativeai optional fallback

### `backend/runtime.txt`

Specifies Python runtime for deployment.

### `backend/Procfile`

Alternative deployment start command:

```text
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### `backend/.env.example`

Template for backend environment variables.

Includes:

- Supabase keys
- Groq API key
- Groq model
- optional Gemini fallback keys

### `backend/app/main.py`

FastAPI application entry point.

Responsibilities:

- creates FastAPI app
- configures CORS
- loads interaction cache during startup
- initializes orchestrator
- includes API routers
- exposes `/health`

Startup logic:

```text
ClinicalRepository -> get interactions -> build interaction cache
```

### `backend/app/config.py`

Loads environment variables from `backend/.env`.

### `backend/app/dependencies.py`

Creates cached shared dependencies:

- `ClinicalRepository`
- `SafetyOrchestrator`

Uses `lru_cache` so the same instances are reused.

## Backend API Layer

### `backend/app/api/safety.py`

Defines safety-related routes:

- `POST /api/safety-check`
- `POST /api/admin/refresh-clinical-cache`

Main route calls:

```text
SafetyOrchestrator.check(patient, query, proposed_drug)
```

### `backend/app/api/patients.py`

Defines:

```text
POST /api/patients
```

Returns patient list from repository.

### `backend/app/api/generic_ai.py`

Defines:

```text
POST /api/ask-generic
```

Calls LLM without deterministic constraints for comparison.

### `backend/app/api/safe_ai.py`

Defines:

```text
POST /api/ask-safe
```

Calls LLM with deterministic safety constraints.

### `backend/app/api/__init__.py`

Marks `api` as a Python package.

## Backend Cache Layer

### `backend/app/cache/interaction_cache.py`

Stores interactions in memory as normalized keys.

Important logic:

```text
build(interactions)
  -> normalize each drug pair
  -> store in dict

get(drug_a, drug_b)
  -> normalize pair
  -> O(1) lookup
```

This improves performance and avoids repeated database calls for interaction checks.

## Backend Database Layer

### `backend/app/database/supabase_client.py`

Creates Supabase client when Supabase environment variables are present.

If Supabase is not configured, repository logic can use bundled seed data.

### `backend/app/database/queries.py`

Repository abstraction for clinical data.

Responsibilities:

- get drugs
- get aliases
- get interactions
- get allergy cross-reactivity rules
- get patients
- merge Supabase rows with bundled baseline data where needed

This keeps clinical data access separate from safety engine logic.

### `backend/app/database/__init__.py`

Marks `database` as a Python package.

## Backend Engine Layer

### `backend/app/engine/intent_classifier.py`

Classifies doctor query into:

- `DRUG_QUERY`
- `REVIEW_QUERY`
- `CALCULATOR_QUERY`
- `GENERAL_QUERY`

Uses deterministic keyword/rule logic.

No AI is used.

### `backend/app/engine/entity_resolver.py`

Resolves medication names safely.

Logic:

```text
exact match
alias match
prefix/partial match
conservative fuzzy match
AI clarification text
safe unknown-drug exit
```

Returns structured `ResolvedDrug` states.

### `backend/app/engine/orchestrator.py`

Main workflow coordinator.

Responsibilities:

- classify intent
- call correct workflow
- resolve drug if needed
- run safety engines
- run calculators
- generate constraints
- sort alerts
- log clinical audit events
- return `SafetyCheckResponse`

This is the central backend brain, but it is deterministic.

### `backend/app/engine/interaction_engine.py`

Checks interactions using `InteractionCache`.

Creates alerts such as:

- `DRUG_INTERACTION`
- `EXISTING_DRUG_INTERACTION`

### `backend/app/engine/allergy_engine.py`

Checks allergy conflicts and cross-reactivity.

Creates alerts such as:

- `ALLERGY_CROSS_REACTIVITY`

Can generate HARD_BLOCK alerts.

### `backend/app/engine/renal_engine.py`

Checks renal dosing rules based on patient kidney function and drug metadata.

Creates alerts such as:

- `RENAL_DOSING`

### `backend/app/engine/calculator_engine.py`

Calculates deterministic clinical scores:

- CKD-EPI 2021 eGFR
- CHA2DS2-VASc

Returns score data for backend constraints and frontend score cards.

### `backend/app/engine/constraint_generator.py`

Converts alerts and scores into text constraints for Safe AI.

The Safe AI prompt uses this output to remain aligned with deterministic findings.

### `backend/app/engine/__init__.py`

Marks `engine` as a Python package.

## Backend LLM Layer

### `backend/app/llm/gemini_client.py`

LLM client wrapper.

Despite the legacy filename, the current default provider is Groq.

Responsibilities:

- load LLM provider env variables
- call Groq chat completions API
- optionally fall back to Gemini if configured
- generate generic AI response
- generate safe constrained AI response
- generate clarification wording
- return deterministic fallback if LLM fails

### `backend/app/llm/prompts.py`

Stores prompt templates:

- generic system prompt
- safe system prompt
- patient context formatting

The safe prompt emphasizes deterministic constraints.

### `backend/app/llm/__init__.py`

Marks `llm` as a Python package.

## Backend Models

### `backend/app/models/schemas.py`

Pydantic request and response models:

- `Drug`
- `DrugInteraction`
- `AllergyCrossReactivity`
- `DrugAlias`
- `Patient`
- `ResolvedDrug`
- `SafetyCheckRequest`
- `SafetyCheckResponse`
- `AiRequest`
- `AiResponse`

These models define API contract and validation.

### `backend/app/models/alerts.py`

Defines `SafetyAlert`.

Fields:

- type
- severity
- title
- mechanism
- recommendation
- importance

### `backend/app/models/__init__.py`

Marks `models` as a Python package.

## Backend Seed Data

### `backend/app/seed/clinical_data.py`

Bundled fallback clinical data:

- drugs
- drug interactions
- aliases
- allergy cross-reactivity
- renal dosing metadata

Used when Supabase is not configured and also helps preserve assessment-critical data.

### `backend/app/seed/patients.py`

Bundled sample patient registry for local and assessment use.

### `backend/app/seed/__init__.py`

Marks `seed` as a Python package.

## Backend Utilities

### `backend/app/utils/normalize.py`

Normalizes drug names and interaction keys.

Handles:

- lowercase conversion
- punctuation cleanup
- Unicode normalization
- interaction key sorting

### `backend/app/utils/severity.py`

Maps severity to importance:

```text
HARD_BLOCK -> 10
SEVERE -> 8
MODERATE -> 5
MINOR -> 2
```

### `backend/app/utils/logger.py`

Structured logging for clinical audit events.

Tracks:

- doctor queries
- resolved drugs
- alert types
- unknown drugs
- override attempts
- medication review audits

### `backend/app/utils/__init__.py`

Marks `utils` as a Python package.

## Backend Scripts

### `backend/scripts/bootstrap_supabase.py`

Applies Supabase schema and seed SQL using `SUPABASE_DB_URL`.

Used for local database setup.

### `backend/scripts/run_backend.ps1`

Windows helper script for starting the backend dev server.

## Backend Tests

### `backend/tests/test_assessment_scenarios.py`

Main backend regression suite.

Covers:

- severe interaction scenarios
- allergy hard blocks
- renal dosing warnings
- medication review flow
- typo clarification
- ambiguous medication clarification
- unknown-drug fail-safe
- calculator query routing
- general patient question routing
- override attempt logging
- seed data breadth

## Frontend Files

### `frontend/package.json`

Frontend package definition and scripts.

Important scripts:

```text
npm run dev
npm run build
npm run preview
```

### `frontend/package-lock.json`

Locks frontend dependency versions.

### `frontend/index.html`

Vite HTML entry point.

### `frontend/.env.example`

Frontend environment variable template:

```text
VITE_API_BASE_URL=http://localhost:8000
```

### `frontend/postcss.config.js`

PostCSS configuration for Tailwind.

### `frontend/tailwind.config.js`

Tailwind configuration.

### `frontend/src/main.jsx`

React application entry point. Mounts `App` into the DOM.

### `frontend/src/App.jsx`

Main frontend coordinator.

Responsibilities:

- load patients
- manage selected patient
- manage query input
- call backend safety check
- call generic AI and safe AI endpoints
- show alerts and scores
- handle clarification modal
- update query history
- render dashboard layout

### `frontend/src/lib/api.js`

Frontend API client.

Functions:

- `patients()`
- `safetyCheck()`
- `askGeneric()`
- `askSafe()`

Also normalizes `VITE_API_BASE_URL` so deployment still works if the URL accidentally ends with `/api`.

## Frontend Components

### `frontend/src/components/PatientSelector.jsx`

Dropdown for selecting a patient from the registry.

### `frontend/src/components/PatientCard.jsx`

Displays patient demographics, diagnoses, medications, allergies, labs, and clinical context.

### `frontend/src/components/QuestionInput.jsx`

Doctor query input area and analyze button.

### `frontend/src/components/SafetyAlerts.jsx`

Displays deterministic alerts grouped and prioritized by severity.

### `frontend/src/components/SeverityBadge.jsx`

Reusable severity badge component for alert labels.

### `frontend/src/components/ClinicalScores.jsx`

Displays deterministic score cards:

- eGFR
- CHA2DS2-VASc
- stroke risk
- renal status

### `frontend/src/components/ResponseComparison.jsx`

Shows side-by-side:

- Generic AI
- Safe AI

Also shows why the Safe AI response changed.

### `frontend/src/components/ClarificationModal.jsx`

Displays candidate medications when resolver returns `needs_clarification`.

The user must select and confirm a candidate before safety validation runs.

### `frontend/src/components/QueryHistory.jsx`

Shows recent doctor queries and results.

### `frontend/src/components/LoadingOverlay.jsx`

Displays loading state during API calls.

### `frontend/src/styles/index.css`

Tailwind and global CSS styling for the clinical dashboard.

## Supabase Files

### `supabase/schema.sql`

Creates database schema:

- `drugs`
- `drug_interactions`
- `allergy_cross_reactivity`
- `drug_aliases`
- `patients`

Also creates indexes for normalized lookup.

### `supabase/seed.sql`

Inserts validated seed data:

- baseline medications
- interaction rows
- aliases
- allergy rules
- sample patients

## Docs Files

### `docs/API.md`

API reference documentation.

### `docs/ENVIRONMENT.md`

Environment variable setup guide.

### `docs/DEPLOYMENT.md`

Deployment runbook for Supabase, Render, and Vercel.

## 16. End-to-End Example

Query:

```text
Can I prescribe Clarithromycin for this patient's respiratory infection?
```

System behavior:

```text
Frontend submits query
  -> Backend classifies DRUG_QUERY
  -> Entity resolver resolves Clarithromycin
  -> Interaction engine checks current meds
  -> Finds Clarithromycin + Atorvastatin
  -> Creates SEVERE alert
  -> Calculator engine injects renal/stroke context
  -> Constraint generator creates Safe AI constraints
  -> Generic AI response is generated
  -> Safe AI response is generated with constraints
  -> Frontend displays severe alert and AI comparison
```

## 17. Deployment Summary

Backend:

```text
Render
FastAPI
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Frontend:

```text
Vercel
React + Vite
npm run build
dist output
```

Database:

```text
Supabase PostgreSQL
schema.sql
seed.sql
```

LLM:

```text
Groq
llama-3.1-8b-instant
```

## 18. Testing Summary

Backend:

```powershell
cd backend
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

Frontend:

```powershell
cd frontend
npm run build
```

Expected current status:

```text
Backend tests: 20 passing
Frontend build: passing
```

## 19. Safety Disclaimer

This project is an educational deterministic clinical safety prototype and is not intended for autonomous real-world medical use.

It does not replace licensed clinicians, pharmacists, institutional medication safety systems, or validated production clinical decision support software. All medication decisions require qualified professional review and local clinical governance.
