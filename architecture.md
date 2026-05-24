# MedGuard AI Architecture

## Architectural Positioning

MedGuard AI is deterministic clinical safety middleware with constrained AI orchestration. The system is intentionally designed so that medication safety decisions are made by deterministic engines backed by validated clinical data, not by a language model.

The application demonstrates a safety-first pattern for healthcare AI:

```text
Clinical data -> deterministic validation -> generated constraints -> constrained AI explanation
```

## Safety Contract

The system has three clear layers:

```text
Database = clinical truth
Deterministic engines = safety authority
LLM = explanation and clarification layer
```

The LLM never determines medication safety.

It cannot:

- approve a drug
- override a HARD_BLOCK
- invent missing drug facts
- bypass deterministic validation
- select ambiguous medications silently
- replace interaction, allergy, renal, or score engines

It can:

- phrase deterministic findings clearly
- ask medication-name clarification questions
- explain why the Safe AI response differs from Generic AI
- provide patient-context wording after safety constraints are generated

## Runtime Flow

```text
Doctor Query
  -> Intent Classifier
  -> Safety Orchestrator
  -> Entity Resolver, if drug-specific
  -> Deterministic Safety Engines
  -> Calculator Engine
  -> Constraint Generator
  -> Safe AI Response
  -> Frontend Dashboard
```

## Repository File Structure

```text
MedGuard AI/
  README.md
  architecture.md
  render.yaml
  docs/
    DEPLOYMENT.md
    ENVIRONMENT.md

  backend/
    requirements.txt
    runtime.txt
    Procfile
    .env.example
    app/
      main.py
      config.py
      dependencies.py

      api/
        safety.py
        patients.py
        generic_ai.py
        safe_ai.py

      cache/
        interaction_cache.py

      database/
        supabase_client.py
        queries.py

      engine/
        intent_classifier.py
        entity_resolver.py
        orchestrator.py
        interaction_engine.py
        allergy_engine.py
        renal_engine.py
        calculator_engine.py
        constraint_generator.py

      llm/
        gemini_client.py
        prompts.py

      models/
        schemas.py
        alerts.py

      seed/
        clinical_data.py
        patients.py

      utils/
        normalize.py
        severity.py
        logger.py

    scripts/
      bootstrap_supabase.py
      run_backend.ps1

    tests/
      test_assessment_scenarios.py

  frontend/
    package.json
    index.html
    .env.example
    src/
      App.jsx
      main.jsx
      lib/
        api.js
      components/
        PatientSelector.jsx
        PatientCard.jsx
        QuestionInput.jsx
        SafetyAlerts.jsx
        SeverityBadge.jsx
        ClinicalScores.jsx
        ResponseComparison.jsx
        ClarificationModal.jsx
        QueryHistory.jsx
        LoadingOverlay.jsx
      styles/
        index.css

  supabase/
    schema.sql
    seed.sql
```

### Structure Responsibilities

- `backend/app/api`: FastAPI route boundaries for safety checks, patients, and AI comparison calls.
- `backend/app/engine`: deterministic clinical workflow layer. This is where intent routing, entity resolution, safety validation, calculators, and constraint generation live.
- `backend/app/cache`: startup-loaded interaction cache for normalized O(1) interaction lookup.
- `backend/app/database`: Supabase access layer and fallback repository behavior.
- `backend/app/llm`: constrained LLM client and prompt templates. Despite the legacy filename `gemini_client.py`, this client is Groq-first and supports optional Gemini fallback.
- `backend/app/models`: Pydantic schemas for API requests, responses, drugs, patients, and alerts.
- `backend/app/seed`: bundled validated seed data used for local development and assessment fallback.
- `backend/app/utils`: shared normalization, severity ranking, and structured audit logging.
- `frontend/src/components`: clinical dashboard UI modules, including alert hierarchy, score cards, AI comparison, and medication clarification modal.
- `supabase`: production database schema and seed data.
- `docs`: deployment and environment setup documentation.

## Intent Routing

The intent classifier is deterministic and keyword/rule based.

```text
DRUG_QUERY
  -> resolve proposed medication
  -> clarify if ambiguous
  -> run proposed-drug safety checks

REVIEW_QUERY
  -> scan current medication list
  -> detect existing interactions
  -> summarize renal/allergy/monitoring concerns

CALCULATOR_QUERY
  -> calculate deterministic scores
  -> return clinical score cards and explanation context

GENERAL_QUERY / HEALTH_QUERY
  -> avoid drug lookup
  -> use patient context and deterministic scores for explanation
```

This prevents patient questions such as "How severe is this patient's kidney disease?" from incorrectly becoming unknown-drug failures.

## Entity Resolution Design

The resolver follows a conservative multi-stage workflow:

```text
Exact Match
  -> Alias Match
  -> Prefix and Partial Match
  -> Conservative Fuzzy Match
  -> AI-Assisted Clarification Text
  -> Safe Unknown-Drug Exit
```

The resolver returns structured states:

```text
resolved
needs_clarification
drug_not_found
not_found
```

For ambiguous matches, the backend returns candidates and the frontend requires confirmation before safety validation starts.

Example:

```json
{
  "status": "needs_clarification",
  "candidates": ["Clarithromycin", "Azithromycin"],
  "confidence": 0.78,
  "match_type": "partial"
}
```

## Deterministic Engines

### Interaction Engine

Interaction checks use normalized pair keys:

```text
clarithromycin::atorvastatin
```

All interaction rows are preloaded during FastAPI startup into `InteractionCache`, giving O(1) lookup per pair.

For a proposed medication and `n` current medications:

```text
lookup per pair: O(1)
interaction pass: O(n)
```

### Allergy Engine

The allergy engine checks direct patient allergy text and class cross-reactivity rules from the clinical database. It can generate HARD_BLOCK alerts for high-risk allergy conflicts.

### Renal Engine

The renal engine evaluates patient renal function and drug-specific renal dosing metadata. It produces deterministic dose-adjustment and avoidance alerts.

### Calculator Engine

The calculator engine computes:

- CKD-EPI 2021 eGFR
- CHA2DS2-VASc

These calculations are mathematical and deterministic. AI is not involved.

## Full Medication Review Mode

Review mode analyzes the current medication profile without requiring a proposed new medication.

It checks:

- existing drug-drug interactions
- renal risk across current medications
- allergy conflicts
- monitoring requirements
- severe findings summary

This moves the platform beyond a one-off drug checker into a proactive safety audit workflow.

## Constraint Generation

After deterministic engines run, alerts and scores are converted into a constraint block for the Safe AI response.

The constraint generator includes:

- hard blocks
- severe warnings
- renal dosing instructions
- allergy restrictions
- clinical score context
- unknown-drug warnings
- explanation requirements

The Safe AI prompt receives this constraint block and must obey it.

## Generic AI vs Safe AI

The frontend intentionally displays two responses:

```text
Generic AI: natural draft without MedGuard constraints
Safe AI: constrained response after deterministic validation
```

The goal is to show why generic AI is not sufficient for medication safety. The "Why Safe AI Differed" section identifies deterministic reasons such as:

- severe interaction detected
- renal adjustment required
- allergy conflict identified
- deterministic clinical score injected
- unknown drug failed safely

## Alert Prioritization

Alerts are sorted by deterministic importance:

```text
HARD_BLOCK = 10
SEVERE     = 8
MODERATE   = 5
MINOR      = 2
```

The frontend displays higher-risk findings first with stronger visual hierarchy.

## Database Model

Core tables:

- `drugs`: validated medications, normalized names, classes, renal dosing metadata
- `drug_interactions`: pairwise interactions with severity and management
- `drug_aliases`: known aliases, abbreviations, and alternate names
- `allergy_cross_reactivity`: class-level allergy rules
- `patients`: patient context, labs, medications, allergies, history

Supabase PostgreSQL is the production database. Bundled seed data is available as a local fallback for assessment and offline development.

## API Boundary

Main backend routes:

```text
GET  /health
POST /api/patients
POST /api/safety-check
POST /api/ask-generic
POST /api/ask-safe
POST /api/admin/refresh-clinical-cache
```

The safety-check endpoint is the main deterministic orchestration boundary. The AI endpoints are separated so the UI can demonstrate generic versus constrained behavior.

## Deployment Shape

```text
Frontend: React + Vite + Tailwind
Backend: FastAPI + deterministic engines
Database: Supabase PostgreSQL
LLM: Groq llama-3.1-8b-instant
Hosting: Vercel or Render frontend, Render or Railway backend
```

The repository includes:

- `render.yaml` for Render blueprint deployment
- `backend/runtime.txt` for Python runtime selection
- `backend/.env.example` for backend configuration
- `frontend/.env.example` for frontend configuration
- `docs/DEPLOYMENT.md` for deployment steps

## Scalability Notes

The architecture is intended to scale by adding validated deterministic modules rather than expanding autonomous AI behavior.

Extension points:

- new drug interaction rows
- new drug aliases
- new allergy cross-reactivity classes
- new renal dosing metadata
- additional deterministic calculators
- new alert types
- additional review-mode checks

Because the interaction cache is loaded at startup and uses normalized keys, pair lookups remain constant time. The full proposed-drug interaction pass scales linearly with the patient's current medication count.

## Failure Modes and Safety Behavior

The platform fails closed:

- ambiguous medication: ask for confirmation
- unknown medication: recommend pharmacist review
- LLM unavailable: deterministic fallback response
- unsafe medication: display hard block or severe alert
- override language detected: log and retain safety warning

This behavior is essential for clinical safety infrastructure. The system prefers a cautious false positive over an unsafe false negative.
