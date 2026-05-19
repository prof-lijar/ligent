# Ligent Agents

This package contains the local ADK-backed role agents used by Ligent.

Layout:

- `adk_models.py`: structured agent output contract
- `adk_runtime.py`: ADK + Ollama executor and agent factories
- `roles.py`: shared role enum
- `mock_agents.py`: legacy deterministic fallback used only for reference

The role agents are built with `google-adk` and `LiteLlm` against the local Ollama API.
The folder stays compatible with the ADK/agents-cli style of defining a root agent plus
specialized sub-agents.

Local model defaults:

- Ollama base URL: `http://127.0.0.1:11434`
- Default model: `gemma4:e2b`

Useful checks:

```sh
ollama serve
ollama list
```

If you install the Google agents CLI locally, keep this package structure aligned with
its scaffolded agent layout.
