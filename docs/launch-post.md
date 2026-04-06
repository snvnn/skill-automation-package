# Launch Post Draft

## Short Version

I packaged the local skill automation setup I have been using for Codex and Claude Code into a standalone repo:

https://github.com/snvnn/skill-automation-package

It installs a repo-local skill resolver, a default routing skill, and managed `AGENTS.md` / `CLAUDE.md` blocks so future agent sessions can reuse or generate skills automatically inside a project.

Install:

```bash
python3 scripts/install.py --target /path/to/repo
```

Then use:

```bash
python3 .claude/tools/skill_agent.py auto "<task>" --json
```

## Longer Version

I wanted a way to make repository-specific skills persist across sessions instead of rebuilding the same workflows every time an agent starts cold.

This package adds that missing layer:

- search existing local skills for a task
- generate a new reusable skill when no strong match exists
- refresh the local registry automatically
- inject guidance into `AGENTS.md` and `CLAUDE.md` so future Codex and Claude Code sessions follow the same path

The package is intentionally simple:

- one install script
- one local skill resolver CLI
- one default routing skill
- optional packaged tests

The goal is not a marketplace. The goal is to make reusable, project-local workflows cheap enough that agents actually keep them up to date.

Repository:

https://github.com/snvnn/skill-automation-package

## Suggested Title

Skill Automation Package: Reusable Repo-Local Skills for Codex and Claude Code
