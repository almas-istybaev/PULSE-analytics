# The Pragmatic Programmer (Andrew Hunt, David Thomas)
*Applied to FastAPI & React V2 Stack*

"The Pragmatic Programmer" focuses on the attitude, style, and philosophy of effective developers.

## 1. Orthogonality
*   **Definition:** "Eliminate Effects Between Unrelated Things." If you change one module, it shouldn't break an unrelated module.
*   **Application in our Stack:**
    *   Changing the UI layout of the React dashboard should require **zero** changes to the FastAPI backend.
    *   Swapping out SQLite for PostgreSQL should require **zero** changes to the FastAPI `routers/` or `services/` layers—only the database connection and potentially some SQLAlchemy specific adjustments in `repositories/`.

## 2. DRY (Don't Repeat Yourself)
*   *Already covered in `dry_kiss_yagni.md`, but emphasized strongly here as a philosophical stance against knowledge duplication in documentation vs code.* 
*   **Code generators:** Use them to stay DRY. E.g., OpenAPI schemas automatically generating TypeScript types for the React frontend, so interfaces are never out of sync.

## 3. Tracer Bullets
*   **Concept:** Build a minimal, end-to-end working implementation of a feature first to prove the architecture, then flesh it out.
*   **SDD Integration:** Implement a "walking skeleton" of a Spec first. (e.g., Database Model -> Simple Route -> Simple React component rendering raw JSON). Ensure the pipeline works before polishing the Tailwind UI or adding complex validation.

## 4. Exceptions vs. Errors
*   **Rule:** Use exceptions for exceptional problems.
*   *FastAPI Approach:* If an item being searched for is not found, should it throw an Exception or return `None`? If fetching an item by ID from a direct URL is expected to succeed, raise a 404 Exception. If searching for items returns nothing, returning an empty list `[]` is normal, not an exception.

## 5. Decoupling and the Law of Demeter
*   **Rule:** "Don't talk to strangers." Modules shouldn't reach deeply into other modules' data structures.
*   *Python Example:* `order.customer.address.zipcode` is a violation. The code is tightly coupled to the exact nested structure. Instead, the `Order` class should expose a method `order.get_customer_zipcode()`.
*   *React Example:* Avoid "Prop Drilling". Passing props down 5 levels of components couples all intermediate components to data they don't care about. Use Context API or global state (Zustand) instead.

## 6. Broken Windows Theory
*   **Rule:** Don't live with broken windows. Fix bad designs, wrong decisions, and poor code when you see them.
*   **Enforcer Duty:** If an agent spots a legacy Vanilla JavaScript file or an Express.js remnant in the V2 codebase, flag it for immediate refactoring or deletion. Do not let bad architecture rot the new foundation.
