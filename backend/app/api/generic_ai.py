from fastapi import APIRouter

from app.llm.gemini_client import GeminiClient
from app.models.schemas import AiRequest, AiResponse

router = APIRouter(prefix="/api", tags=["ai"])


@router.post("/ask-generic", response_model=AiResponse)
def ask_generic(payload: AiRequest) -> AiResponse:
    client = GeminiClient()
    return AiResponse(
        response=client.generate_generic(payload.patient.model_dump(), payload.query),
        model=client.model_name,
        mode="generic",
    )
