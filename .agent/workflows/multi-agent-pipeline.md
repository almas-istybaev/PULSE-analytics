---
description: How to orchestrate multi-agent development for new features
---

# Multi-Agent Workflow Pipeline

To prevent regressions and ensure high-quality code, we now use a pipeline approach leveraging our specialized Agent Skills. When you want to build a new feature (e.g., "Add user roles"), do not ask the agent to just "write the code". Instead, follow this orchestrated pipeline:

## Step 1: The Architect Phase (`spec-crafter`)
**User Command:**
> "Используй скилл spec-crafter. Спроектируй фичу: [ОПИСАНИЕ ФИЧИ]"

**Agent Actions:**
- The agent reads existing data models and UI constraints.
- Generates a new `00X-feature/spec.md` with database designs, API contracts, and Mermaid UML diagrams.
- Generates `00X-feature/tasks.md` to track progress.
- **Wait for User Approval.**

## Step 2: The Test Engineer Phase (`tdd-agent-master`)
**User Command:**
> "Используй скилл tdd-agent-master. Напиши тесты для спецификации 00X."

**Agent Actions:**
- The agent generates Vitest/Supertest files in the `tests/` directory.
- Creates necessary database mocks and fixtures.
- Ensures tests fail appropriately (Red phase).

## Step 3: The Developer Phase (Execution)
**User Command:**
> "Реализуй логику для прохождения тестов спецификации 00X."

**Agent Actions:**
- The agent writes the FastAPI routes in `app/api/endpoints/` and React TSX components in `client/src/features/`.
- If database models are complex, the agent autonomously consults `sqlite-optimizer-pro` to generate optimal indexes for SQLAlchemy.
- Runs `pytest` and `npm run tsc` until all checks pass (Green phase).

## Step 4: The Reviewer Phase (`clean-arch-enforcer` & `doc-master`)
**User Command:**
> "Используй скиллы clean-arch-enforcer и doc-master. Проведи аудит написанного кода."

**Agent Actions:**
- The agent acts as a strict code reviewer.
- Audits the new code against the Constitution, Frontend Codex, and UI/UX Pro Max guidelines.
- Enforces strict TSDoc for React hooks/components and Google Style Docstrings for Python functions.
- Refactors code if necessary until architecture is perfectly documented and clean.

## Step 5: Finalization
**User Command:**
> "Сделай коммит и генерацию walkthrough."
