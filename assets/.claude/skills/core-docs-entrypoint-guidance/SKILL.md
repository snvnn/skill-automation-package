---
name: core-docs-entrypoint-guidance
description: Identify the best documentation entrypoints and reading order in a read-only way. Use when an agent needs to find canonical docs without changing the repo.
---

# Core Docs Entrypoint Guidance

## Goal

Point an agent to the smallest set of documents worth reading first and distinguish active references from lower-priority material.

## Workflow

1. Inspect the root `README.md`, `docs/` tree, and any obvious operations or reference directories.
2. Separate canonical docs from working notes, archives, examples, or historical records.
3. Recommend a practical reading order for the current task.
4. Keep the output read-only and focused on navigation, not documentation edits.

## Guardrails

- Do not create, edit, or delete repository files.
- Do not treat archived or draft material as current truth unless the repo says so.
- Prefer a short ordered list of entrypoints over a broad document dump.
