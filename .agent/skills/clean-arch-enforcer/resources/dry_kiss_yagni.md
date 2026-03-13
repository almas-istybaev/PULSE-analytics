# DRY, KISS, and YAGNI Principles

These three foundational principles act as a defense against chaotic, bloated, or overly complex codebases.

## 1. DRY (Don't Repeat Yourself)
**Definition:** Every piece of knowledge must have a single, unambiguous, authoritative representation within a system.

*   **Rule of Three:** If you write the same code three times, it's time to extract it into a reusable function, component, or module.
*   **FastAPI:** 
    *   Extract common validation logic into custom Pydantic validators.
    *   Extract common query filters into SQLAlchemy utility functions.
    *   Use FastAPI `Depends()` for shared logic (e.g., pagination parameters, standard authentication checks).
*   **React:**
    *   Extract duplicated UI patterns into reusable components (e.g., a standard `Card` or `Modal`).
    *   Extract duplicated state logic or side-effects into Custom Hooks (e.g., `useLocalStorage`, `useDebounce`).
    *   Centralize API endpoint URLs and base configurations instead of hardcoding them in every `fetch` call.

## 2. KISS (Keep It Simple, Stupid)
**Definition:** Most systems work best if they are kept simple rather than made complicated. Simplicity should be a key goal in design, and unnecessary complexity should be avoided.

*   **Avoid Over-Engineering:** Do not implement a complex microservices architecture, event bus, or Redux state container if a monolithic API and React Context can solve the problem elegantly and efficiently for the current scale.
*   **Readability First:** Clever, one-line code golf solutions are harder to maintain than verbose, explicitly named standard logic. Optimize for the developer reading the code 6 months from now.
*   **FastAPI:** Stick to clear, synchronous-looking async routes. Avoid deeply nested decorators unless strictly necessary.
*   **React:** If local state (`useState`) works perfectly for a single form, do not force it into a global state manager (Zustand/Context). 

## 3. YAGNI (You Aren't Gonna Need It)
**Definition:** Always implement things when you actually need them, never when you just foresee that you need them.

*   **Context:** Developers often build generic abstractions anticipating future use cases that never materialize, leading to dead code and rigid architectures.
*   **Action:** Build only what is required to satisfy the immediate feature specifications (SDD).
*   **Example (Backend):** Don't build a complex caching layer with Redis until performance metrics actively demand it.
*   **Example (Frontend):** Don't build a highly configurable, multi-step wizard component framework if the current spec only asks for a simple 2-step form. Build the simple form first, refactor later if a third or fourth form appears.
