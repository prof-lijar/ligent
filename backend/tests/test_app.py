from fastapi.testclient import TestClient

import api.routes
from app import app
from llm.errors import OllamaModelUnavailableError, OllamaUnavailableError
from services.schemas import RunPreviewResponse


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


def test_ollama_plan_endpoint_returns_planner_response(monkeypatch) -> None:
    def fake_create_ollama_plan(payload: object) -> RunPreviewResponse:
        return RunPreviewResponse.model_validate(
            {
                "runId": "run_local",
                "status": "completed",
                "summary": "Local plan created.",
                "nextStep": "Review it.",
                "assignedAgents": ["planner"],
                "createdAt": "2026-05-19T00:00:00Z",
            }
        )

    monkeypatch.setattr(api.routes, "create_ollama_plan", fake_create_ollama_plan)

    response = client.post(
        "/runs/ollama-plan",
        json={"goal": "Plan with Ollama", "model": "qwen2.5-coder:7b"},
    )

    assert response.status_code == 200
    assert response.json()["summary"] == "Local plan created."


def test_ollama_plan_endpoint_reports_missing_ollama(monkeypatch) -> None:
    def fake_create_ollama_plan(payload: object) -> RunPreviewResponse:
        raise OllamaUnavailableError(
            "Ollama is not running at http://127.0.0.1:11434. "
            "Start it with `ollama serve`."
        )

    monkeypatch.setattr(api.routes, "create_ollama_plan", fake_create_ollama_plan)

    response = client.post("/runs/ollama-plan", json={"goal": "Plan with Ollama"})

    assert response.status_code == 503
    assert "ollama serve" in response.json()["detail"]


def test_ollama_plan_endpoint_reports_missing_model(monkeypatch) -> None:
    def fake_create_ollama_plan(payload: object) -> RunPreviewResponse:
        raise OllamaModelUnavailableError(
            "Ollama model 'gemma3:4b' is not available. "
            "Install it with `ollama pull gemma3:4b`."
        )

    monkeypatch.setattr(api.routes, "create_ollama_plan", fake_create_ollama_plan)

    response = client.post(
        "/runs/ollama-plan",
        json={"goal": "Plan with Ollama", "model": "gemma3:4b"},
    )

    assert response.status_code == 404
    assert "ollama pull gemma3:4b" in response.json()["detail"]
