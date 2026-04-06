<!-- SKILL-AUTOMATION:CLAUDE:START -->
## Local Skill Automation

- Store repo-local skills under `.claude/skills/<skill-name>/`.
- For any non-trivial task, start with `python3 .claude/tools/skill_agent.py auto "<task>" --json`.
- If `auto` returns `reuse`, open the matched skill and follow it.
- If `auto` returns `created`, use the generated skill immediately. The registry is updated automatically.
- If a step inside the current workflow becomes its own repeatable, non-trivial subtask, rerun `python3 .claude/tools/skill_agent.py auto "<sub-task>" --json` for that step before expanding the parent flow manually.
- To preview a generated skill before writing files, use `python3 .claude/tools/skill_agent.py auto "<task>" --dry-run --json`.
- Use `suggest`, `search`, `bootstrap`, `create`, and `refresh` only when the default `auto` flow is not enough.
<!-- SKILL-AUTOMATION:CLAUDE:END -->
