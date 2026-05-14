# Ligent — Agent Orchestrator

## Overview

Ligent is an LLM-powered agent orchestrator that acts as an overall agent controller. It possesses its own skills, knowledge, and experiences to coordinate multiple specialized sub-agents across the full software development lifecycle — from project planning through deployment and monitoring.

Ligent serves as the sole intermediary between all sub-agents, routing communication, resolving conflicts, and ensuring coherent project execution through a collaborative coordination model.

## Core Architecture

### Ligent (Controller Agent)

- LLM-powered agent with rules, skills, and tools
- Acts as the sole intermediary — all inter-agent communication flows through Ligent
- Can dynamically create tools for sub-agents on its own initiative or by user request
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

## Open Questions

### Ligent's Knowledge & Learning
- What gives Ligent its skills and knowledge? (Knowledge base, RAG, system prompts, rules, or a combination)
- Does Ligent learn from past projects to improve orchestration over time?

### Sub-Agent Lifecycle
- Are sub-agents persistent (always running, maintaining state) or spawned on demand?
- Does each sub-agent have a fixed configuration, or can Ligent reconfigure them per project?

### Collaboration Details
- When a sub-agent needs input from another, does Ligent only route on request, or does it proactively anticipate needs?
- How are cross-agent conflicts resolved beyond arbitration?

### User Interaction
- Does the user interact only with Ligent, or can they directly address individual sub-agents?
- What is the user interface — chat, dashboard, hybrid, or something else?

### Tooling
- What is the mechanism for Ligent to dynamically create tools for sub-agents?
- Are tools shared across sub-agents, or strictly isolated per agent?
