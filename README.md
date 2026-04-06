# Skill Automation Package

Portable repo-local skill automation for Codex and Claude Code.

## What It Installs

- `.claude/tools/skill_agent.py`
- `.claude/skills/project-skill-router/`
- optional `.claude/tests/test_skill_agent.py`
- managed automation blocks for `AGENTS.md` and `CLAUDE.md`

## What It Does

- resolves the best existing local skill for a task
- generates a new reusable skill when no strong match exists
- refreshes the local skill registry automatically
- injects default guidance so future Codex and Claude Code sessions use the same flow

## Install Into Another Repository

```bash
python3 scripts/install.py --target /path/to/target-repo
```

Preview without writing files:

```bash
python3 scripts/install.py --target /path/to/target-repo --dry-run
```

Skip the packaged test file:

```bash
python3 scripts/install.py --target /path/to/target-repo --no-tests
```

## Installed Agent Flow

For non-trivial work in the target repository:

```bash
python3 .claude/tools/skill_agent.py auto "<task>" --json
```

- `reuse`: open the matched local skill and follow it
- `created`: use the generated skill immediately
- `preview-create`: rerun without `--dry-run` to persist the generated skill

## Maintenance

If you update the source package inside a working repository, resync the packaged assets with:

```bash
python3 scripts/sync_assets.py
```

## Verification

From a repository that contains the package source:

```bash
python3 -m unittest discover -s .claude/tests -p 'test_*.py'
```

## License

MIT
