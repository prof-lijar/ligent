# Ligent — Agent Orchestrator

## Overview

Ligent is a local-first, LLM-powered coding agent orchestrator that acts as an overall agent controller. It is designed to run efficiently with small Ollama models such as Qwen and Gemma while coordinating multiple specialized sub-agents across the full software development lifecycle — from project planning through deployment and monitoring.

Ligent serves as the sole intermediary between all sub-agents, routing communication, resolving conflicts, and ensuring coherent project execution through a collaborative coordination model.

## Core Architecture

### Ligent (Controller Agent)

- LLM-powered agent with rules, skills, and tools
- Acts as the sole intermediary — all inter-agent communication flows through Ligent
- Uses declared tools with explicit permission boundaries for the MVP
- Maintains overall project context, state, and history across all agents
- Arbitrates conflicts between sub-agents

### Sub-Agents

Each sub-agent has its own dedicated toolset and domain expertise.

| Agent | Responsibility |
|-------|---------------|
| **Planner** | Requirements breakdown, task decomposition, estimation, prioritization |
| **Designer** | UI/UX design, system architecture, data modeling |
| **Frontend** | UI implementation, client-side logic, component development |
| **Backend** | APIs, business logic, data layer, security |
| **QA** | Testing, validation, edge case analysis, quality assurance |
| **DevOps** | Deployment, CI/CD pipelines, infrastructure, monitoring |
| **Documentation** | Technical docs, API docs, user guides, changelogs |

## Coordination Model

Ligent uses a **collaborative** coordination model:

- Sub-agents can request information or assistance from other sub-agents through Ligent
- Ligent routes requests, provides relevant context, and synthesizes responses
- Ligent proactively identifies cross-agent dependencies and potential conflicts
- When sub-agents disagree (e.g., QA reports a bug, Frontend claims intended behavior), Ligent arbitrates based on project requirements and context

## MVP Decisions

### Ligent's Knowledge & Learning
- MVP knowledge comes from project files, explicit user goals, structured state, and concise agent instructions.
- Long-term learning from past projects is out of scope until the core orchestration loop is proven.

### Sub-Agent Lifecycle
- Sub-agents are spawned on demand for scoped tasks.
- Agent configuration is explicit and role-based for the MVP.

### Collaboration Details
- Sub-agent communication flows through Ligent only.
- Conflicts are resolved by Ligent using user requirements, project constraints, evidence, and test results.

### User Interaction
- The user interacts only with Ligent.
- The MVP interface is a lightweight Tauri desktop app with a React UI.

### Tooling
- MVP tools are declared statically and exposed through narrow permission boundaries.
- Sub-agents receive only the tools and context needed for their scoped task.
