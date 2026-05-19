from __future__ import annotations

from io import BytesIO
from urllib.error import HTTPError, URLError

from llm.errors import (
    LLMResponseValidationError,
    OllamaModelUnavailableError,
    OllamaUnavailableError,
)
from llm.ollama import OllamaProvider


class FakeResponse:
    def __init__(self, body: str) -> None:
        self.body = body

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body.encode("utf-8")


def test_ollama_provider_returns_parsed_json() -> None:
    def opener(request: object, *, timeout: float) -> FakeResponse:
        return FakeResponse(
            '{"response": "{\\"summary\\": \\"ok\\", \\"tasks\\": []}"}'
        )

    provider = OllamaProvider(opener=opener)

    result = provider.generate_json(
        model="qwen2.5-coder:7b",
        prompt="Plan",
        schema_hint='{"summary": "string"}',
    )

    assert result == {"summary": "ok", "tasks": []}


def test_ollama_provider_repairs_malformed_json() -> None:
    calls: list[object] = []

    def opener(request: object, *, timeout: float) -> FakeResponse:
        calls.append(request)
        if len(calls) == 1:
            return FakeResponse('{"response": "not json"}')
        return FakeResponse('{"response": "{\\"summary\\": \\"repaired\\"}"}')

    provider = OllamaProvider(opener=opener)

    result = provider.generate_json(
        model="qwen2.5-coder:7b",
        prompt="Plan",
        schema_hint='{"summary": "string"}',
    )

    assert result == {"summary": "repaired"}
    assert len(calls) == 2


def test_ollama_provider_rejects_unrepairable_json() -> None:
    def opener(request: object, *, timeout: float) -> FakeResponse:
        return FakeResponse('{"response": "still not json"}')

    provider = OllamaProvider(opener=opener)

    try:
        provider.generate_json(
            model="qwen2.5-coder:7b",
            prompt="Plan",
            schema_hint='{"summary": "string"}',
        )
    except LLMResponseValidationError as error:
        assert "repair attempt failed" in str(error)
    else:
        raise AssertionError("Expected malformed output to fail")


def test_ollama_provider_reports_missing_server() -> None:
    def opener(request: object, *, timeout: float) -> FakeResponse:
        raise URLError("connection refused")

    provider = OllamaProvider(opener=opener)

    try:
        provider.generate_json(
            model="qwen2.5-coder:7b",
            prompt="Plan",
            schema_hint='{"summary": "string"}',
        )
    except OllamaUnavailableError as error:
        assert "ollama serve" in str(error)
    else:
        raise AssertionError("Expected missing Ollama to fail")


def test_ollama_provider_reports_missing_model() -> None:
    def opener(request: object, *, timeout: float) -> FakeResponse:
        raise HTTPError(
            url="http://127.0.0.1:11434/api/generate",
            code=404,
            msg="not found",
            hdrs={},
            fp=BytesIO(b"model not found"),
        )

    provider = OllamaProvider(opener=opener)

    try:
        provider.generate_json(
            model="gemma3:4b",
            prompt="Plan",
            schema_hint='{"summary": "string"}',
        )
    except OllamaModelUnavailableError as error:
        assert "ollama pull gemma3:4b" in str(error)
    else:
        raise AssertionError("Expected missing model to fail")
