from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import generic_ai, patients, safe_ai, safety
from app.cache.interaction_cache import interaction_cache
from app.database.queries import ClinicalRepository
from app.dependencies import get_orchestrator
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    repository = ClinicalRepository()
    interaction_cache.build(repository.get_interactions())
    get_orchestrator()
    logger.info("Interaction cache initialized with %s pairs", interaction_cache.size)
    yield


app = FastAPI(
    title="MedGuard AI Clinical Drug Safety Engine",
    version="1.0.0",
    description="Deterministic clinical drug safety middleware with constrained LLM explanations.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(safety.router)
app.include_router(generic_ai.router)
app.include_router(safe_ai.router)
app.include_router(patients.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "interaction_cache_pairs": interaction_cache.size}
