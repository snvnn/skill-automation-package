---
name: core-project-summary
description: Produce a read-only summary of the repository's purpose, main components, and current constraints. Use when an agent needs fast onboarding context without changing the repo.
---

# Core Project Summary

## Goal

Build a short, source-grounded summary of what the repository does and what matters before deeper work.

## Workflow

1. Read the root `README.md`, top-level manifests, and the most relevant entry directories before summarizing.
2. Identify the repository purpose, main subsystems, runtime or build stack, and current constraints from existing files only.
3. Keep the output read-only: summarize what exists, cite the files you used, and do not create or modify repository files.
4. End with the smallest set of next files or directories worth reading for the current task.

## Guardrails

- Do not create, edit, or delete repository files.
- Do not invent architecture, roadmap, or ownership details that are not supported by source material.
- Prefer a short orientation summary over a long document.
