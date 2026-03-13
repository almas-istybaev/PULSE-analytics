---
name: sequential-thinking
description: Advanced tool for dynamic and reflective problem-solving through thoughts. Helps analyze problems, plan designs with room for revision, and maintain context over multiple steps.
---

# Sequential Thinking Skill

This skill empowers the agent to use the `sequential-thinking` MCP tool for tackling complex, non-linear problems within the PULSE project. It promotes a reflective and iterative approach to coding, architectural design, and debugging.

## 1. When to Use Sequential Thinking

Use this skill when facing:
- **Complex Architectural Changes**: When refactoring core modules (e.g., migrating business logic from routers to services).
- **Subtle Bug Hunting**: When debugging issues involving race conditions, multi-service state synchronization, or complex data flow.
- **Multi-Step Feature Planning**: When implementing features that span across both FastAPI backend and React frontend, requiring careful sequencing of database migrations, API development, and UI implementation.
- **Optimization Tasks**: When analyzing performance bottlenecks that require evaluating multiple alternative solutions (e.g., SQLite indexing vs. caching).

## 2. Core Principles

- **Iterative Thinking**: Don't aim for the final answer in one go. Break the problem down into sequential thoughts.
- **Reflection and Revision**: Use the `isRevision` flag to revisit and correct previous assumptions as new information emerges.
- **Branching**: Use `branchFromThought` to explore alternative architectural paths or debugging hypotheses without losing the original context.
- **Context Preservation**: The tool maintains history, allowing for deep analysis without "forgetting" early constraints.

## 3. Practical Workflow in PULSE

### Refactoring Logic
1. **Thought 1**: Analyze current implementation (e.g., in `routers/`).
2. **Thought 2**: Outline the target structure (e.g., moving to `services/` and `repositories/`).
3. **Thought 3**: Identify dependencies and potential breaking changes.
4. **Branch A**: Explore a "safe" incremental migration.
5. **Branch B**: Explore a "full" revolutionary refactor if time permits.
6. **Revision**: If a test fails, revise the plan based on the error.

### Debugging API Issues
1. **Thought 1**: Trace the request from the React frontend.
2. **Thought 2**: Examine FastAPI middleware or auth guards.
3. **Thought 3**: Hypothesize about database state.
4. **Revision**: If logs show a different path, mark previous thoughts as "reconsidered".

## 4. Guidelines for the Agent

- **Be Expressive**: Explain *why* a certain branch is being explored.
- **Acknowledge Uncertainty**: If a specific line of reasoning is a guess, flag it.
- **Stay Focused**: Use the `totalThoughts` estimate to keep the process structured and avoid infinite loops.
- **Verify Hypotheses**: Always end with a verification step that maps back to the project's standards (FastAPI + React + SDD).

## 5. Usage

Invoke this thinking process when a task feels "messy" or has high stakes for the system's stability. Start the `sequentialthinking` tool at the beginning of the analysis phase.
