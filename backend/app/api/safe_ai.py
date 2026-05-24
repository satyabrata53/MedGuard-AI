from fastapi import APIRouter

from app.llm.gemini_client import GeminiClient
from app.models.schemas import AiRequest, AiResponse

router = APIRouter(prefix="/api", tags=["ai"])


@router.post("/ask-safe", response_model=AiResponse)
def ask_safe(payload: AiRequest) -> AiResponse:
    client = GeminiClient()
    return AiResponse(
        response=client.generate_safe(payload.patient.model_dump(), payload.query, payload.constraints),
        model=client.model_name,
        mode="safe",
    )
