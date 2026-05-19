from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ligent-backend"}


def test_preview_run_returns_typed_placeholder(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LIGENT_STATE_DB", str(tmp_path / "ligent.sqlite"))

    response = client.post(
        "/runs/preview",
        json={"goal": "Scaffold the Ligent backend"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["runId"].startswith("run_")
    assert body["status"] == "completed"
    assert body["summary"]
    assert body["nextStep"] == (
        "Review persisted tasks, agent results, and the controller decision."
    )
    assert body["assignedAgents"] == [
        "planner",
        "design",
        "implement",
        "qa",
        "devops",
        "documentation",
    ]
    assert body["createdAt"]


def test_preview_run_rejects_empty_goal() -> None:
    response = client.post("/runs/preview", json={"goal": ""})

    assert response.status_code == 422


def test_backend_allows_local_desktop_origin() -> None:
    response = client.options(
        "/runs/preview",
        headers={
            "Origin": "http://127.0.0.1:1420",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://127.0.0.1:1420"
    )
