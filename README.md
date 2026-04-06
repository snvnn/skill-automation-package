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
- `scripts/package_layout.py`: shared package manifest loader and asset copy helpers
- `templates/agents_block.md`: managed block for `AGENTS.md`
- `templates/claude_block.md`: managed block for `CLAUDE.md`
- `scripts/install.py`: installer for another repository
- `scripts/sync_assets.py`: sync packaged assets from the source repository
- `tests/test_package_layout.py`: verification for grouped asset expansion and executable handling

## Architecture Notes

The package is split into two main layers:

- packaging: install and sync the shipped assets into another repository
- runtime: `skill_agent.py` resolves, creates, refreshes, and prunes repo-local skills after installation

The packaging layer is manifest-driven. `package.json` declares three asset groups:

- `managed_assets`: always installed
- `optional_assets`: installed unless `--no-tests` is used
- `executable_assets`: copied assets that should receive executable permissions

Asset entries can point to either a single file or a directory. Directory entries are expanded recursively, which means related assets can now be grouped under one manifest path instead of repeating every file in multiple scripts.

## Extending The Package

### Add or change packaged assets

1. Put the asset under `assets/`.
2. Register it in `package.json` under `managed_assets` or `optional_assets`.
3. If the copied file should be executable, also add the same relative path to `executable_assets`.
4. Run `python3 scripts/sync_assets.py` if the source-of-truth file lives outside `assets/`.
5. Verify the installer with `python3 scripts/install.py --target /tmp/skill-automation-package-dry-run --dry-run`.

Why this is simpler now:

- `scripts/install.py` and `scripts/sync_assets.py` both read the same layout from `scripts/package_layout.py`
- directory assets expand automatically during copy, so adding a new file inside a managed directory usually does not require code changes

### Extend `skill_agent.py`

The CLI parser is now command-spec driven. New subcommands are registered through `build_command_specs()` instead of manually growing `build_parser()`.

Typical flow for a new command:

1. Implement `cmd_<name>(args)`.
2. Add a `CliCommand(...)` entry in `build_command_specs()`.
3. Use `cli_argument(...)` entries for parser arguments, or a dedicated `configure=` function when the command needs more setup.

This keeps parser wiring declarative and makes command additions lower risk because the registration logic lives in one table.

## Maintenance

If you update the source package inside a working repository, resync the packaged assets with:

```bash
python3 scripts/sync_assets.py
```

Then reinstall into a target repository or regenerate the published package commit as needed.

When you need to publish changes from a stale or dirty local checkout, use the documented worktree-based flow in `docs/publish-workflow.md` instead of committing directly on the old checkout.

## Verification

From a repository that contains the package source and packaged tests:

```bash
python3 -m unittest discover -s .claude/tests -p 'test_*.py'
```

From this package repository, you can also run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m unittest discover -s assets/.claude/tests -p 'test_*.py'
python3 scripts/install.py --target /tmp/skill-automation-package-dry-run --dry-run
```

## License

MIT
