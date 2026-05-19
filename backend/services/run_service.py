from services.controller import LigentController
from services.schemas import RunPreviewRequest, RunPreviewResponse


def create_run_preview(payload: RunPreviewRequest) -> RunPreviewResponse:
    return LigentController().run(payload.goal)
