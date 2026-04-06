---
name: core-repo-structure-analysis
description: Map the repository layout, key entrypoints, and likely edit locations in a read-only way. Use when an agent needs to understand where code, docs, tests, or config live without changing the repo.
---

# Core Repo Structure Analysis

## Goal

Create a compact map of the repository layout so an agent can find the right area before making changes.

## Workflow

1. Inspect the top-level directories, manifests, and obvious entrypoint files before drawing conclusions.
2. Group the repository into major areas such as application code, tests, docs, scripts, tooling, or generated assets.
3. Explain which directories are likely to matter for the current task and why.
4. Keep the analysis read-only and limit the output to navigation guidance rather than implementation advice.

## Guardrails

- Do not create, edit, or delete repository files.
- Do not claim a directory is authoritative unless the repository structure supports that conclusion.
- Prefer a practical map of likely edit locations over a full file inventory.
