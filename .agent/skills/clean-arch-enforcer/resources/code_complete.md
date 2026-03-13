# Code Complete: A Practical Handbook of Software Construction (Steve McConnell)
*Applied to FastAPI & React V2 Stack*

"Code Complete" bridges the gap between high-level architecture and low-level coding. It emphasizes software construction as a primary discipline.

## 1. Design in Construction
*   **Software's Primary Technical Imperative:** Managing complexity. The most critical goal in software construction is minimizing inherent complexity.
*   **Information Hiding:** The foundation of object-oriented design. Expose only what is strictly necessary.
    *   *FastAPI:* Do not return raw database models to the client. Always mask them through Pydantic `response_model` schemas to hide internal ID structures, passwords, or soft-deleted flags.
    *   *React:* A generic `<DataTable />` component should not know about "Users" or "Orders". It should only know about "columns" and "rows". Data fetching and domain mapping is hidden in the parent component.

## 2. High-Quality Routines (Functions)
*   **Cohesion:** A routine must have strong cohesion—it should contain operations that are closely related. If a FastAPI service method is named `calculate_tax_and_send_email()`, it has weak, un-cohesive coupling. Break it into `calculate_tax()` and `send_notification()`.
*   **Defensive Programming:** Protect your programs from invalid inputs.
    *   *FastAPI Implementation:* Pydantic handles the first layer, but business constraints (e.g., "Cannot deduct more stock than available") must be defensively checked in the `services/` layer early, before database transactions begin.

## 3. Working with Variables
*   **Initialization:** Initialize variables as they are declared. Define variables close to where they are first used.
*   **Scope:** Keep the scope of variables as small as possible. Avoid global variables entirely.
*   **Magic Numbers:** Avoid "magic numbers" (e.g., `if state == 4`). Use Enums locally or in the database. In Python, use `enum.Enum`.

## 4. Statements and Logic
*   **Straight-Line Code:** Make dependencies obvious through naming and parameters.
*   **If-Statements:** Write the nominal (normal) path first, handle the errors/exceptions in the `else` or as early return guard clauses.
*   **Guard Clauses (Bouncer Pattern):** Avoid deep nesting (Arrow Anti-Pattern). Return early on failure.
    *   *React Example:* `if (isLoading) return <Spinner />; if (error) return <Error />; return <Data />;` instead of massive nested ternary operators.

## 5. Construction Practices
*   **Refactoring:** It is not an isolated phase; it is a continuous activity during construction.
*   **Code Review:** Reading other people's code is one of the most effective ways to catch bugs. As an agent, your role is to ruthlessly but constructively point out violations of these principles.
