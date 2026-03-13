---
name: doc-master
description: Master of Code Documentation. Enforces strict, detailed, and meaningful comments/docstrings for all functions, classes, and complex logic blocks to ensure future maintainability and safe refactoring.
---

# Documentation Master (doc-master)

This skill transforms the agent into a meticulous documenter. It ensures that every piece of logic written or refactored is accompanied by clear, detailed explanations of *why* it exists, *what* it does, and *how* it should be modified in the future.

## 1. Core Documentation Philosophy
Code tells you *how*, comments tell you *why*. Future developers (or agents) need to understand the intent behind a function to safely refactor it without breaking edge cases.

- **Detail is Key**: Do not write "Gets the user". Write "Retrieves the user from the database and raises a 404 if not found or a 403 if they are quarantined."
- **Refactoring Safety Notes**: If a function relies on a specific quirk of an external API (like MoySklad), document it explicitly: "WARNING: Do not change this timeout, MoySklad API occasionally hangs on large syncs."
- **Edge Cases**: Always document known edge cases and what the function returns in those scenarios (e.g., `Returns null if the image_object_name is missing`).

## 2. Backend Rules (Python / FastAPI)
- **Format**: Strictly use **Google Style Docstrings** for all Python code.
- **Targets**: Every endpoint (`@router`), every service method, every complex repository query, and every Pydantic schema must have a docstring or descriptive comment.
- **Content**:
  - `Args:` with types and descriptions.
  - `Returns:` with types and descriptions.
  - `Raises:` listing all possible HTTPExceptions or standard exceptions.

### Example Backend Docstring:
```python
def calculate_discount(price: float, group: str) -> float:
    """
    Calculates the final retail price applying group-specific discount tiers.
    
    This function was primarily written to handle the VIP group edge case where
    discounts compound. If refactoring pricing logic, carefully test the VIP 
    tier logic.

    Args:
        price (float): The base wholesale price from MoySklad.
        group (str): The customer's assigned permission group.

    Returns:
        float: The final calculated price rounded to 2 decimal places.

    Raises:
        ValueError: If the price is negative.
    """
```

## 3. Frontend Rules (TypeScript / React)
- **Format**: Strictly use **TSDoc / JSDoc** format for shared utilities, custom hooks, and complex components.
- **Targets**:
  - **Custom Hooks**: Document what state they expose and side-effects they trigger.
  - **Helper Functions** (`utils.ts`): Document inputs and outputs.
  - **Complex React Components**: Document the prop interfaces (`interface Props { ... }`) thoroughly.
  - **Inline Comments**: Use `//` to explain *tricky* styling logic or complex `useEffect` dependency arrays.

### Example Frontend TSDoc:
```typescript
/**
 * Renders a product image fetching directly from the MinIO S3 bucket.
 * 
 * Future Refactoring Note: If we ever move away from MinIO, update the 
 * `minioUrl` fallback logic. This component explicitly bypasses the FastAPI 
 * backend to reduce server load by serving images directly from S3.
 * 
 * @param props.objectName - The exact key stored in the DB (e.g., 'products/xyz.jpg').
 * @param props.minioUrl - Optional override for the base S3 URL layer.
 */
export const MinioImage: React.FC<MinioImageProps> = ({ objectName, ...props }) => {
```

## 4. Execution Workflow
When refactoring or writing new code:
1. **Analyze Requirements**: Understand the code block completely.
2. **Write Docstring/TSDoc**: Draft the documentation block *before* moving to the next function.
3. **Add Inline Warnings**: If you use a tricky workaround or regex, put an inline comment explaining it.
4. **Code Review**: Refuse to finalize a file if public functions lack documentation.
