# Ligent

Ligent is a lightweight local coding-agent controller. The desktop app sends a goal to the FastAPI backend, the controller assigns scoped agent tasks, stores the run in SQLite, and returns a coherent result for the user to review.

## Requirements

- Node.js 20+
- npm 10+
- Python 3.13+
- Rust and Cargo for Tauri builds
- Ollama for local model planning

## Setup

Install JavaScript and Python dependencies:

```sh
npm install
npm run backend:install
```

Install and start Ollama, then pull a small local model:

```sh
ollama serve
ollama pull gemma4:e2b
```

You can also use another local model, such as a Qwen or Gemma tag available in your Ollama install.

## Run The Demo

Start the backend:

```sh
npm run backend:dev
```

In another terminal, start the desktop UI:

```sh
npm run desktop:dev
```

Open the Vite URL shown by the command, usually `http://127.0.0.1:1420`. The demo goal is prefilled. Click `Run local demo` to create a persisted run and show task progress, agent outputs, decisions, and the final summary.

For the Tauri shell:

```sh
npm run tauri:dev
```

## Local Ollama Planning

The backend also exposes a local model planning path:

```sh
curl -X POST http://127.0.0.1:8765/runs/ollama-plan \
  -H 'Content-Type: application/json' \
  -d '{"goal":"Plan a small Ligent change","model":"gemma4:e2b"}'
```

Set `LIGENT_OLLAMA_MODEL` to change the default model used when the request does not include one.

## Agents

Ligent's role agents live in `backend/agents/` and are built with `google-adk` against local Ollama via `LiteLlm`. The controller runs Planner, Design, Implement, QA, DevOps, and Documentation as separate scoped turns, then persists their outputs in SQLite.

The agent package follows the ADK/agents-cli style of a root controller plus specialized sub-agents. The current runtime is local-only and does not require hosted API keys by default.

To run the ADK-backed preview path directly:

```sh
curl -X POST http://127.0.0.1:8765/runs/adk-preview \
  -H 'Content-Type: application/json' \
  -d '{"goal":"Plan a small Ligent change"}'
```

## Validation

```sh
npm run backend:test
npm run desktop:typecheck
npm run desktop:build
```

Run state is stored in `backend/.local/ligent.sqlite` by default. Set `LIGENT_STATE_DB` to use a different SQLite file.
