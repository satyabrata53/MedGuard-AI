from fastapi import APIRouter, Depends

from app.database.queries import ClinicalRepository
from app.dependencies import get_repository
from app.models.schemas import Patient

router = APIRouter(prefix="/api", tags=["patients"])


@router.post("/patients", response_model=list[Patient])
def patients(repository: ClinicalRepository = Depends(get_repository)) -> list[Patient]:
    return [Patient(**patient) for patient in repository.get_patients()]
