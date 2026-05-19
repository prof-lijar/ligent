import pytest
from pydantic import ValidationError

from agents.roles import AgentRole
from state.models import (
    AgentMessage,
    AgentResult,
    ConflictRecord,
    DecisionRecord,
    MessageType,
    ProjectState,
    RunState,
    TaskState,
    TaskStatus,
)


def test_agent_message_requires_expected_output_contract() -> None:
    message = AgentMessage.model_validate(
        {
            "id": "msg_1",
            "projectId": "project_1",
            "runId": "run_1",
            "taskId": "task_1",
            "from": "controller",
            "to": "planner",
            "type": "task_assignment",
            "instructions": "Plan the work.",
            "expectedOutput": {"type": "plan"},
        }
    )

    assert message.sender == "controller"
    assert message.type == MessageType.TASK_ASSIGNMENT


def test_malformed_agent_message_fails_validation() -> None:
    with pytest.raises(ValidationError):
        AgentMessage.model_validate(
            {
                "id": "msg_1",
                "projectId": "project_1",
                "runId": "run_1",
                "taskId": "task_1",
                "from": "controller",
                "to": "planner",
                "type": "task_assignment",
                "instructions": "",
                "expectedOutput": {"type": "plan"},
            }
        )


def test_assigned_task_requires_agent() -> None:
    with pytest.raises(ValidationError):
        TaskState(
            id="task_1",
            run_id="run_1",
            title="Plan work",
            status=TaskStatus.ASSIGNED,
        )


def test_core_state_contracts_validate() -> None:
    project = ProjectState(id="project_1", name="Ligent")
    run = RunState(id="run_1", project_id=project.id, goal="Build contracts")
    task = TaskState(
        id="task_1",
        run_id=run.id,
        title="Plan work",
        assigned_agent=AgentRole.PLANNER,
        status=TaskStatus.ASSIGNED,
    )
    result = AgentResult(
        id="result_1",
        message_id="msg_1",
        task_id=task.id,
        agent=AgentRole.PLANNER,
        result={"tasks": []},
        evidence=["issue #5"],
        confidence=0.8,
    )
    decision = DecisionRecord(
        id="decision_1",
        run_id=run.id,
        summary="Use SQLite",
        reason="Local-first persistence for MVP.",
        chosenOption="SQLite",
    )
    conflict = ConflictRecord(
        id="conflict_1",
        run_id=run.id,
        taskIds=[task.id],
        summary="Conflicting recommendations",
    )

    assert project.status == "active"
    assert run.status == "queued"
    assert task.assigned_agent == AgentRole.PLANNER
    assert result.confidence == 0.8
    assert decision.chosen_option == "SQLite"
    assert conflict.status == "open"
