from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from state.models import DecisionRecord
from state.store import ProjectStore


class ToolName(StrEnum):
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    RUN_COMMAND = "run_command"


class ToolDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    NEEDS_APPROVAL = "needs_approval"


class ToolRequest(BaseModel):
    id: str = Field(default_factory=lambda: f"tool_{uuid4().hex}", min_length=1)
    run_id: str = Field(alias="runId", min_length=1)
    task_id: str = Field(alias="taskId", min_length=1)
    tool: ToolName
    path: str | None = None
    command: list[str] | None = None
    approved: bool = False
    reason: str = Field(min_length=1, max_length=4000)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("command")
    @classmethod
    def command_parts_must_be_non_empty(
        cls,
        command: list[str] | None,
    ) -> list[str] | None:
        if command is not None and any(part.strip() == "" for part in command):
            raise ValueError("command parts must be non-empty")
        return command


class ToolPermissionResult(BaseModel):
    request_id: str = Field(alias="requestId")
    decision: ToolDecision
    reason: str
    resolved_path: str | None = Field(alias="resolvedPath", default=None)
    command: list[str] | None = None

    model_config = ConfigDict(populate_by_name=True)


class ToolPermissionGate:
    def __init__(
        self,
        workspace_root: str | Path,
        store: ProjectStore | None = None,
    ) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.store = store

    def evaluate(self, request: ToolRequest) -> ToolPermissionResult:
        if request.tool in {ToolName.READ_FILE, ToolName.WRITE_FILE}:
            return self._evaluate_file_request(request)

        if request.tool == ToolName.RUN_COMMAND:
            return self._evaluate_command_request(request)

        return self._deny(request, "Unknown tool request.")

    def _evaluate_file_request(self, request: ToolRequest) -> ToolPermissionResult:
        if request.path is None or request.path.strip() == "":
            return self._deny(request, "File tool requests require a path.")

        resolved_path = self._resolve_workspace_path(request.path)
        if resolved_path is None:
            return self._deny(request, "Path is outside the workspace.")

        if request.tool == ToolName.WRITE_FILE and not request.approved:
            return self._needs_approval(
                request,
                "File writes require explicit approval.",
                resolved_path=resolved_path,
            )

        return self._allow(
            request,
            "Tool request is scoped to the workspace.",
            resolved_path=resolved_path,
        )

    def _evaluate_command_request(self, request: ToolRequest) -> ToolPermissionResult:
        if not request.command:
            return self._deny(request, "Command tool requests require command parts.")

        if not request.approved:
            return self._needs_approval(
                request,
                "Generated commands require explicit approval.",
                command=request.command,
            )

        return self._allow(
            request,
            "Command was explicitly approved.",
            command=request.command,
        )

    def _resolve_workspace_path(self, path: str) -> Path | None:
        candidate = (self.workspace_root / path).resolve()
        if candidate == self.workspace_root or self.workspace_root in candidate.parents:
            return candidate
        return None

    def _allow(
        self,
        request: ToolRequest,
        reason: str,
        resolved_path: Path | None = None,
        command: list[str] | None = None,
    ) -> ToolPermissionResult:
        return self._record(
            request,
            ToolDecision.ALLOW,
            reason,
            resolved_path=resolved_path,
            command=command,
        )

    def _deny(
        self,
        request: ToolRequest,
        reason: str,
        resolved_path: Path | None = None,
        command: list[str] | None = None,
    ) -> ToolPermissionResult:
        return self._record(
            request,
            ToolDecision.DENY,
            reason,
            resolved_path=resolved_path,
            command=command,
        )

    def _needs_approval(
        self,
        request: ToolRequest,
        reason: str,
        resolved_path: Path | None = None,
        command: list[str] | None = None,
    ) -> ToolPermissionResult:
        return self._record(
            request,
            ToolDecision.NEEDS_APPROVAL,
            reason,
            resolved_path=resolved_path,
            command=command,
        )

    def _record(
        self,
        request: ToolRequest,
        decision: ToolDecision,
        reason: str,
        resolved_path: Path | None = None,
        command: list[str] | None = None,
    ) -> ToolPermissionResult:
        result = ToolPermissionResult(
            requestId=request.id,
            decision=decision,
            reason=reason,
            resolvedPath=str(resolved_path) if resolved_path else None,
            command=command,
        )

        if self.store is not None:
            self.store.save_decision(
                DecisionRecord(
                    id=f"decision_{uuid4().hex}",
                    run_id=request.run_id,
                    summary=f"Tool request {decision.value}: {request.tool.value}",
                    reason=reason,
                    inputs=[
                        f"tool:{request.tool.value}",
                        f"task:{request.task_id}",
                    ],
                    chosenOption=decision.value,
                    rejectedOptions=[],
                    created_at=datetime.now(UTC),
                )
            )

        return result
