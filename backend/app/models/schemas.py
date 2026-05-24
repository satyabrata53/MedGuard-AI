from typing import Any, Literal
from pydantic import BaseModel, Field

from app.models.alerts import SafetyAlert


class Drug(BaseModel):
    id: int | None = None
    generic_name: str
    generic_name_normalized: str
    drug_class: str
    renal_dosing: dict[str, Any] = Field(default_factory=dict)


class DrugInteraction(BaseModel):
    id: int | None = None
    drug_a_normalized: str
    drug_b_normalized: str
    severity: Literal["HARD_BLOCK", "SEVERE", "MODERATE", "MINOR"]
    mechanism: str
    clinical_effect: str
    management: str


class AllergyCrossReactivity(BaseModel):
    id: int | None = None
    allergy_class: str
    cross_reacts_with: str
    cross_reactivity_pct: float
    guidance: str


class DrugAlias(BaseModel):
    id: int | None = None
    alias: str
    actual_drug: str


class Patient(BaseModel):
    id: str
    name: str
    age: int
    sex: Literal["male", "female"]
    race: str = "unspecified"
    weight_kg: float | None = None
    diagnoses: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    labs: dict[str, Any] = Field(default_factory=dict)
    vitals: dict[str, Any] = Field(default_factory=dict)
    history: dict[str, bool] = Field(default_factory=dict)


class ResolvedDrug(BaseModel):
    input: str
    normalized_input: str
    status: Literal["resolved", "needs_clarification", "drug_not_found", "clarify", "not_found"]
    resolved_name: str | None = None
    resolved_normalized: str | None = None
    confidence: float
    match_type: str
    candidates: list[str] = Field(default_factory=list)
    message: str | None = None
    confidence_explanation: str | None = None


class SafetyCheckRequest(BaseModel):
    patient: Patient
    query: str
    proposed_drug: str | None = None


class SafetyCheckResponse(BaseModel):
    alerts: list[SafetyAlert]
    scores: dict[str, Any]
    resolved_drug: ResolvedDrug
    constraints: str
    intent: str = "DRUG_QUERY"
    review_summary: dict[str, Any] = Field(default_factory=dict)
    why_safe_ai_changed: list[str] = Field(default_factory=list)


class AiRequest(BaseModel):
    patient: Patient
    query: str
    alerts: list[SafetyAlert] = Field(default_factory=list)
    scores: dict[str, Any] = Field(default_factory=dict)
    constraints: str = ""


class AiResponse(BaseModel):
    response: str
    model: str
    mode: Literal["generic", "safe"]
