---
name: clean-arch-enforcer
description: Strictly enforces the project's Constitution, Frontend Codex, and overarching software design principles (SOLID, DRY, KISS) for the V2 FastAPI + React stack. Operates as an automated architectural linter and SDD enforcer.
---

# Clean Architecture Enforcer (V2: FastAPI + React + SDD)

This skill transforms the agent into a strict reviewer that enforces the `constitution.md`, `frontend-codex.md`, Spec-Driven Development (SDD) principles, and fundamental software design patterns (SOLID, DRY, KISS).

## 1. Core Software Design Principles Enforcement
For a deep dive into how these principles apply to our specific stack, **you MUST read the relevant local resources before enforcing any rule**:

| Resource | Contents |
|---|---|
| `resources/solid_principles.md` | SOLID principles (SRP, OCP, LSP, ISP, DIP) with FastAPI & React examples |
| `resources/dry_kiss_yagni.md` | DRY, KISS, YAGNI — anti-complexity principles |
| `resources/design_patterns.md` | Repository, Factory, Decorator, Observer, and other key patterns |
| `resources/clean_code.md` | Robert C. Martin — Naming, Functions, Error Handling, Formatting rules |
| `resources/code_complete.md` | Steve McConnell — Cohesion, Defensive Programming, Guard Clauses |
| `resources/pragmatic_programmer.md` | Hunt & Thomas — Orthogonality, Tracer Bullets, Broken Windows, Law of Demeter |
| `resources/grokking_algorithms.md` | Abhargava — Big O, Hash Tables, Search & Sort performance rules |

- **SOLID Principles**:
  - **Single Responsibility (SRP)**: Reject components or functions that do too much. A FastAPI endpoint simply routes data; a service processes logic; a React component renders UI or manages one specific piece of state.
  - **Open/Closed (OCP)**: Code should be open for extension but closed for modification. Enforce the use of React composition (`children`, render props) and FastAPI class inheritance/protocol extensions over endless `if/else` chains.
  - **Liskov Substitution (LSP)**: Ensure that subclass overrides in Python models/services gracefully map to parent definitions.
  - **Interface Segregation (ISP)**: Ensure that React components do not receive massive props objects when they only need one or two scalar values. Enforce granular Pydantic models.
  - **Dependency Inversion (DIP)**: Highly enforce dependency injection. In FastAPI, this means utilizing `Depends()` extensively instead of hardcoding service classes. In React, use Custom Hooks and the Context API rather than coupling UI components directly to fetch logic.
- **DRY (Don't Repeat Yourself)**: Flag copy-pasted logic. Enforce extraction of reusable React Custom Hooks and FastAPI utility dependencies.
- **KISS (Keep It Simple, Stupid)**: Actively push back against over-engineering. If a standard FastAPI routing pattern or a simple React `useState` solves the problem elegantly, reject convoluted architectures (e.g., unnecessary Redux usage, premature microservices).

## 2. Spec-Driven Development (SDD) Enforcement
- **Specification First**: Reject PRs or large code changes that do not correspond to an approved specification in the `.specify/specs/` directory.
- **Single Source of Truth**: Ensure that API changes or database schema modifications are first reflected in the specifications or OpenAPI docs before being implemented in code.
- **TDD Compliance**: Ensure that unit tests (`pytest`) are written and linked to the specifications *before* or *during* the implementation phase.

## 3. Backend Rules Enforcement (FastAPI / Python)
- **Layered Architecture (SRP)**: Reject code where routing logic leaks into business services, or database logic leaks into routers. 
  - `routers/` — purely for HTTP handling and Pydantic schema validation.
  - `services/` — pure business logic.
  - `repositories/` — strictly SQLAlchemy Database interactions.
  - `models/` — SQLAlchemy ORM definitions.
- **Strict Data Validation**: Ensure all incoming and outgoing API traffic is strictly typed and validated using **Pydantic models**.
- **DevSecOps First**: Ensure JWT authentication and Role-Based Access Control (RBAC) are verified via FastAPI dependencies (`Depends()`) on all protected routes.
- **Design Patterns**: Favor the **Repository Pattern** for database access to abstract SQLAlchemy logic away from Services. Use the **Factory Pattern** for generating complex Pydantic response objects.

## 4. Frontend Rules Enforcement (React / Vite / Tailwind)
> Read `../ui-ux-pro-max/resources/component_based_architecture.md` before reviewing any React code.

- **Atomic Design:** Enforce a clear component hierarchy — Atoms (`ui/`), Molecules (`common/`), Organisms (`features/`), Pages. Reject "God Components" that do multiple unrelated things.
- **Smart vs. Dumb:** Presentational components must NOT fetch data. Data fetching belongs in Pages or Custom Hooks.
- **Custom Hooks (DRY):** If the same `useQuery` or `useEffect` logic appears in 2+ components, extract it into a shared Custom Hook.
- **Modern React Paradigms**: Enforce the use of React Functional Components and Hooks. Reject Class components.
- **Server State vs Client State**: 
  - **Server State**: Must use `React Query` (`@tanstack/react-query`) for data fetching, caching, and background synchronization. Reject raw `useEffect` fetches (adhering to DIP/SRP).
  - **Client State**: Keep local state minimal (e.g., `useState`, `Zustand`, or Context API).
- **Mobile-First PWA Design**: Validate adherence to the `frontend-codex.md`. Ensure features are designed as "Smart Cards" over dense data tables. Evaluate Tap Targets (`min-h-[48px]`).
- **Utility-First Styling**: All styling must use Tailwind CSS. Custom CSS is highly discouraged.

## 5. Usage
When asked to "audit the codebase", "enforce architecture", or handle a PR review:
1. Cross-reference the changes with active specifications in the `.specify/specs/` directory.
2. Review the latest changes against `frontend-codex.md` and `constitution.md`.
3. Check code against **SOLID, DRY, and KISS** principles. Highlight violations like massive "God components" or tightly coupled business logic.
4. Refuse to merge or implement code that bypasses Pydantic validation, JWT security layers, or writes custom CSS instead of Tailwind.
