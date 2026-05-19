from datetime import UTC, datetime
from uuid import uuid4

from agents.roles import AgentRole
from services.schemas import RunPreviewRequest, RunPreviewResponse


PREVIEW_STAGES = (
    AgentRole.PLANNER,
    AgentRole.DESIGN,
    AgentRole.IMPLEMENT,
    AgentRole.QA,
    AgentRole.DOCUMENTATION,
)


def create_run_preview(payload: RunPreviewRequest) -> RunPreviewResponse:
    goal_preview = payload.goal[:120]

    return RunPreviewResponse(
        run_id=f"run_{uuid4().hex}",
        status="queued",
        summary="Backend accepted the goal and created a preview run.",
        next_step=f"Controller loop will decompose: {goal_preview}",
        assigned_agents=list(PREVIEW_STAGES),
        created_at=datetime.now(UTC),
    )

