---
name: project-skill-router
description: Search, rank, scaffold, and refresh repo-local skills inside .claude/skills. Use when an agent should find an existing reusable workflow before coding, or create a new project skill for work that is likely to repeat.
---

# Project Skill Router

## Goal

Reuse the smallest suitable local skill first, and create a new one only when the workflow is reusable and no good match already exists.

## Workflow

1. Start non-trivial work with `python3 .claude/tools/skill_agent.py auto "<task>" --json` so the repo can either reuse an existing skill or generate one immediately.
2. If `auto` returns `reuse`, open that skill's `SKILL.md` and follow it instead of inventing a new workflow.
3. If `auto` returns `created`, use the generated skill right away and refine it only if the task reveals a real gap.
4. If the task is novel and you want inspection before writing files, run `python3 .claude/tools/skill_agent.py auto "<task>" --dry-run --json`.
5. Use `suggest`, `search`, `bootstrap`, or `create` only when you need more control than the default `auto` flow provides.

## Reuse Notes

- Local skills live in `.claude/skills/<skill-name>/`.
- Search by purpose, not only by name; the registry indexes category, tags, triggers, summary, and workflow steps.
- Keep `SKILL.md` concise and procedural. Put structured metadata in the companion `skill.json`, including validation and example requests when available.
- `auto` refreshes the registry after generating a new skill, so future sessions can find it immediately.
- Prefer creating a skill only for repeatable, multi-step workflows. Do not create one-off skills for a single narrow edit.
