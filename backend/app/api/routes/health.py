from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class HealthResponse(BaseModel):
    status: str

@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """
    Simple health check endpoint returning status 'ok'.
    """
    return HealthResponse(status="ok")
