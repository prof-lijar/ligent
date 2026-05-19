from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from agents.roles import AgentRole


class ProjectStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(StrEnum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    REJECTED = "rejected"
    MERGED = "merged"


class MessageType(StrEnum):
    TASK_ASSIGNMENT = "task_assignment"
    AGENT_RESULT = "agent_result"
    TOOL_REQUEST = "tool_request"
    TOOL_RESULT = "tool_result"
    CLARIFICATION = "clarification"


class ProjectState(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    brief: str = Field(default="", max_length=12000)
    status: ProjectStatus = ProjectStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RunState(BaseModel):
    id: str = Field(min_length=1)
    project_id: str = Field(alias="projectId", min_length=1)
    goal: str = Field(min_length=1, max_length=4000)
    status: RunStatus = RunStatus.QUEUED
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(populate_by_name=True)


class TaskState(BaseModel):
    id: str = Field(min_length=1)
    run_id: str = Field(alias="runId", min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(default="", max_length=12000)
    assigned_agent: AgentRole | None = Field(alias="assignedAgent", default=None)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("status")
    @classmethod
    def assigned_tasks_need_agent(cls, status: TaskStatus, info: Any) -> TaskStatus:
        if status in {
            TaskStatus.ASSIGNED,
            TaskStatus.IN_PROGRESS,
            TaskStatus.COMPLETED,
            TaskStatus.MERGED,
        } and info.data.get("assigned_agent") is None:
            raise ValueError("assigned_agent is required for assigned task states")
        return status


class AgentMessage(BaseModel):
    id: str = Field(min_length=1)
    project_id: str = Field(alias="projectId", min_length=1)
    run_id: str = Field(alias="runId", min_length=1)
    task_id: str = Field(alias="taskId", min_length=1)
    sender: str = Field(alias="from", min_length=1)
    to: str = Field(min_length=1)
    type: MessageType
    context: dict[str, Any] = Field(default_factory=dict)
    instructions: str = Field(min_length=1, max_length=12000)
    constraints: list[str] = Field(default_factory=list)
    expected_output: dict[str, Any] = Field(alias="expectedOutput")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(populate_by_name=True)


class AgentResult(BaseModel):
    id: str = Field(min_length=1)
    message_id: str = Field(alias="messageId", min_length=1)
    task_id: str = Field(alias="taskId", min_length=1)
    agent: AgentRole
    result: dict[str, Any]
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(populate_by_name=True)


class DecisionRecord(BaseModel):
    id: str = Field(min_length=1)
    run_id: str = Field(alias="runId", min_length=1)
    summary: str = Field(min_length=1, max_length=4000)
    reason: str = Field(min_length=1, max_length=12000)
    inputs: list[str] = Field(default_factory=list)
    chosen_option: str = Field(alias="chosenOption", min_length=1)
    rejected_options: list[str] = Field(alias="rejectedOptions", default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(populate_by_name=True)


class ConflictRecord(BaseModel):
    id: str = Field(min_length=1)
    run_id: str = Field(alias="runId", min_length=1)
    task_ids: list[str] = Field(alias="taskIds", min_length=1)
    summary: str = Field(min_length=1, max_length=4000)
    status: str = Field(default="open", pattern="^(open|resolved)$")
    resolution_decision_id: str | None = Field(
        alias="resolutionDecisionId", default=None
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(populate_by_name=True)
