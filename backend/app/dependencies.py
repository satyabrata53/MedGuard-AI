from functools import lru_cache

from app.database.queries import ClinicalRepository
from app.engine.orchestrator import SafetyOrchestrator


@lru_cache
def get_repository() -> ClinicalRepository:
    return ClinicalRepository()


@lru_cache
def get_orchestrator() -> SafetyOrchestrator:
    return SafetyOrchestrator(get_repository())
