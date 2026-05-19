from fastapi import APIRouter

from services.run_service import create_run_preview
from services.schemas import HealthResponse, RunPreviewRequest, RunPreviewResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="ligent-backend")


@router.post("/runs/preview", response_model=RunPreviewResponse)
def preview_run(payload: RunPreviewRequest) -> RunPreviewResponse:
    return create_run_preview(payload)

