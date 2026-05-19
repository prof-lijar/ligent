from services.controller import LigentController
from services.schemas import OllamaPlanRequest, RunPreviewRequest, RunPreviewResponse


def create_run_preview(payload: RunPreviewRequest) -> RunPreviewResponse:
    return LigentController().run(payload.goal)


def create_ollama_plan(payload: OllamaPlanRequest) -> RunPreviewResponse:
    return LigentController().run_ollama_planning(payload.goal, model=payload.model)
