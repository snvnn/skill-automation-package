# Skill Automation Package

Portable repo-local skill automation for Codex and Claude Code.

This repository ships a Python-installed automation bundle. It is not an npm runtime package; `package.json` is used here as a package manifest for managed assets, versioning, and install metadata.

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

Or use the npm wrapper entrypoint:

```bash
npx skill-automation-package install --target /path/to/target-repo
```

To update an existing target without forcing an unnecessary reinstall when it is already current:

```bash
npx skill-automation-package update --target /path/to/target-repo
```

The npm entrypoint is a thin wrapper around the Python installer. It does not replace the Python core, and Python 3.10 or newer is still required.
If you already have this repository checked out locally, the direct `python3 scripts/install.py ...` path remains fully supported.
`install` always allows reinstall. `update` is version-aware and only reinstalls when the target reports an older installed version.
Before reinstalling, the wrapper checks `.claude/skill-automation-package.json` in the target repo and reports whether the target is not installed, already at the current version, or behind the current package version.

The installer copies the packaged assets, updates managed blocks in `AGENTS.md` and `CLAUDE.md` unless skipped, writes `.claude/skill-automation-package.json`, and refreshes `.claude/skills/registry.json`.

Then, inside the target repository, start non-trivial work with:

```bash
python3 .claude/tools/skill_agent.py auto "<task>" --json
```

If you want a preview before writing files:

```bash
python3 .claude/tools/skill_agent.py auto "<task>" --dry-run --json
```

## Example Outcomes

Representative `auto` outcomes look like this.

Reuse an existing skill:

```json
{
  "action": "reuse",
  "task": "vision extraction error on the OCR screen",
  "match": {
    "name": "ocr-debug",
    "category": "ios",
    "reason": "triggers overlap: extraction, vision, error"
  }
}
```

Create a new skill when no strong match exists:

```json
{
  "action": "created",
  "task": "draft a reusable privacy policy update workflow",
  "created_skill": {
    "name": "new-skill-name",
    "category": "docs"
  }
}
```

The exact skill name is inferred from the task, but the flow is stable: reuse when there is a strong match, otherwise scaffold a new reusable local skill and refresh the registry immediately.

## Installation Guide

Use this package when you have the package repository checked out locally and want to install the automation bundle into another repository.

### Prerequisites

- Python 3.10 or newer
- for the npm entrypoint, Node.js 18 or newer
- a target repository where you want repo-local skill automation under `.claude/`
- write access to the target repository

### Standard Install

1. Choose the target repository.
2. Run the installer from this package repository:

```bash
python3 scripts/install.py --target /path/to/target-repo
```

3. The installer will:

- copy `.claude/tools/skill_agent.py`
- copy `.claude/skills/project-skill-router/`
- optionally copy `.claude/tests/test_skill_agent.py`
- insert managed automation blocks into `AGENTS.md` and `CLAUDE.md`
- write `.claude/skill-automation-package.json`
- refresh `.claude/skills/registry.json`

### Why `AGENTS.md` And `CLAUDE.md` Are Updated

The installer adds a bounded managed block so future Codex and Claude Code sessions start from the same routing command instead of bypassing the local skill system.

If your team wants a less invasive rollout:

- use `--skip-agents` to keep `AGENTS.md` untouched
- use `--skip-claude` to keep `CLAUDE.md` untouched
- add the generated command guidance manually after you validate the package in that repository

### Verify The Install

After installation, check the target repository:

```bash
cd /path/to/target-repo
python3 .claude/tools/skill_agent.py list
python3 .claude/tools/skill_agent.py auto "find or create the right reusable workflow" --json
```

You should see the packaged router skill in the list, and `auto` should return either a reusable local skill match or a generated preview/result.

### Common Install Variants

- Preview without writing files: `python3 scripts/install.py --target /path/to/target-repo --dry-run`
- Skip the packaged test file: `python3 scripts/install.py --target /path/to/target-repo --no-tests`
- Skip managed `AGENTS.md`: `python3 scripts/install.py --target /path/to/target-repo --skip-agents`
- Skip managed `CLAUDE.md`: `python3 scripts/install.py --target /path/to/target-repo --skip-claude`

## Managed File Behavior

- If `AGENTS.md` or `CLAUDE.md` does not exist, install creates the file and inserts the managed block.
- If both package markers already exist, install replaces only the content inside that managed block.
- If the markers are missing, install appends the managed block to the end of the existing file.
- `--dry-run` previews the install result without creating the target directory or writing package files, and its status lines use `Would ...` wording for changes that are only being previewed.

## Target Repo Git Hygiene

Decide up front whether the installed automation should be shared through version control or kept local to one checkout.

### Shared Automation In Version Control

Use this when the repository wants shared repo-local skills and shared entrypoint guidance.

Usually commit:

- `.claude/tools/skill_agent.py`
- `.claude/skills/project-skill-router/`
- `.claude/tests/test_skill_agent.py` when installed
- `AGENTS.md` and `CLAUDE.md` when you want the managed guidance blocks shared with the team

Usually ignore:

```gitignore
.claude/skills/registry.json
.claude/skills/usage.json
.claude/skills/_archived/
.claude/skill-automation-package.json
.claude/**/__pycache__/
.claude/**/*.pyc
```

The install manifest is usually not worth committing because it changes on reinstall and mostly records machine-generated install metadata.

Do not blindly ignore `.claude/skills/` if you want teammates to share reusable local skills. That would also hide the actual skill definitions.

### Local-Only Automation

Use this when the install is only for one developer checkout and should not affect the shared repository state.

Typical approach:

- install with `--skip-agents --skip-claude` if you do not want top-level guidance files touched
- ignore the installed automation tree and any optional managed docs

Example:

```gitignore
.claude/
AGENTS.md
CLAUDE.md
```

Pick one policy deliberately. Mixing the two usually creates confusion during upgrades.

### Reinstall After Updates

Upgrade by rerunning the installer from the newer package source:

```bash
python3 scripts/install.py --target /path/to/target-repo
```

If you are consuming the published npm package, the equivalent update path is:

```bash
npx skill-automation-package install --target /path/to/target-repo
```

That npm path is still a reinstall. It uses the existing install metadata to report whether the target is already up to date or whether a newer package version is available before reinstalling.
If you want a version-aware no-op when the target is already current, use:

```bash
npx skill-automation-package update --target /path/to/target-repo
```

### Current Wrapper Limitations

- `update` is a version-aware reinstall, not a partial update.
- `update` blocks implicit downgrade attempts; use `install` only when you intentionally want to replace the target with the current package version.
- If install metadata is malformed, `update` stops and asks you to use `install` for a deliberate reinstall.

What gets updated in place:

- packaged assets under `.claude/` are copied over the existing installed package files
- the managed blocks in `AGENTS.md` and `CLAUDE.md` are replaced when their markers already exist
- `.claude/skill-automation-package.json` is rewritten with the latest package version and install timestamp
- `.claude/skills/registry.json` is regenerated at the end of install

What stays in place:

- repo-local skills you created under `.claude/skills/`
- usage tracking in `.claude/skills/usage.json`
- archived skills under `.claude/skills/_archived/`

Important upgrade caveats:

- if you edited shipped files such as `.claude/tools/skill_agent.py` directly, reinstall will overwrite those edits
- if you removed the managed markers from `AGENTS.md` or `CLAUDE.md`, reinstall will append a new managed block instead of replacing the old text
- install does not remove older files that are no longer part of the package, so cleanup is still manual when package contents shrink

### Default Upgrade Path

Use this unless the target repository intentionally manages `AGENTS.md` and `CLAUDE.md` outside this package.

```bash
python3 scripts/install.py --target /path/to/target-repo --dry-run
python3 scripts/install.py --target /path/to/target-repo
```

This keeps the packaged `.claude` assets and the managed guidance blocks aligned on every reinstall.

For npm releases, `package.json` `version` is the source of truth and the matching git tag should be `vX.Y.Z`.
Run `npm run release:check` before tagging or publishing.

### Upgrade Without Managed Docs

Use this variant only when the target repository already manages `AGENTS.md` and `CLAUDE.md` manually and you want to refresh only the packaged `.claude` assets.

```bash
python3 scripts/install.py --target /path/to/target-repo --dry-run --skip-agents --skip-claude
python3 scripts/install.py --target /path/to/target-repo --skip-agents --skip-claude
```

## Installed Agent Flow

- `reuse`: open the matched local skill and follow it
- `created`: use the generated skill immediately
- `preview-create`: rerun without `--dry-run` to persist the generated skill
- If a step inside the chosen workflow becomes its own repeatable, non-trivial subtask, rerun `python3 .claude/tools/skill_agent.py auto "<sub-task>" --json` for that step and then return to the parent workflow.

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

Runtime routing is recursive by design. A parent skill should hand off any reusable, multi-step sub-flow back into the same automation set with `python3 .claude/tools/skill_agent.py auto "<sub-task>" --json` instead of absorbing that logic into one oversized skill.

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

`sync_assets.py` looks for the nearest matching parent repository that already contains the live `.claude` source tree. If the source-of-truth lives somewhere else, point at it explicitly:

```bash
python3 scripts/sync_assets.py --source-root /path/to/source-repo
```

Then reinstall into a target repository or regenerate the published package commit as needed.

When you need to publish changes from a stale or dirty local checkout, use the documented worktree-based flow in `docs/operations/publish-workflow.md` instead of committing directly on the old checkout.

For npm-specific release flow, version/tag rules, and reinstall-based lifecycle notes, see `docs/operations/npm-release-workflow.md`.

## Verification

From a repository that contains the package source and packaged tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .claude/tests -p 'test_*.py'
```

From this package repository, you can also run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s assets/.claude/tests -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 scripts/install.py --target /tmp/skill-automation-package-dry-run --dry-run
```

Equivalent maintenance helpers are also exposed in `package.json` under `test`, `test:assets`, `install:dry-run`, and `sync-assets`.
Those script wrappers set `PYTHONDONTWRITEBYTECODE=1` so routine verification does not leave Python bytecode behind in the packaged asset tree.

## License

MIT
