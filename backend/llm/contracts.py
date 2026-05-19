from typing import Protocol


class JsonLLMProvider(Protocol):
    def generate_json(
        self,
        *,
        model: str,
        prompt: str,
        schema_hint: str,
    ) -> dict[str, object]:
        """Return parsed JSON from a local model provider."""


class UrlOpen(Protocol):
    def __call__(self, request: object, *, timeout: float) -> object:
        """Small urllib-compatible transport hook for tests."""
