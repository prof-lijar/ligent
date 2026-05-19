from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from llm.errors import (
    LLMResponseValidationError,
    OllamaModelUnavailableError,
    OllamaUnavailableError,
)
from services.run_service import create_ollama_plan, create_run_preview, get_run_detail
from services.schemas import (
    HealthResponse,
    OllamaPlanRequest,
    RunDetailResponse,
    RunPreviewRequest,
    RunPreviewResponse,
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="ligent-backend")


@router.post("/runs/preview", response_model=RunPreviewResponse)
def preview_run(payload: RunPreviewRequest) -> RunPreviewResponse:
    return create_run_preview(payload)


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
def run_detail(run_id: str) -> RunDetailResponse:
    detail = get_run_detail(run_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    return detail


@router.post("/runs/ollama-plan", response_model=RunPreviewResponse)
def ollama_plan(payload: OllamaPlanRequest) -> RunPreviewResponse:
    try:
        return create_ollama_plan(payload)
    except OllamaModelUnavailableError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except OllamaUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except LLMResponseValidationError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except ValidationError as error:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama response did not match the planning schema: {error}",
        ) from error
