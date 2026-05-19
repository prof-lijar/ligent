import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from agents.mock_agents import MockAgent
from agents.roles import AgentRole
from services.schemas import RunPreviewResponse
from state.models import (
    AgentMessage,
    DecisionRecord,
    MessageType,
    ProjectState,
    RunState,
    RunStatus,
    TaskState,
    TaskStatus,
)
from state.store import ProjectStore


DEFAULT_PROJECT_ID = "project_default"
DEFAULT_PROJECT_NAME = "Ligent Workspace"
DEFAULT_STATE_PATH = Path(__file__).resolve().parents[1] / ".local" / "ligent.sqlite"


TASK_PLAN: tuple[tuple[AgentRole, str], ...] = (
    (AgentRole.PLANNER, "Break down the request into scoped implementation tasks."),
    (AgentRole.DESIGN, "Identify the user-facing flow and architecture shape."),
    (AgentRole.IMPLEMENT, "Describe the implementation work needed for the request."),
    (AgentRole.QA, "Define validation and regression checks for the request."),
    (AgentRole.DEVOPS, "Check local runtime, build, and operational assumptions."),
    (AgentRole.DOCUMENTATION, "Summarize the result and next-step handoff."),
)


def get_default_state_path() -> Path:
    configured_path = os.environ.get("LIGENT_STATE_DB")
    if configured_path:
        return Path(configured_path)
    return DEFAULT_STATE_PATH


class LigentController:
    def __init__(
        self,
        store: ProjectStore | None = None,
        mock_agent: MockAgent | None = None,
    ) -> None:
        self.store = store or ProjectStore(get_default_state_path())
        self.mock_agent = mock_agent or MockAgent()

    def run(self, user_request: str) -> RunPreviewResponse:
        goal = user_request.strip()
        if not goal:
            raise ValueError("user_request is required")

        now = datetime.now(UTC)
        project = ProjectState(
            id=DEFAULT_PROJECT_ID,
            name=DEFAULT_PROJECT_NAME,
            brief="Default local Ligent project state.",
            updated_at=now,
        )
        run = RunState(
            id=f"run_{uuid4().hex}",
            project_id=project.id,
            goal=goal,
            status=RunStatus.RUNNING,
            created_at=now,
            updated_at=now,
        )

        self.store.save_project(project)
        self.store.save_run(run)

        completed_roles: list[AgentRole] = []
        for position, (role, instruction) in enumerate(TASK_PLAN, start=1):
            task = self._create_task(run.id, goal, role, instruction, position)
            message = self._create_message(project.id, run.id, task, instruction)
            result = self.mock_agent.run(message, task)
            completed_task = task.model_copy(
                update={
                    "status": TaskStatus.COMPLETED,
                    "updated_at": datetime.now(UTC),
                }
            )

            self.store.save_task(task)
            self.store.save_agent_message(message)
            self.store.save_agent_result(result)
            self.store.save_task(completed_task)
            completed_roles.append(role)

        decision = DecisionRecord(
            id=f"decision_{uuid4().hex}",
            run_id=run.id,
            summary="Completed deterministic mock orchestration.",
            reason=(
                "The MVP controller loop validated task assignment, structured "
                "agent output, persistence, and final synthesis without using a "
                "live model provider."
            ),
            inputs=[goal],
            chosenOption="Use deterministic mock agents before Ollama integration.",
            rejectedOptions=["Call local Ollama before the controller loop is stable."],
        )
        self.store.save_decision(decision)

        completed_run = run.model_copy(
            update={
                "status": RunStatus.COMPLETED,
                "updated_at": datetime.now(UTC),
            }
        )
        self.store.save_run(completed_run)

        return RunPreviewResponse(
            run_id=completed_run.id,
            status=completed_run.status,
            summary=(
                "Ligent completed a deterministic mock orchestration run with "
                f"{len(completed_roles)} scoped agents."
            ),
            next_step="Review persisted tasks, agent results, and the controller decision.",
            assigned_agents=completed_roles,
            created_at=completed_run.created_at,
        )

    @staticmethod
    def _create_task(
        run_id: str,
        goal: str,
        role: AgentRole,
        instruction: str,
        position: int,
    ) -> TaskState:
        return TaskState(
            id=f"task_{run_id}_{position}_{role.value}",
            run_id=run_id,
            title=f"{role.value.title()} task",
            description=f"{instruction} Goal: {goal}",
            assigned_agent=role,
            status=TaskStatus.ASSIGNED,
        )

    @staticmethod
    def _create_message(
        project_id: str,
        run_id: str,
        task: TaskState,
        instruction: str,
    ) -> AgentMessage:
        if task.assigned_agent is None:
            raise ValueError("task must have an assigned agent")

        return AgentMessage.model_validate(
            {
                "id": f"msg_{task.id}",
                "projectId": project_id,
                "runId": run_id,
                "taskId": task.id,
                "from": "controller",
                "to": task.assigned_agent.value,
                "type": MessageType.TASK_ASSIGNMENT,
                "context": {"goalScoped": True},
                "instructions": instruction,
                "constraints": [
                    "Return structured output only.",
                    "Do not mutate global state directly.",
                ],
                "expectedOutput": {
                    "recommendation": "string",
                    "status": "completed",
                },
            }
        )
