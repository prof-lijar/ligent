# Ligent Project Plan

## Product Goal

Ligent is an agent orchestration system for software projects. It acts as the single controller between the user, project state, tools, and specialized sub-agents. Its job is to turn a user goal into coordinated work across planning, design, implementation, testing, deployment, and documentation without losing context or letting agents conflict with each other.

## MVP Definition

The MVP should prove that Ligent can coordinate a small software task end to end with multiple specialized agents while keeping a clear project record.

### MVP Capabilities

- User interacts only with Ligent.
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

## Core Design Decisions

### User Interaction

For the MVP, the user talks only to Ligent. Direct user-to-sub-agent messaging should be avoided because it weakens Ligent's role as the source of truth.

### Sub-Agent Lifecycle

Sub-agents should be spawned on demand for each task. This keeps the system simpler, cheaper, and easier to reason about. Persistent agents can be added later if task memory becomes necessary.

### State Model

Ligent owns the shared state. Sub-agents receive scoped context and return structured results. They should not directly mutate global project state.

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

- Runtime: Node.js with TypeScript
- Interface: CLI first
- Persistence: local JSON files or SQLite
- Agent abstraction: provider-agnostic LLM adapter
- Validation: Zod schemas for all agent messages
- Tests: Vitest

The CLI-first approach keeps the orchestration engine independent from any future dashboard.

### Main Modules

```text
src/
  cli/
    index.ts
  core/
    ligent.ts
    project-state.ts
    task-planner.ts
    conflict-resolver.ts
  agents/
    types.ts
    planner.ts
    designer.ts
    frontend.ts
    backend.ts
    qa.ts
    devops.ts
    documentation.ts
  llm/
    provider.ts
    mock-provider.ts
  storage/
    project-store.ts
  schemas/
    messages.ts
    project.ts
  tests/
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

Goal: Create the initial TypeScript project with a runnable CLI.

Deliverables:

- `package.json`
- TypeScript config
- CLI entry point
- Basic test setup
- Lint or formatting baseline

Acceptance criteria:

- `npm test` runs
- `npm run build` runs
- CLI can print help text

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

Acceptance criteria:

- Each MVP agent can receive a scoped task.
- Each agent returns a validated structured result.
- Ligent rejects malformed agent output.

### Milestone 5: Conflict Handling

Goal: Add basic conflict detection and arbitration.

Deliverables:

- Conflict detection rules
- Conflict resolver
- Decision record generation

Acceptance criteria:

- Ligent detects incompatible agent recommendations.
- Ligent records why one recommendation was chosen.

### Milestone 6: Real LLM Provider

Goal: Connect the orchestrator to a real model provider.

Deliverables:

- Provider configuration
- API key loading
- Structured response validation
- Retry and error handling

Acceptance criteria:

- Ligent can run one real multi-agent planning session from the CLI.
- Failed or malformed model output is handled gracefully.

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

1. Initialize a TypeScript CLI project.
2. Add schemas for project state, tasks, messages, agent results, and decisions.
3. Implement a local JSON project store.
4. Implement mock agents with deterministic outputs.
5. Implement `LigentController.run(userRequest)`.
6. Add tests for state creation, task assignment, message validation, and result synthesis.
7. Add a real LLM provider after the orchestration loop works with mocks.
8. Add README instructions and a sample run.

## Key Risks

### Over-Broad Scope

The product can easily become too large. Keep the MVP focused on orchestration, not a full IDE, deployment platform, or autonomous company.

### Weak State Ownership

If sub-agents mutate shared state directly, coordination will become unreliable. Ligent must own state changes.

### Unstructured Agent Output

Free-form agent output will make orchestration brittle. Structured schemas should be mandatory from the beginning.

### Premature Dashboard Work

A dashboard may be useful later, but the engine should work independently first.

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
- Agent outputs are structured, validated, and traceable.
- Conflicts are recorded and resolved.
- The final result explains what happened, what changed, and what remains.
