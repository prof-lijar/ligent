from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from agents.roles import AgentRole


class HealthResponse(BaseModel):
    status: str = Field(min_length=1)
    service: str = Field(min_length=1)


class RunPreviewRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=4000)


class RunPreviewResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run_id: str = Field(alias="runId", min_length=1)
    status: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    next_step: str = Field(alias="nextStep", min_length=1)
    assigned_agents: list[AgentRole] = Field(alias="assignedAgents", min_length=1)
    created_at: datetime = Field(alias="createdAt")

