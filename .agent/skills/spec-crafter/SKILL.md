---
name: spec-crafter
description: Master of Spec-Driven Development, handling task tracking, specification generation, and dependency mapping.
---

# Spec Crafter

This skill empowers the agent to expertly manage the `.specify/` directory, treating specs as executable code.

## 1. Specification Generation
- **Format**: Every new spec must follow the standard markdown structure: Context, Proposed Solution, Database Changes, API Changes, UI Changes, and Implementation Steps.
- **Diagrams**: Actively use Mermaid.js code blocks (`mermaid`) to visually map out architecture, state machines, or data flows within `spec.md`.

## 2. Task Management (`tasks.md`)
- Keep `tasks.md` extremely granular.
- Use `[ ]` for pending, `[/]` for in-progress, and `[x]` for completed.
- Update `tasks.md` instantly as work progresses, never batching updates at the end.

## 3. Dependency Tracking
- Always read related specs before starting a new one. For instance, if modifying frontend architecture (Spec 007), cross-reference it with the PIM Module (Spec 006) to ensure no regressions.
- Update the main `constitution.md` or `memory/` files if a specific architecture decision becomes a global rule.

## 4. Workflow Integration
When the user requests a new feature:
1. "Shall I create a Spec for this?"
2. Generate `00X-feature-name/spec.md` with deep technical details and Mermaid diagrams.
3. Wait for User Approval.
4. Generate `tasks.md`.
5. Execute.
