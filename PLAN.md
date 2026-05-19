# Ligent Project Plan

## Product Goal

Ligent is a local-first coding agent orchestration system for software projects. It acts as the single controller between the user, project state, tools, local LLM providers, and specialized sub-agents. Its job is to turn a user goal into coordinated work across planning, design, implementation, testing, deployment, and documentation without losing context or letting agents conflict with each other.

The product should be optimized for efficient local Ollama models, especially small models such as Qwen and Gemma. Larger hosted providers can remain possible behind an adapter, but they are not the MVP default.

## MVP Definition

The MVP should prove that Ligent can coordinate a small software task end to end with multiple specialized agents while keeping a clear project record.

### MVP Capabilities

- User interacts only with Ligent.
- Ligent runs primarily against local Ollama models.
- Ligent decomposes a user request into tasks.
- Ligent assigns tasks to specialized sub-agents.
- Sub-agents return structured outputs through Ligent.
- Ligent maintains shared project context and task state.
- Ligent resolves basic conflicts between agent outputs.
- Ligent produces a final implementation summary and next-step recommendation.

### Out of Scope for MVP

- Long-running autonomous production deployment.
- Real-time always-on sub-agent processes.
- Self-modifying tools without human approval.
- Complex learning from historical projects.
- Full visual dashboard.
- Multi-user collaboration.
- Hosted LLM provider integrations as the default path.

## Core Design Decisions

### User Interaction

For the MVP, the user talks only to Ligent. Direct user-to-sub-agent messaging should be avoided because it weakens Ligent's role as the source of truth.

### Sub-Agent Lifecycle

Sub-agents should be spawned on demand for each task. This keeps the system simpler, cheaper, and easier to reason about. Persistent agents can be added later if task memory becomes necessary.

### State Model

Ligent owns the shared state. Sub-agents receive scoped context and return structured results. They should not directly mutate global project state.

Because the default models are small local models, state and prompts should stay compact. Ligent should pass only the task brief, relevant files or summaries, explicit constraints, and expected output schema needed for the assigned work.

Minimum shared state:

- Project brief
- User goal
- Requirements
- Task list
- Agent assignments
- Agent outputs
- Decisions
- Conflicts
- Final result

### Coordination Model

Ligent uses hub-and-spoke coordination:

1. User sends request to Ligent.
2. Ligent updates project state.
3. Ligent decomposes the request into tasks.
4. Ligent delegates scoped work to sub-agents.
5. Sub-agents return structured results.
6. Ligent synthesizes outputs.
7. Ligent asks follow-up agents only when needed.
8. Ligent returns the final answer to the user.

The controller should prefer fewer, higher-quality delegation rounds over broad fan-out. Local models are fast and cheap to run, but the orchestration loop should still minimize redundant context, repeated reasoning, and unnecessary agent calls.

### Conflict Resolution

Ligent resolves conflicts using this priority order:

1. Explicit user requirements
2. Project constraints
3. Existing codebase behavior
4. Test results
5. Agent confidence and evidence
6. Ligent's own judgment

All meaningful conflicts should be recorded as decisions.

## Agent Roles

### Ligent Controller

Responsibilities:

- Own project context
- Interpret user intent
- Create and prioritize tasks
- Select sub-agents
- Route messages
- Enforce permissions
- Resolve conflicts
- Summarize progress
- Decide when the work is complete

### Planner Agent

Responsibilities:

- Break down requirements
- Identify dependencies
- Estimate task complexity
- Produce execution plans
- Identify unclear requirements

### Designer Agent

Responsibilities:

- Design UX flows
- Propose system architecture
- Model data structures
- Identify user-facing tradeoffs

### Frontend Agent

Responsibilities:

- Implement UI
- Build client-side state and interaction logic
- Follow design system constraints
- Report integration needs to Ligent

### Backend Agent

Responsibilities:

- Implement APIs
- Model persistence
- Enforce business rules
- Handle auth and security concerns

### QA Agent

Responsibilities:

- Design test cases
- Validate acceptance criteria
- Find regressions
- Report risk and edge cases

### DevOps Agent

Responsibilities:

- Configure build and deployment workflows
- Manage environment assumptions
- Report operational risks

### Documentation Agent

Responsibilities:

- Write user-facing and technical documentation
- Maintain changelog notes
- Produce handoff summaries

## Technical Architecture

### Recommended MVP Stack

Because the repository is empty, the first implementation should optimize for fast iteration and clear boundaries.

Recommended stack:

- Desktop: Tauri with React
- Backend: Python with FastAPI
- Interface: lightweight Tauri desktop interface with React
- Persistence: SQLite plus project files
- Agent abstraction: provider-agnostic LLM adapter
- Default LLM provider: Ollama over localhost
- Default model targets: small local coding-capable models such as Qwen and Gemma
- Validation: Pydantic for backend contracts, Zod for UI-facing TypeScript contracts if needed
- Tests: Python unit tests for backend, UI tests for desktop flows

The lightweight interface should prove the core orchestration loop without becoming a full dashboard. Keep the UI focused on one user goal input, live progress, agent outputs, decisions, conflicts, and final results.

### Local Model Strategy

The MVP should treat local Ollama as the first real provider.

Design rules:

- Keep the provider interface generic, but implement the Ollama provider in the Python backend before any hosted provider.
- Do not require API keys for the default local path.
- Keep prompts short, role-specific, and schema-driven.
- Use deterministic settings where possible for planning, validation, and merge decisions.
- Validate every model response with Pydantic before it reaches controller state.
- Retry malformed output with a smaller repair prompt before failing the task.
- Prefer task-specific context summaries over dumping full files or full project history.
- Record model name, provider, prompt size estimate, response validation status, and retry count in task metadata.
- Fail closed when a local model asks for a tool or file path outside the task scope.

The first supported provider should call Ollama's local HTTP API. Hosted providers can be added later as optional adapters if the core orchestration loop proves useful.

### Main Modules

```text
ligent/
  desktop/                  # Tauri app
    src/                    # React UI
    src-tauri/

  backend/                  # Python backend
    app.py                  # FastAPI app
    agents/                 # ADK agents
    services/
    tools/
    state/
    pyproject.toml

  workspace/                # User project files
  README.md
```

The execution flow should be:

```text
Tauri desktop UI
  -> React dashboard
  -> FastAPI backend / Tauri commands
  -> Ligent backend orchestrator
  -> Planner / Design / Implement / QA / DevOps agents
  -> Ollama local models
  -> SQLite + project files
```

### Message Contracts

All agent communication should use structured messages.

Core message fields:

- `id`
- `projectId`
- `from`
- `to`
- `type`
- `taskId`
- `context`
- `instructions`
- `constraints`
- `expectedOutput`
- `result`
- `evidence`
- `confidence`

### Task States

Tasks should move through explicit states:

- `pending`
- `assigned`
- `in_progress`
- `blocked`
- `completed`
- `rejected`
- `merged`

### Decision Records

Ligent should write decision records when:

- User requirements are clarified
- Agents disagree
- Ligent overrides an agent recommendation
- Scope is changed
- A risky assumption is accepted

Decision record fields:

- `id`
- `timestamp`
- `summary`
- `reason`
- `inputs`
- `chosenOption`
- `rejectedOptions`

## Implementation Milestones

### Milestone 1: Project Foundation

Goal: Create the initial Tauri desktop app and Python backend with a runnable lightweight local interface.

Deliverables:

- `package.json`
- Desktop app setup
- `backend/pyproject.toml`
- FastAPI app entry point
- Minimal goal input and run view
- Basic test setup
- Lint or formatting baseline

Acceptance criteria:

- Desktop build/test command runs
- Backend test command runs
- The local interface can submit a goal and show a placeholder run result.

### Milestone 2: Core State and Contracts

Goal: Define the orchestration data model.

Deliverables:

- Project state schema
- Task schema
- Agent message schema
- Decision record schema
- Local project store

Acceptance criteria:

- Project state can be created, saved, loaded, and validated.
- Invalid agent messages fail validation.

### Milestone 3: Ligent Controller Loop

Goal: Implement the central orchestration loop.

Deliverables:

- `LigentController`
- Task decomposition interface
- Agent dispatch interface
- Result synthesis interface
- Decision recording

Acceptance criteria:

- A user request can become a project state with tasks.
- Ligent can assign tasks to mock agents.
- Ligent can merge mock agent results into a final summary.

### Milestone 4: Sub-Agent Framework

Goal: Add specialized agent definitions.

Deliverables:

- Agent role definitions
- Prompt templates or instruction builders
- Mock provider support
- LLM provider interface
- Local-model prompt constraints

Acceptance criteria:

- Each MVP agent can receive a scoped task.
- Each agent returns a validated structured result.
- Ligent rejects malformed agent output.
- Agent prompts stay compact enough for small local models.

### Milestone 5: Conflict Handling

Goal: Add basic conflict detection and arbitration.

Deliverables:

- Conflict detection rules
- Conflict resolver
- Decision record generation

Acceptance criteria:

- Ligent detects incompatible agent recommendations.
- Ligent records why one recommendation was chosen.

### Milestone 6: Local Ollama Provider

Goal: Connect the orchestrator to local Ollama models.

Deliverables:

- Ollama provider configuration
- Local model selection
- Structured response validation
- Retry and error handling
- Clear setup checks for missing Ollama or missing models

Acceptance criteria:

- Ligent can run one real multi-agent planning session from the local interface using a local Ollama model.
- Failed or malformed model output is handled gracefully.
- The default path does not require hosted API keys or network access.

### Milestone 7: End-to-End Demo

Goal: Demonstrate Ligent on a small software request.

Deliverables:

- Example project run
- Stored project state
- Final summary
- README usage instructions

Acceptance criteria:

- A new user can run the demo locally.
- The demo shows at least Planner, Designer, Backend or Frontend, QA, and Documentation participating through Ligent.

## First Implementation Sequence

1. Initialize the Tauri desktop app under `desktop/`.
2. Add schemas for project state, tasks, messages, agent results, and decisions.
3. Initialize the Python FastAPI backend under `backend/`.
4. Implement a SQLite-backed project store.
5. Implement mock ADK-style agents with deterministic outputs.
6. Implement `LigentController.run(userRequest)`.
7. Add tests for state creation, task assignment, message validation, and result synthesis.
8. Add the local Ollama provider after the orchestration loop works with mocks.
9. Add README instructions and a sample local interface run.

## Key Risks

### Over-Broad Scope

The product can easily become too large. Keep the MVP focused on orchestration, not a full IDE, deployment platform, or autonomous company.

### Weak State Ownership

If sub-agents mutate shared state directly, coordination will become unreliable. Ligent must own state changes.

### Unstructured Agent Output

Free-form agent output will make orchestration brittle. Structured schemas should be mandatory from the beginning.

### Small-Model Drift

Small local models may ignore instructions, produce malformed JSON, or overreach beyond the scoped task. Keep prompts short, validate all outputs, retry with repair prompts, and fail closed when output cannot be trusted.

### Premature Dashboard Work

A richer dashboard may be useful later, but the MVP interface should stay focused on the orchestration run itself.

### Unsafe Tool Creation

Dynamic tool creation should require explicit approval and sandboxing. For MVP, tools should be declared statically.

## Future Phases

### Phase 2: Dashboard

- Project timeline
- Agent activity stream
- Task board
- Decision log
- Conflict view

### Phase 3: Persistent Knowledge

- Project memory
- Reusable lessons
- Agent performance history
- Retrieval over previous project decisions

### Phase 4: Tool Marketplace

- Tool definitions
- Tool permissions
- Tool sharing rules
- Human approval workflow

### Phase 5: Deployment Orchestration

- CI/CD integration
- Environment management
- Release notes
- Monitoring feedback loop

## Success Metrics

- Ligent can produce a coherent plan from an ambiguous user request.
- Ligent can coordinate at least three agents without direct agent-to-agent communication.
- Ligent can run its default path with a local Ollama model.
- Agent outputs are structured, validated, and traceable.
- Conflicts are recorded and resolved.
- The final result explains what happened, what changed, and what remains.
