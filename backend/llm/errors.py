class LLMProviderError(RuntimeError):
    """Base error for local model provider failures."""


class OllamaUnavailableError(LLMProviderError):
    """Raised when the local Ollama server cannot be reached."""


class OllamaModelUnavailableError(LLMProviderError):
    """Raised when Ollama is running but the requested model is missing."""


class LLMResponseValidationError(LLMProviderError):
    """Raised when a model response cannot be parsed or repaired as JSON."""
