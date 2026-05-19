# Ligent Architecture

## Direction

Ligent is a lightweight desktop coding agent interface backed by a local agent orchestrator. The interface should stay fast and focused: submit a goal, inspect progress, review agent outputs, resolve conflicts, and receive a coherent final result.

The default execution path is local-first:

```text
Tauri desktop UI
  -> React dashboard
  -> FastAPI backend / Tauri commands
  -> Ligent backend orchestrator
  -> Planner / Design / Implement / QA / DevOps agents
  -> Ollama local models
  -> SQLite + project files
```

## Repository Structure

```text
ligent/
  desktop/                  # Tauri app
    src/                    # React UI
    src-tauri/

  backend/                  # Python backend
    app.py                  # FastAPI app
    agents/                 # ADK agents
    llm/                    # Local/provider-agnostic LLM adapters
    services/
    tools/
    state/
    pyproject.toml

  workspace/                # User project files
  README.md
```

## Layer Responsibilities

### Desktop UI (`desktop/src/`)

- Owns the visible user experience.
- Provides the lightweight dashboard for goal input, run progress, task state, agent outputs, decisions, conflicts, and final summaries.
- Uses stores for UI state and run state projection.
- Does not own orchestration decisions or mutate project state directly.
- Use React for the MVP UI. Do not introduce Svelte unless the product direction changes explicitly.

### Tauri Shell (`desktop/src-tauri/`)

- Owns the desktop runtime boundary.
- Exposes narrow commands for the React UI to start runs, inspect state, approve actions, and read results.
- Keeps local file and command permissions explicit.
- Does not contain orchestration business logic beyond command wiring.
- Uses the official Tauri repository/docs as the reference for future setup, APIs, permissions, commands, and configuration: https://github.com/tauri-apps/tauri

### Python Backend (`backend/`)

- Owns the FastAPI app, controller, agent contracts, state transitions, tool boundaries, and local model provider integration.
- Keeps the controller as the source of truth for tasks, outputs, decisions, conflicts, and final synthesis.
- Validates all structured agent responses before they affect state.
- Keeps sub-agents scoped and on demand.

### Workspace (`workspace/`)

- Contains user project files that Ligent is allowed to inspect or modify.
- Treat all content as untrusted input.
- Keep tool access scoped to the active project and explicit user-approved actions.

## Backend Subdirectories

### `backend/agents/`

ADK agent definitions, prompt builders, dispatch logic, and structured result contracts.

Use these references for future agent design, agent CLI patterns, task delegation, and orchestration decisions:

- https://github.com/google/agents-cli
- https://github.com/google/adk-python

### `backend/llm/`

Provider-agnostic local model interfaces, Ollama integration, provider errors, and model response contracts.

The default provider path is Ollama over `http://127.0.0.1:11434`. Use `LIGENT_OLLAMA_MODEL` to override the default model, or pass a model in the local planning request. Keep model outputs schema-driven and validate them with Pydantic before controller state changes.

### `backend/services/`

Controller services, orchestration use cases, run lifecycle, synthesis, and conflict resolution.

### `backend/tools/`

Tool definitions, permission checks, command/file safety boundaries, and tool result contracts.

### `backend/state/`

Project state, task state, decision records, conflict records, persistence models, and SQLite/local file storage adapters.

### `backend/app.py`

FastAPI app entry point. This is the boundary exposed to the desktop app.

## Rules

- Keep UI, desktop shell, backend, and workspace boundaries separate.
- Do not put agent orchestration logic in React components.
- Do not put agent orchestration logic in Tauri command handlers.
- Keep orchestration logic in `backend/`.
- Do not let sub-agents mutate global state directly.
- Keep Tauri commands narrow and explicit.
- Use SQLite plus project files for local persistence.
- Use Ollama local models as the default model path.
- Keep hosted providers optional and behind provider adapters.
- Keep prompts compact and scoped for small local models such as Qwen and Gemma.
