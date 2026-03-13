# Grokking Algorithms (Aditya Bhargava)
*Applied to FastAPI & React V2 Stack*

"Grokking Algorithms" explains fundamental algorithmic thinking in a visual and approachable style. These concepts directly impact the performance and correctness of inventory-critical sections of our application.

## 1. Binary Search
*   **Concept:** For a sorted list of `n` elements, binary search takes at most `log₂(n)` steps, whereas simple search takes at most `n` steps.
*   **Application:** Avoid linear scans in data-heavy contexts. If you are searching through a sorted list of 1 million inventory SKUs, binary search is ~20 steps vs. ~1,000,000. 
*   **In our Stack:** Always leverage **indexed database columns** in SQLite. The database query planner uses binary search (B-tree index) to find rows. This is why creating indexes on frequently queried columns like `sku`, `username`, `code` is non-negotiable.

## 2. Big O Notation (Thinking About Performance)
*   **O(1)** — Constant time. Best case. E.g., dict/set lookup in Python, primary key lookup in SQLite.
*   **O(log n)** — Logarithmic. E.g., Binary search, indexed DB queries.
*   **O(n)** — Linear time. E.g., Iterating through a list.
*   **O(n log n)** — Linearithmic. E.g., Efficient sorting algorithms (`sort`).
*   **O(n²)** — Quadratic. **Red Flag.** E.g., Nested loops over a collection. If spotted in code reviews, demand a refactor.
*   **Enforcement Rule:** When reviewing service-layer Python code operating on large collections (inventory items, sync operations), flag any nested loops or multiple sequential scans as a potential O(n²) or O(n³) problem.

## 3. Arrays vs. Linked Lists (→ Why Database Indexes Matter)
*   **Arrays (Lists in Python):** Elements are contiguous in memory. Random access O(1). Insert/delete at start O(n).
*   **Linked Lists:** Insert/delete O(1) with pointer. Random access O(n).
*   **Practical Takeaway:** Python `list` is an array. Use it for ordered collections where index access matters. For building a queue of tasks (background jobs with APScheduler), Python `collections.deque` or a job queue (Redis) is more efficient than repeatedly inserting/removing from the front of a list.

## 4. Selection Sort, Quicksort (→ Use Python Built-ins)
*   **Concept:** Never write your own sort in application code. Use `list.sort()` (Timsort, O(n log n)) or `.order_by()` in SQLAlchemy which delegates to the database sort algorithm.
*   **Enforcement Rule:** Flag any manual bubble sort or selection sort implementations immediately as an anti-pattern. The language and database internals always provide superior, optimized implementations.

## 5. Recursion and the Call Stack
*   **Risk:** Unbounded recursion in Python leads to `RecursionError` (default stack limit ~1000 frames).
*   **Practical Rule:** If a recursive function is used in the codebase (e.g., traversing a tree of categories), ensure it has a clear base case and is bounded by the data size in the real world. For very deep recursion, prefer an iterative approach using an explicit stack.

## 6. Hash Tables (Python Dicts → FastAPI Caches)
*   **Concept:** Hash tables offer O(1) average-case lookup, insert, and delete. They are the most powerful data structure for lookups.
*   **Application:**
    *   **In-Memory Caching:** For frequently read, rarely written data (e.g., product categories, config lookups), use a Python `dict` or `functools.lru_cache` as an in-memory cache within the FastAPI process to avoid repeated database queries.
    *   **Python Sets:** For "does this item exist?" type checks, use a `set` (backed by a hash table) instead of a `list` for O(1) vs. O(n) performance.

## 7. Breadth-First Search (BFS) and Graphs
*   **Concept:** BFS finds the shortest path in an unweighted graph.
*   **Application:** Relevant if inventory data has hierarchical/dependency structures (e.g., product categories, warehouse dependencies). BFS can traverse a category tree level by level.
*   **Rule:** If a feature requires traversing graph-like data (parent-child relationships in a tree), use a proper BFS/DFS algorithm rather than manual, ad-hoc recursive queries.
