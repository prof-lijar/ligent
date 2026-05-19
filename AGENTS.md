# AGENTS.md

## Project Priority

Ligent must stay fast, light, performance-focused, and secure by default.

When making decisions, use this priority order:

1. Correctness and security
2. Fast user feedback
3. Low runtime and dependency weight
4. Clear, maintainable architecture
5. Extensibility after the MVP proves the core loop

## Product Direction

Ligent is an agent orchestration system for software projects. The user should interact with Ligent as the single controller. Ligent owns shared project context, delegates scoped tasks to sub-agents, receives structured outputs, resolves conflicts, and returns a coherent result.

Keep the MVP centered on a lightweight local interface. Prefer implementation choices that prove the orchestration loop end to end before adding a full dashboard or long-running infrastructure.

## Architecture Rules

- Follow `ARCHITECTURE.md` as the source of truth for the repository structure.
- Follow this required layout: `desktop/` for the Tauri app, `desktop/src/` for React UI, `desktop/src-tauri/` for the Tauri shell, `backend/` for the Python/FastAPI orchestrator, and `workspace/` for user project files.
- For Tauri setup, APIs, permissions, commands, and configuration, check the official Tauri repository/docs first: https://github.com/tauri-apps/tauri
- Keep the controller as the source of truth for project state, task state, agent outputs, decisions, and conflicts.
- Sub-agents should receive scoped context and return structured results. They should not directly mutate global state.
- For agent design, agent CLIs, task delegation, and orchestration patterns, check these references before implementation: https://github.com/google/agents-cli and https://github.com/google/adk-python
- Do not put agent orchestration logic in React components or Tauri command handlers.
- Use `backend/app.py` and explicit FastAPI routes as the boundary exposed to the desktop app.
- Use explicit message contracts for all agent communication.
- Prefer provider-agnostic interfaces around LLM calls so the core orchestration logic is not tied to one vendor.
- Keep modules small and focused. Avoid framework-heavy abstractions before the MVP needs them.
- Use structured validation at boundaries. Prefer Pydantic for Python backend contracts and Zod only for frontend/UI-facing TypeScript contracts.
- Use SQLite plus project files for MVP persistence. Do not introduce a network database until there is a concrete need.

## Performance Rules

- Optimize first for startup time, low memory use, and responsive local UI interactions.
- Avoid large dependencies unless they remove substantial complexity.
- Do not add background workers, daemons, polling loops, or persistent sub-agent processes unless explicitly required.
- Spawn sub-agents on demand for scoped tasks.
- Keep context passed to sub-agents minimal and relevant. Do not forward full project history when a smaller brief is enough.
- Cache only where it is simple, correct, and measurable.
- Prefer streaming or incremental progress updates for long operations.

## Security Rules

- Treat user goals, project files, environment variables, credentials, and agent outputs as untrusted inputs.
- Never log secrets, tokens, API keys, private prompts, or raw environment dumps.
- Never execute generated commands or code without explicit approval and a clear safety boundary.
- Validate all structured agent responses before using them.
- Keep tool permissions narrow. A sub-agent should only receive the tools and context needed for its task.
- Record security-relevant decisions and permission escalations in project state.
- Fail closed on ambiguous permissions, unknown tool requests, invalid schemas, or unsafe file paths.
- Do not add telemetry, remote reporting, or external network calls without explicit user approval.

## Implementation Style

- Prefer Python for backend orchestration and TypeScript for the desktop UI.
- Keep backend services small, typed, and explicit.
- Keep public interfaces boring and explicit.
- Use deterministic tests for orchestration, state transitions, conflict resolution, and schema validation.
- Avoid clever prompt-only behavior when a typed state machine or validation rule can enforce the same constraint.
- Keep generated summaries concise, evidence-based, and tied to task IDs or decision records.
- Leave unrelated files alone.

## Testing Expectations

Before handing off code changes, run the narrowest reliable validation available for the touched area.

Expected checks once the MVP exists:

- Type check for changed TypeScript UI code
- Python unit tests for changed backend orchestration logic
- Schema validation tests for changed Pydantic or Zod message contracts
- Local interface smoke test for changed user flows

If a check cannot run because the project has not been scaffolded yet, state that clearly in the final response.

## Documentation Expectations

- Update `PLAN.md` when product direction, MVP scope, or architecture decisions change.
- Update `ARCHITECTURE.md` when repository structure, layer boundaries, or local execution flow changes.
- Keep `proposal.md` high-level and product-facing.
- Add concise developer docs only when they help future agents work faster or safer.
- Record meaningful tradeoffs as decisions instead of burying them in comments.

## Things To Avoid

- Heavy frameworks before the core orchestration loop exists.
- Global mutable state outside the controller.
- Direct user-to-sub-agent workflows in the MVP.
- Long-running autonomous deployment or production mutation.
- Mock behavior that hides missing core orchestration behavior.
- Broad file-system, shell, or network access for sub-agents.
- Full dashboards, plugin systems, or learning systems before the MVP is proven.
