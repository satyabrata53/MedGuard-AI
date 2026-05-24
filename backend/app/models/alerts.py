from pydantic import BaseModel, Field


class SafetyAlert(BaseModel):
    type: str
    severity: str
    title: str
    mechanism: str
    recommendation: str
    importance: int = Field(ge=1, le=10)
