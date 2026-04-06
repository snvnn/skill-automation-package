# Skill Automation Package

Portable repo-local skill automation for Codex and Claude Code.

## Why This Exists

Most agent sessions can search local files, but they do not automatically build a reusable skill system for the repository they are working in. This package adds that layer.

After installation, an agent can:

- search for the best existing local skill for a task
- generate a new reusable skill when no strong match exists
- refresh the local skill registry automatically
- track reuse frequency for each local skill
- archive low-value skills that stay unused long enough to become cleanup candidates
- route future Codex and Claude Code sessions through the same workflow

## What It Installs

- `.claude/tools/skill_agent.py`
- `.claude/skills/project-skill-router/`
- optional `.claude/tests/test_skill_agent.py`
- managed automation blocks for `AGENTS.md` and `CLAUDE.md`

## Quick Start

Install into another repository:

```bash
python3 scripts/install.py --target /path/to/target-repo
```

Then, inside the target repository, start non-trivial work with:

```bash
python3 .claude/tools/skill_agent.py auto "<task>" --json
```

If you want a preview before writing files:

```bash
python3 .claude/tools/skill_agent.py auto "<task>" --dry-run --json
```

## Installed Agent Flow

- `reuse`: open the matched local skill and follow it
- `created`: use the generated skill immediately
- `preview-create`: rerun without `--dry-run` to persist the generated skill

Check reuse health:

```bash
python3 .claude/tools/skill_agent.py usage
```

Review stale or underspecified skills before patching them:

```bash
python3 .claude/tools/skill_agent.py review
```

Apply the safe metadata refreshes for the current candidates:

```bash
python3 .claude/tools/skill_agent.py update --apply
```

Preview cleanup candidates:

```bash
python3 .claude/tools/skill_agent.py prune
```

Archive the current candidates:

```bash
python3 .claude/tools/skill_agent.py prune --apply
```

## Install Options

Preview without writing files:

```bash
python3 scripts/install.py --target /path/to/target-repo --dry-run
```

Skip the packaged test file:

```bash
python3 scripts/install.py --target /path/to/target-repo --no-tests
```

Do not update `AGENTS.md`:

```bash
python3 scripts/install.py --target /path/to/target-repo --skip-agents
```

Do not update `CLAUDE.md`:

```bash
python3 scripts/install.py --target /path/to/target-repo --skip-claude
```

## Package Layout

- `assets/.claude/tools/skill_agent.py`: resolver, search, scaffold, usage tracking, refresh review/update, and prune CLI
- `assets/.claude/skills/project-skill-router/`: default reusable routing skill
- `templates/agents_block.md`: managed block for `AGENTS.md`
- `templates/claude_block.md`: managed block for `CLAUDE.md`
- `scripts/install.py`: installer for another repository
- `scripts/sync_assets.py`: sync packaged assets from the source repository

## Maintenance

If you update the source package inside a working repository, resync the packaged assets with:

```bash
python3 scripts/sync_assets.py
```

Then reinstall into a target repository or regenerate the published package commit as needed.

## Verification

From a repository that contains the package source and packaged tests:

```bash
python3 -m unittest discover -s .claude/tests -p 'test_*.py'
```

## License

MIT
