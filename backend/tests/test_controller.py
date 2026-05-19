from agents.roles import AgentRole
from services.controller import LigentController
from state.models import RunStatus, TaskStatus
from state.store import ProjectStore


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
    assert len(decisions) == 1
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
