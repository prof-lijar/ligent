from agents.roles import AgentRole
from services.controller import LigentController
from state.models import RunStatus, TaskStatus
from state.store import ProjectStore


class FakePlanningProvider:
    def generate_json(
        self,
        *,
        model: str,
        prompt: str,
        schema_hint: str,
    ) -> dict[str, object]:
        return {
            "summary": f"Planned with {model}",
            "tasks": [
                {
                    "title": "Implement provider",
                    "description": "Add local Ollama planning support.",
                    "acceptance": ["Provider output is validated."],
                }
            ],
            "risks": ["Local model may be missing."],
            "next_step": "Review the generated plan.",
            "confidence": 0.82,
        }


class RepairingPlanningProvider:
    def __init__(self) -> None:
        self.calls = 0

    def generate_json(
        self,
        *,
        model: str,
        prompt: str,
        schema_hint: str,
    ) -> dict[str, object]:
        self.calls += 1
        if self.calls == 1:
            return {
                "summary": "Needs repair.",
                "tasks": [
                    {
                        "title": "Bad task",
                        "description": "Acceptance is the wrong type.",
                        "acceptance": "not a list",
                    }
                ],
                "risks": [],
                "next_step": "Repair it.",
                "confidence": "Medium",
            }
        return {
            "summary": "Repaired plan.",
            "tasks": [
                {
                    "title": "Good task",
                    "description": "Acceptance is now a list.",
                    "acceptance": ["Schema validation passes."],
                }
            ],
            "risks": [],
            "next_step": "Review repaired output.",
            "confidence": 0.7,
        }


def test_controller_creates_run_tasks_results_and_decision(tmp_path) -> None:
    store = ProjectStore(tmp_path / "ligent.sqlite")
    controller = LigentController(store=store)

    response = controller.run("Add a health endpoint")

    run = store.get_run(response.run_id)
    tasks = store.list_tasks(response.run_id)
    messages = store.list_agent_messages(response.run_id)
    decisions = store.list_decisions(response.run_id)

    assert run is not None
    assert run.status == RunStatus.COMPLETED
    assert response.status == RunStatus.COMPLETED
    assert response.assigned_agents == [
        AgentRole.PLANNER,
        AgentRole.DESIGN,
        AgentRole.IMPLEMENT,
        AgentRole.QA,
        AgentRole.DEVOPS,
        AgentRole.DOCUMENTATION,
    ]
    assert len(tasks) == 6
    assert len(messages) == 6
    assert len(decisions) == 2
    assert decisions[0].summary == "Tool permission boundary enforced."
    assert decisions[1].summary == "Completed deterministic mock orchestration."
    assert all(task.status == TaskStatus.COMPLETED for task in tasks)

    for task in tasks:
        results = store.list_agent_results(task.id)
        assert len(results) == 1
        assert results[0].task_id == task.id
        assert results[0].confidence == 0.75


def test_controller_rejects_empty_request(tmp_path) -> None:
    controller = LigentController(store=ProjectStore(tmp_path / "ligent.sqlite"))

    try:
        controller.run("  ")
    except ValueError as error:
        assert str(error) == "user_request is required"
    else:
        raise AssertionError("Expected empty request to fail")


def test_controller_uses_run_scoped_task_ids(tmp_path) -> None:
    store = ProjectStore(tmp_path / "ligent.sqlite")
    controller = LigentController(store=store)

    first_run = controller.run("First request")
    second_run = controller.run("Second request")

    first_tasks = store.list_tasks(first_run.run_id)
    second_tasks = store.list_tasks(second_run.run_id)

    assert len(first_tasks) == 6
    assert len(second_tasks) == 6
    assert {task.id for task in first_tasks}.isdisjoint(
        {task.id for task in second_tasks}
    )


def test_controller_runs_ollama_planning_after_validation(tmp_path) -> None:
    store = ProjectStore(tmp_path / "ligent.sqlite")
    controller = LigentController(store=store, llm_provider=FakePlanningProvider())

    response = controller.run_ollama_planning("Add local planning", model="gemma3:4b")

    run = store.get_run(response.run_id)
    tasks = store.list_tasks(response.run_id)
    messages = store.list_agent_messages(response.run_id)
    decisions = store.list_decisions(response.run_id)
    results = store.list_agent_results(tasks[0].id)

    assert run is not None
    assert run.status == RunStatus.COMPLETED
    assert response.summary == "Planned with gemma3:4b"
    assert response.next_step == "Review the generated plan."
    assert response.assigned_agents == [AgentRole.PLANNER]
    assert len(tasks) == 1
    assert len(messages) == 1
    assert len(decisions) == 1
    assert tasks[0].status == TaskStatus.COMPLETED
    assert results[0].agent == AgentRole.PLANNER
    assert results[0].confidence == 0.82
    assert results[0].result["tasks"][0]["title"] == "Implement provider"


def test_controller_repairs_schema_invalid_ollama_output(tmp_path) -> None:
    provider = RepairingPlanningProvider()
    store = ProjectStore(tmp_path / "ligent.sqlite")
    controller = LigentController(store=store, llm_provider=provider)

    response = controller.run_ollama_planning("Plan from a small model")

    tasks = store.list_tasks(response.run_id)
    results = store.list_agent_results(tasks[0].id)

    assert provider.calls == 2
    assert response.summary == "Repaired plan."
    assert results[0].result["tasks"][0]["acceptance"] == [
        "Schema validation passes."
    ]
