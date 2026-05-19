from agents.roles import AgentRole
from state.models import (
    AgentMessage,
    AgentResult,
    ConflictRecord,
    DecisionRecord,
    ProjectState,
    RunState,
    TaskState,
    TaskStatus,
)
from state.store import ProjectStore


def test_project_state_round_trips_through_sqlite(tmp_path) -> None:
    store = ProjectStore(tmp_path / "ligent.sqlite")
    project = ProjectState(id="project_1", name="Ligent", brief="Local agent")
    run = RunState(id="run_1", project_id=project.id, goal="Build state")
    task = TaskState(
        id="task_1",
        run_id=run.id,
        title="Plan state",
        assigned_agent=AgentRole.PLANNER,
        status=TaskStatus.ASSIGNED,
    )
    message = AgentMessage.model_validate(
        {
            "id": "msg_1",
            "projectId": project.id,
            "runId": run.id,
            "taskId": task.id,
            "from": "controller",
            "to": "planner",
            "type": "task_assignment",
            "instructions": "Plan the state layer.",
            "expectedOutput": {"type": "plan"},
        }
    )
    result = AgentResult(
        id="result_1",
        message_id=message.id,
        task_id=task.id,
        agent=AgentRole.PLANNER,
        result={"plan": ["schema", "store"]},
        evidence=["issue #5"],
        confidence=0.9,
    )
    decision = DecisionRecord(
        id="decision_1",
        run_id=run.id,
        summary="Use SQLite",
        reason="Local persistence with no network database.",
        chosenOption="SQLite",
        rejectedOptions=["network database"],
    )
    conflict = ConflictRecord(
        id="conflict_1",
        runId=run.id,
        taskIds=[task.id],
        summary="Planner and QA disagree",
    )

    store.save_project(project)
    store.save_run(run)
    store.save_task(task)
    store.save_agent_message(message)
    store.save_agent_result(result)
    store.save_decision(decision)
    store.save_conflict(conflict)

    loaded_project = store.get_project(project.id)
    loaded_run = store.get_run(run.id)

    assert loaded_project == project
    assert loaded_run == run
    assert store.list_tasks(run.id) == [task]
    assert store.list_agent_messages(run.id) == [message]
    assert store.list_agent_results(task.id) == [result]
    assert store.list_decisions(run.id) == [decision]
    assert store.list_conflicts(run.id) == [conflict]


def test_store_updates_existing_project(tmp_path) -> None:
    store = ProjectStore(tmp_path / "ligent.sqlite")
    store.save_project(ProjectState(id="project_1", name="Ligent"))
    store.save_project(ProjectState(id="project_1", name="Ligent updated"))

    loaded_project = store.get_project("project_1")

    assert loaded_project is not None
    assert loaded_project.name == "Ligent updated"
