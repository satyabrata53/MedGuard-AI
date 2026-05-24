# API Documentation

Base URL locally: `http://localhost:8000`

## `POST /api/patients`

Returns the seeded patient list.

Response: `Patient[]`

## `POST /api/safety-check`

Runs deterministic medication safety validation.

Request:

```json
{
  "patient": { "id": "P-1001", "name": "Maya Srinivasan" },
  "query": "Can I add clarithro?",
  "proposed_drug": null
}
```

Response:

```json
{
  "alerts": [],
  "scores": {
    "ckd_epi_2021_egfr": 31.5,
    "cha2ds2_vasc": 5
  },
  "resolved_drug": {
    "status": "resolved",
    "resolved_name": "Clarithromycin",
    "confidence": 1
  },
  "constraints": "WARNING SEVERE..."
}
```

## `POST /api/ask-generic`

Generates the unconstrained comparison response. This endpoint intentionally receives no deterministic safety constraints.

Request:

```json
{
  "patient": {},
  "query": "Can I add clarithro?"
}
```

## `POST /api/ask-safe`

Generates a constrained response using deterministic safety constraints.

Request:

```json
{
  "patient": {},
  "query": "Can I add clarithro?",
  "alerts": [],
  "scores": {},
  "constraints": "STOP HARD BLOCK..."
}
```

## `GET /health`

Returns service status and interaction cache size.
