<!-- SKILL-AUTOMATION:AGENTS:START -->
## Repo Local Skill Automation

For any non-trivial task in this repository, start with:

```bash
python3 .claude/tools/skill_agent.py auto "<task>" --json
```

- If the action is `reuse`, open the matched skill under `.claude/skills/<skill-name>/SKILL.md` and follow it.
- If the action is `created`, use the generated skill immediately. The registry is already refreshed.
- If a step inside the chosen workflow becomes its own repeatable, non-trivial subtask, rerun `python3 .claude/tools/skill_agent.py auto "<sub-task>" --json` for that step, then resume the parent workflow.
- If you want a preview before writing files, run:

```bash
python3 .claude/tools/skill_agent.py auto "<task>" --dry-run --json
```

- Use `suggest`, `search`, `bootstrap`, `create`, and `refresh` only when the default `auto` flow is not enough.
<!-- SKILL-AUTOMATION:AGENTS:END -->
