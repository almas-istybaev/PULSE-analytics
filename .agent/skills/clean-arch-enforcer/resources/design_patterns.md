# Design Patterns in Modern Web Development (FastAPI & React)

Design patterns are typical solutions to commonly occurring problems in software design. In the context of our V2 stack, specific patterns are highly recommended.

## 1. Architectural Patterns

### The Repository Pattern (Backend)
*   **Purpose:** To isolate the data access layer (SQLAlchemy) from the business logic layer (Services).
*   **Implementation:** 
    *   Create a repository class (e.g., `ItemRepository`) that handles `db.query(Item)...` operations.
    *   Services call the repository (e.g., `item_repo.get_by_id(db, item_id)`).
    *   **Benefit:** Keeps Services clean, allows swapping ORMs (rare but possible), and makes mocking the database in unit tests significantly easier.

### Component-Based Architecture (Frontend)
*   **Purpose:** To build UIs from encapsulated components that manage their own state.
*   **Implementation:** React enforces this natively. Break UIs down into Presentational Components (dumb, UI only) and Container Components (smart, handle data fetching via React Query).

## 2. Creational Patterns

### The Factory Pattern (Backend)
*   **Purpose:** Provides an interface for creating objects in a superclass, but allows subclasses to alter the type of objects that will be created.
*   **Implementation in FastAPI:** Often used when creating different types of Pydantic response models dynamically based on input, or initializing different third-party service clients based on environment variables.

### Singleton Pattern
*   **Purpose:** Ensure a class has only one instance, and provide a global point of access to it.
*   **Implementation:** 
    *   **FastAPI:** The database `engine` and connection pools are singletons. Dependency injection `Depends()` often handles singleton-like lifecycles per request.
    *   **React:** `React Query`'s `QueryClient` acts as a singleton cache for the application.

## 3. Structural Patterns

### The Decorator Pattern (Backend & Frontend)
*   **Purpose:** Attach new behaviors to objects by placing these objects inside special wrapper objects that contain the behaviors.
*   **Implementation in FastAPI:** `Depends()` acts as a structural decorator for routes (e.g., attaching authentication or database sessions dynamically). Python's `@` decorators are heavily used for defining routes (`@app.get()`).
*   **Implementation in React:** Historically solved by Higher-Order Components (HOCs). In modern React, this is mostly replaced by **Custom Hooks**, which decorate functional components with additional state or side-effects.

### The Adapter Pattern (Frontend)
*   **Purpose:** Allows objects with incompatible interfaces to collaborate.
*   **Implementation:** When consuming third-party APIs (like MoySklad) with complex or legacy data structures, create an "Adapter" function on the frontend that transforms the raw API response into the clean, specific data structure your React components expect.

## 4. Behavioral Patterns

### The Observer/Pub-Sub Pattern
*   **Purpose:** Defines a subscription mechanism to notify multiple objects about any events that happen to the object they're observing.
*   **Implementation:**
    *   **React:** The Context API inherently acts as an observable pattern. Components subscribe to a Context and re-render when its value changes. `React Query` acts as an observer for server state.
    *   **Backend:** Can be used with message brokers (RabbitMQ, Redis Pub/Sub) for async background tasks (e.g., notifying MoySklad when local inventory updates).
