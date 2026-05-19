import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import ValidationError

from agents.adk_runtime import AdkRoleAgentExecutor, RoleAgentExecutor
from agents.roles import AgentRole
from llm.contracts import JsonLLMProvider
from llm.ollama import OllamaProvider
from llm.planning import PLANNING_SCHEMA_HINT, PlanningOutput
from services.schemas import RunPreviewResponse
from state.models import (
    AgentMessage,
    AgentResult,
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
DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:7b"


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


def get_default_ollama_model() -> str:
    return os.environ.get("LIGENT_OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)


class LigentController:
    def __init__(
        self,
        store: ProjectStore | None = None,
        agent_executor: RoleAgentExecutor | None = None,
        llm_provider: JsonLLMProvider | None = None,
    ) -> None:
        self.store = store or ProjectStore(get_default_state_path())
        self.agent_executor = agent_executor or AdkRoleAgentExecutor()
        self.llm_provider = llm_provider

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
        self.store.save_decision(
            DecisionRecord(
                id=f"decision_{uuid4().hex}",
                run_id=run.id,
                summary="Tool permission boundary enforced.",
                reason=(
                    "Workspace tools are scoped to workspace/ and writes or "
                    "generated commands require explicit approval."
                ),
                inputs=["workspace/", "tool permissions"],
                chosenOption="Fail closed on unsafe or unapproved tool requests.",
            )
        )

        completed_roles: list[AgentRole] = []
        try:
            for position, (role, instruction) in enumerate(TASK_PLAN, start=1):
                task = self._create_task(run.id, goal, role, instruction, position)
                message = self._create_message(project.id, run.id, task, instruction)
                result = self.agent_executor.execute(
                    task=task,
                    message=message,
                    goal=goal,
                )
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
        except Exception as error:
            failed_run = run.model_copy(
                update={
                    "status": RunStatus.FAILED,
                    "updated_at": datetime.now(UTC),
                }
            )
            self.store.save_run(failed_run)
            self.store.save_decision(
                DecisionRecord(
                    id=f"decision_{uuid4().hex}",
                    run_id=run.id,
                    summary="ADK-backed agent orchestration failed.",
                    reason=str(error),
                    inputs=[goal],
                    chosenOption="Fail closed and surface the agent runtime error.",
                    rejectedOptions=["Silently continue after an agent failure."],
                )
            )
            raise

        decision = DecisionRecord(
            id=f"decision_{uuid4().hex}",
            run_id=run.id,
            summary="Completed ADK-backed agent orchestration.",
            reason=(
                "The MVP controller loop validated task assignment, structured "
                "agent output, persistence, and final synthesis with local "
                "ADK role agents."
            ),
            inputs=[goal],
            chosenOption="Use ADK-backed local agents.",
            rejectedOptions=["Use deterministic mock agents for the main run path."],
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
                "Ligent completed an ADK-backed orchestration run with "
                f"{len(completed_roles)} scoped agents."
            ),
            next_step="Review persisted tasks, agent results, and the controller decision.",
            assigned_agents=completed_roles,
            created_at=completed_run.created_at,
        )

    def run_ollama_planning(
        self,
        user_request: str,
        *,
        model: str | None = None,
    ) -> RunPreviewResponse:
        goal = user_request.strip()
        if not goal:
            raise ValueError("user_request is required")

        selected_model = (model or get_default_ollama_model()).strip()
        if not selected_model:
            raise ValueError("model is required")

        provider = self.llm_provider or OllamaProvider()
        prompt = self._create_planning_prompt(goal)
        planning_output = self._generate_planning_output(
            provider,
            selected_model,
            prompt,
        )

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
        task = self._create_task(
            run.id,
            goal,
            AgentRole.PLANNER,
            "Create a scoped local-model implementation plan.",
            1,
        )
        message = self._create_message(
            project.id,
            run.id,
            task,
            "Create a scoped local-model implementation plan.",
        )
        result = AgentResult(
            id=f"result_{message.id}",
            message_id=message.id,
            task_id=task.id,
            agent=AgentRole.PLANNER,
            result=planning_output.model_dump(),
            evidence=[
                f"provider=ollama",
                f"model={selected_model}",
                "validated_by=PlanningOutput",
            ],
            confidence=planning_output.confidence,
        )

        self.store.save_project(project)
        self.store.save_run(run)
        self.store.save_task(task)
        self.store.save_agent_message(message)
        self.store.save_agent_result(result)
        self.store.save_task(
            task.model_copy(
                update={
                    "status": TaskStatus.COMPLETED,
                    "updated_at": datetime.now(UTC),
                }
            )
        )
        self.store.save_decision(
            DecisionRecord(
                id=f"decision_{uuid4().hex}",
                run_id=run.id,
                summary="Completed local Ollama planning session.",
                reason=(
                    "The planner response was parsed as JSON, validated with "
                    "the PlanningOutput contract, and persisted only after "
                    "schema validation succeeded."
                ),
                inputs=[goal, selected_model],
                chosenOption="Use local Ollama for the planner step.",
                rejectedOptions=["Use a hosted LLM provider by default."],
            )
        )

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
            summary=planning_output.summary,
            next_step=planning_output.next_step,
            assigned_agents=[AgentRole.PLANNER],
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

    @staticmethod
    def _create_planning_prompt(goal: str) -> str:
        return (
            "You are Ligent's planner agent. Produce only valid JSON matching "
            "the schema. Keep tasks small, local-first, and safe by default.\n"
            f"Schema:\n{PLANNING_SCHEMA_HINT}\n"
            "Rules: acceptance must be an array of strings. confidence must be "
            "a number from 0 to 1.\n"
            f"User goal:\n{goal}"
        )

    @staticmethod
    def _generate_planning_output(
        provider: JsonLLMProvider,
        model: str,
        prompt: str,
    ) -> PlanningOutput:
        raw_output = provider.generate_json(
            model=model,
            prompt=prompt,
            schema_hint=PLANNING_SCHEMA_HINT,
        )
        try:
            return PlanningOutput.model_validate(raw_output)
        except ValidationError as error:
            repair_prompt = (
                "Repair this JSON so it matches the schema exactly. Return only "
                "valid JSON. Do not include markdown or commentary.\n"
                f"Schema:\n{PLANNING_SCHEMA_HINT}\n"
                "Rules: acceptance must be an array of strings. confidence must "
                "be a number from 0 to 1.\n"
                f"Validation error:\n{error}\n"
                f"Invalid JSON object:\n{raw_output}"
            )
            repaired_output = provider.generate_json(
                model=model,
                prompt=repair_prompt,
                schema_hint=PLANNING_SCHEMA_HINT,
            )
            return PlanningOutput.model_validate(repaired_output)
