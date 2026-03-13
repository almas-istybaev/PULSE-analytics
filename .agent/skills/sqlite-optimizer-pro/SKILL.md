---
name: sqlite-optimizer-pro
description: Advanced database optimization skills for SQLite, focusing on performance, concurrency, and indexing.
---

# SQLite Optimizer Pro

This skill equips the agent with advanced knowledge for optimizing SQLite databases, particularly when handling high concurrency or large datasets (like the Inventory Monitor's PIM and Synchronization modules).

## 1. Concurrency and Resilience
- **WAL Mode**: Ensure `PRAGMA journal_mode=WAL;` is active to allow concurrent readers and single writers without locking the entire database.
- **Busy Timeout**: Always set `PRAGMA busy_timeout = 5000;` (or higher) to handle `SQLITE_BUSY` errors gracefully during concurrent access.
- **Synchronous**: Consider `PRAGMA synchronous=NORMAL;` in WAL mode for a balance between speed and safety.

## 2. Query Optimization
- **EXPLAIN QUERY PLAN**: Before proposing complex `JOIN`s or `WHERE` clauses, the agent should conceptually analyze the query plan to avoid full table scans.
- **Indexing**: 
  - Automatically suggest indexes for foreign keys (e.g., `product_id`).
  - Suggest composite indexes for common multi-column queries (e.g., filtering by `group` and ordering by `price_retail`).
  - Avoid over-indexing, which slows down `INSERT` and `UPDATE` operations (like the Moysklad Sync).

## 3. Data Integrity & Schema
- **STRICT Tables**: Use `CREATE TABLE ... ( ..., ) STRICT;` for new tables to enforce data types at the database level.
- **Foreign Keys**: Ensure `PRAGMA foreign_keys = ON;` is enforced at every connection startup.

## 4. Workflows
When asked to optimize the database:
1. Identify the slowest queries in `inventoryService.js` or `pimService.js`.
2. Propose necessary indexes.
3. Review schema for redundant data.
