from datetime import datetime

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agents.roles import AgentRole
from state.models import TaskStatus


class HealthResponse(BaseModel):
    status: str = Field(min_length=1)
    service: str = Field(min_length=1)


class RunPreviewRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=4000)


class OllamaPlanRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=4000)
    model: str | None = Field(default=None, min_length=1, max_length=120)


class RunPreviewResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run_id: str = Field(alias="runId", min_length=1)
    status: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    next_step: str = Field(alias="nextStep", min_length=1)
    assigned_agents: list[AgentRole] = Field(alias="assignedAgents", min_length=1)
    created_at: datetime = Field(alias="createdAt")


class AgentResultSummary(BaseModel):
    agent: AgentRole
    result: dict[str, Any]
    evidence: list[str] = Field(default_factory=list)
    confidence: float


class TaskDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    description: str
    status: TaskStatus
    assigned_agent: AgentRole | None = Field(alias="assignedAgent")
    instructions: str
    results: list[AgentResultSummary] = Field(default_factory=list)


class DecisionSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    summary: str
    reason: str
    chosen_option: str = Field(alias="chosenOption")


class ConflictSummary(BaseModel):
    id: str
    summary: str
    status: str


class RunDetailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run_id: str = Field(alias="runId")
    status: str
    goal: str
    final_summary: str = Field(alias="finalSummary")
    tasks: list[TaskDetail]
    decisions: list[DecisionSummary]
    conflicts: list[ConflictSummary]
    created_at: datetime = Field(alias="createdAt")
