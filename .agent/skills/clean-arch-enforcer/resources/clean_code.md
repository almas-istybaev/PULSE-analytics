# Clean Code: A Handbook of Agile Software Craftsmanship (Robert C. Martin)
*Applied to FastAPI & React V2 Stack*

"Clean Code" focuses on readability, simplicity, and maintainability. In our automated linting and architecture reviews, enforce the following core tenets:

## 1. Meaningful Names
*   **Intention-Revealing:** The name of a variable, function, or class, should answer all the big questions. It should tell you why it exists, what it does, and how it is used. If a name requires a comment, then the name does not reveal its intent.
    *   *Bad (React):* `const d = useData();`
    *   *Good (React):* `const { inventoryItems, isLoading } = useInventory();`
*   **Searchable Names:** Avoid single-letter variables except for short loop indices. 
*   **Class Names:** Should be noun or noun phrase like `UserRepository` or `ItemService`. Avoid words like `Manager`, `Processor`, `Data`, or `Info`.
*   **Method Names:** Should have verb or verb phrase names like `postPayment`, `deletePage`, or `save`.

## 2. Functions
*   **Small!** Functions should be small. They should hardly ever be 20 lines long.
*   **Do One Thing:** Functions should do one thing. They should do it well. They should do it only. (SRP at the function level).
    *   *FastAPI Enforcement:* If a route handler is parsing a request, validating complex business logic, calling the database three times, and formatting an email—flag it immediately. Extract the logic into smaller service methods.
*   **Function Arguments:** The ideal number of arguments for a function is zero (niladic). Next comes one (monadic), followed closely by two (dyadic). Three arguments (triadic) should be avoided where possible. Use Pydantic models or configuration objects to group arguments.

## 3. Comments
*   **Comments Do Not Make Up for Bad Code:** Clear and expressive code with few comments is far superior to cluttered, complex code with lots of comments.
*   **Explain Yourself in Code:** Use function and variable names to eliminate the need for explanatory comments.
*   **Good Comments:** Legal comments, informative (regex explanations), warnings of consequences, TODOs.
*   **Bad Comments:** Mumbling, redundant comments, misleading comments, commented-out code (delete it, git tracks history!).

## 4. Error Handling
*   **Use Exceptions Rather Than Return Codes:** In FastAPI, use `HTTPException` or custom Python Exceptions instead of returning error dictionaries (`{"status": "error"}`).
*   **Extract Try/Catch Blocks:** Blocks of code inside `try/except` should be extracted into their own functions.

## 5. Formatting
*   **Vertical Density:** Concepts that are closely related should be kept vertically close to each other.
*   **Vertical Distance:** Variables should be declared as close to their usage as possible.
*   *Enforcement:* Rely on `Ruff`/`Black` for Python formatting and `Prettier` for React mapping. Do not bike-shed on styling, rely on the automated tools, but enforce logical vertical distance.
