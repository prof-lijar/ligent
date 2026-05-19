from tools import ToolDecision, ToolName, ToolPermissionGate, ToolRequest
from state.models import ProjectState, RunState
from state.store import ProjectStore


def make_request(
    tool: ToolName,
    *,
    path: str | None = None,
    command: list[str] | None = None,
    approved: bool = False,
) -> ToolRequest:
    return ToolRequest(
        runId="run_1",
        taskId="task_1",
        tool=tool,
        path=path,
        command=command,
        approved=approved,
        reason="test request",
    )


def test_allows_workspace_read(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    gate = ToolPermissionGate(workspace)

    result = gate.evaluate(make_request(ToolName.READ_FILE, path="src/app.py"))

    assert result.decision == ToolDecision.ALLOW
    assert result.resolved_path == str(workspace / "src/app.py")


def test_rejects_path_outside_workspace(tmp_path) -> None:
    gate = ToolPermissionGate(tmp_path / "workspace")

    result = gate.evaluate(make_request(ToolName.READ_FILE, path="../secret.txt"))

    assert result.decision == ToolDecision.DENY
    assert result.reason == "Path is outside the workspace."


def test_write_requires_approval(tmp_path) -> None:
    gate = ToolPermissionGate(tmp_path / "workspace")

    result = gate.evaluate(make_request(ToolName.WRITE_FILE, path="README.md"))

    assert result.decision == ToolDecision.NEEDS_APPROVAL
    assert result.reason == "File writes require explicit approval."


def test_approved_write_is_allowed(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    gate = ToolPermissionGate(workspace)

    result = gate.evaluate(
        make_request(ToolName.WRITE_FILE, path="README.md", approved=True)
    )

    assert result.decision == ToolDecision.ALLOW
    assert result.resolved_path == str(workspace / "README.md")


def test_command_requires_approval(tmp_path) -> None:
    gate = ToolPermissionGate(tmp_path / "workspace")

    result = gate.evaluate(make_request(ToolName.RUN_COMMAND, command=["npm", "test"]))

    assert result.decision == ToolDecision.NEEDS_APPROVAL
    assert result.command == ["npm", "test"]


def test_approved_command_is_allowed(tmp_path) -> None:
    gate = ToolPermissionGate(tmp_path / "workspace")

    result = gate.evaluate(
        make_request(ToolName.RUN_COMMAND, command=["npm", "test"], approved=True)
    )

    assert result.decision == ToolDecision.ALLOW
    assert result.command == ["npm", "test"]


def test_permission_decision_is_recorded(tmp_path) -> None:
    store = ProjectStore(tmp_path / "state.sqlite")
    store.save_project(ProjectState(id="project_1", name="Ligent"))
    store.save_run(RunState(id="run_1", project_id="project_1", goal="Test tools"))
    gate = ToolPermissionGate(tmp_path / "workspace", store=store)

    result = gate.evaluate(make_request(ToolName.READ_FILE, path="README.md"))
    decisions = store.list_decisions("run_1")

    assert result.decision == ToolDecision.ALLOW
    assert len(decisions) == 1
    assert decisions[0].summary == "Tool request allow: read_file"
