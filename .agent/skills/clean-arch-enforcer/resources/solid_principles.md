# SOLID Principles (FastAPI & React Context)

The SOLID principles are five design rules intended to make software designs more understandable, flexible, and maintainable.

## 1. Single Responsibility Principle (SRP)
**Definition:** A class/module/component should have one, and only one, reason to change.

**FastAPI Implementation:**
*   **Routers:** Only handle HTTP request/response parsing and basic Pydantic validation. They do NOT contain business logic.
*   **Services:** Handle core business logic. They do NOT know about HTTP status codes.
*   **Repositories:** Handle all database interactions (SQLAlchemy). Services call Repositories.

**React Implementation:**
*   **Presentational Components:** Only render UI based on props. They don't fetch data.
*   **Container Components (or Custom Hooks):** Handle data fetching (`React Query`), state management, and pass data down as props.
*   **God Components:** Avoid creating massive components that handle API calls, complex local state, and hundreds of lines of JSX. Break them down.

## 2. Open/Closed Principle (OCP)
**Definition:** Software entities should be open for extension but closed for modification.

**FastAPI Implementation:**
*   Use standard Object-Oriented polymorphism or Protocol classes in Python. 
*   Instead of modifying a giant `if/elif` block to add a new payment gateway, create a base `PaymentGateway` interface and implement new classes for each provider.

**React Implementation:**
*   Use **Component Composition** (`children` prop).
*   Use High-Order Components (HOCs) or wrap extending logic inside Custom Hooks rather than adding more and more boolean flags (`isPremium`, `isGuest`, etc.) to a single component's props to change its behavior.

## 3. Liskov Substitution Principle (LSP)
**Definition:** Subtypes must be substitutable for their base types without altering the correctness of the program.

**FastAPI Implementation:**
*   If a function expects a `BaseRepository`, any subclass (e.g., `UserRepository`, `ItemRepository`) should work seamlessly without the function needing to know the exact subclass.
*   Return types and exceptions raised by overridden methods must match the parent class signature.

**React Implementation:**
*   A custom `Button` component should accept all standard HTML `<button>` attributes (using `...rest` spread operator) so it can act as a drop-in replacement anywhere a standard button is used.

## 4. Interface Segregation Principle (ISP)
**Definition:** Clients should not be forced to depend upon interfaces that they do not use.

**FastAPI Implementation:**
*   Create distinct, focused **Pydantic Models** for different operations (e.g., `UserCreate`, `UserRead`, `UserUpdate`). Don't force a single massive `User` model to handle every possible API payload.

**React Implementation:**
*   Instead of passing a massive `user` object to an `Avatar` component that only needs the `avatarUrl` property, pass just `avatarUrl` as a prop. This makes the component more reusable and less brittle.

## 5. Dependency Inversion Principle (DIP)
**Definition:** High-level modules should not depend on low-level modules. Both should depend on abstractions.

**FastAPI Implementation:**
*   Heavily utilize **FastAPI's Dependency Injection system (`Depends()`)**.
*   Instead of instantiating a database connection directly inside a route, inject it: `def read_users(db: Session = Depends(get_db))`.

**React Implementation:**
*   UI components shouldn't directly instantiate `fetch` or `axios` calls.
*   Inject data-fetching logic via **Custom Hooks** (e.g., `const { data } = useUsers()`) or provide global services via the **Context API**.
