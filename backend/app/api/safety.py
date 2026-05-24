from fastapi import APIRouter, Depends

from app.cache.interaction_cache import interaction_cache
from app.database.queries import ClinicalRepository
from app.dependencies import get_orchestrator, get_repository
from app.engine.orchestrator import SafetyOrchestrator
from app.models.schemas import SafetyCheckRequest, SafetyCheckResponse

router = APIRouter(prefix="/api", tags=["safety"])


@router.post("/safety-check", response_model=SafetyCheckResponse)
def safety_check(payload: SafetyCheckRequest, orchestrator: SafetyOrchestrator = Depends(get_orchestrator)) -> SafetyCheckResponse:
    return orchestrator.check(payload.patient, payload.query, payload.proposed_drug)


@router.post("/admin/refresh-clinical-cache")
def refresh_clinical_cache(
    repository: ClinicalRepository = Depends(get_repository),
    orchestrator: SafetyOrchestrator = Depends(get_orchestrator),
) -> dict:
    interaction_cache.build(repository.get_interactions())
    orchestrator.refresh()
    return {"status": "ok", "interaction_cache_pairs": interaction_cache.size}
