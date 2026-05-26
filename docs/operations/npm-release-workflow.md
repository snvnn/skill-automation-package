# npm Release Workflow

## Goal

Publish the npm wrapper as a small distribution layer without changing the Python core contract.

## Source Of Truth

- `package.json` `version` is the release source of truth.
- The git tag for a release must match that version in the form `vX.Y.Z`.
- npm publication should be done only from a commit whose checked-in `package.json` version already matches the intended tag.

## Version Bump Rules

- Patch release:
  - wrapper bug fixes
  - packaging or publish-surface fixes
  - test-only hardening
  - documentation updates that do not expand the public install contract
- Minor release:
  - backward-compatible user-visible changes to the install surface
  - backward-compatible compatibility or distribution expansions

The wrapper lifecycle still uses `package.json` as the only package version source.
There is no separate lifecycle versioning system.

## Release Check

Before tagging or publishing, run:

```bash
npm run release:check
```

That check is expected to validate:

- Python-side tests
- wrapper-specific Node tests
- release metadata and package-surface integrity
- installer dry-run behavior
- `npm pack --dry-run` output

## Recommended Release Flow

1. Bump `package.json` to the intended version.

Recommended commands:

```bash
npm version patch --no-git-tag-version
```

or

```bash
npm version minor --no-git-tag-version
```

2. Run the release verification:

```bash
npm run release:check
```

3. Commit the release changes.

4. Create a matching git tag:

```bash
git tag vX.Y.Z
```

5. Publish the package:

```bash
npm publish
```

If the current checkout is stale or dirty, use the worktree-based process in `docs/operations/publish-workflow.md` before tagging or publishing.

## Repo-Local Install Metadata

The installer already writes repo-local install metadata to:

```text
.claude/skill-automation-package.json
```

Current fields include:

- `name`
- `version`
- `installed_at`
- `assets`

That file is the current lifecycle metadata record for installed targets.
It is useful for local inspection and reinstall tracking, but it is usually not worth committing.

## Install And Update Strategy

Current update behavior is reinstall-based.

Use `install` when you intentionally want to install or reinstall the package into a target repository:

```bash
npx skill-automation-package install --target /path/to/target-repo
```

Use `update` when you want a version-aware operation that may no-op if the target is already current:

```bash
npx skill-automation-package update --target /path/to/target-repo
```

Use the direct Python path when you are working from a local checkout of this repository:

```bash
python3 scripts/install.py --target /path/to/target-repo
```

Current policy:

- `install` always runs and allows deliberate reinstall
- `update` reads `.claude/skill-automation-package.json` before deciding whether to run
- `update` no-ops when the installed target is already at the current package version
- `update` runs the installer when the target has an older installed package version
- `update` blocks implicit downgrades when the target reports a newer installed version
- `update` blocks malformed, incomplete, wrong-package, or invalid-assets install metadata and asks the user to run `install` for deliberate recovery
- packaged files are overwritten on reinstall
- managed `AGENTS.md` and `CLAUDE.md` blocks are refreshed unless skipped
- a managed `.gitignore` block is refreshed by default for generated state
- `--gitignore-mode none` leaves `.gitignore` untouched
- `--gitignore-mode local-only` ignores the whole local install for one-checkout use
- repo-local skills, usage tracking, and archived skills are preserved
- old package files that are no longer shipped are not removed automatically

The `update` command is still reinstall-based.
It is not a partial update and does not delete stale package files.

Dry-run behavior:

- reports package files that would be created, updated, or left unchanged
- reports previously installed files that are no longer shipped when they are listed in prior install metadata
- reports whether managed guidance files and `.gitignore` would be created, replaced, appended, unchanged, or skipped
- does not delete stale files or mutate the target repository
