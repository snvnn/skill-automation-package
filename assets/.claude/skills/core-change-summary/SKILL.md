---
name: core-change-summary
description: Summarize the current working tree or recent changes in a read-only way. Use when an agent needs fast change context without editing the repo.
---

# Core Change Summary

## Goal

Build a concise summary of what changed, where it changed, and what still looks important before deeper review or follow-up work.

## Workflow

1. Inspect the current working tree, changed files, and the smallest relevant diff or file set.
2. Group changes by area, intent, or likely effect instead of listing raw filenames only.
3. Call out obvious risks, open questions, or verification gaps that follow from the observed changes.
4. Keep the output read-only and limited to summary, not repo modification.

## Guardrails

- Do not create, edit, or delete repository files.
- Do not infer intent that is not supported by the observed changes.
- Prefer a compact status summary over a file-by-file changelog.
