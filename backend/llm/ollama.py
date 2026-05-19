from __future__ import annotations

import json
from dataclasses import dataclass
from http.client import HTTPResponse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from llm.contracts import UrlOpen
from llm.errors import (
    LLMResponseValidationError,
    OllamaModelUnavailableError,
    OllamaUnavailableError,
)


@dataclass(frozen=True)
class OllamaProvider:
    base_url: str = "http://127.0.0.1:11434"
    timeout_seconds: float = 45.0
    opener: UrlOpen = urlopen

    def generate_json(
        self,
        *,
        model: str,
        prompt: str,
        schema_hint: str,
    ) -> dict[str, object]:
        first_response = self._generate(model=model, prompt=prompt)
        parsed = self._parse_json(first_response)
        if parsed is not None:
            return parsed

        repair_prompt = (
            "Return only valid JSON. Do not include markdown or commentary.\n"
            f"Required schema:\n{schema_hint}\n"
            "Repair this invalid response into valid JSON:\n"
            f"{first_response}"
        )
        repaired_response = self._generate(model=model, prompt=repair_prompt)
        repaired = self._parse_json(repaired_response)
        if repaired is None:
            raise LLMResponseValidationError(
                "Ollama returned malformed JSON and the repair attempt failed."
            )
        return repaired

    def _generate(self, *, model: str, prompt: str) -> str:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
        }
        request = Request(
            f"{self.base_url.rstrip('/')}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with self.opener(request, timeout=self.timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
        except HTTPError as error:
            message = self._read_error_body(error)
            if error.code == 404 or "not found" in message.lower():
                raise OllamaModelUnavailableError(
                    f"Ollama model '{model}' is not available. "
                    f"Install it with `ollama pull {model}`."
                ) from error
            raise OllamaUnavailableError(
                f"Ollama request failed with HTTP {error.code}: {message}"
            ) from error
        except URLError as error:
            raise OllamaUnavailableError(
                "Ollama is not running at "
                f"{self.base_url}. Start it with `ollama serve`."
            ) from error
        except TimeoutError as error:
            raise OllamaUnavailableError(
                f"Ollama did not respond within {self.timeout_seconds:.0f} seconds."
            ) from error

        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError as error:
            raise LLMResponseValidationError(
                "Ollama returned a non-JSON API response."
            ) from error

        model_response = body.get("response")
        if not isinstance(model_response, str):
            raise LLMResponseValidationError(
                "Ollama API response did not include a text response."
            )
        return model_response

    @staticmethod
    def _parse_json(raw_text: str) -> dict[str, object] | None:
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, dict):
            return None
        return parsed

    @staticmethod
    def _read_error_body(error: HTTPError) -> str:
        try:
            raw_body = error.read().decode("utf-8")
        except Exception:
            raw_body = ""
        return raw_body or error.reason or "unknown Ollama error"
