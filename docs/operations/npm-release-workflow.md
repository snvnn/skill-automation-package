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

This Phase 3 workflow does not add a special update command and does not define a separate lifecycle versioning system beyond `package.json`.

## Release Check

Before tagging or publishing, run:

```bash
npm run release:check
```

That check is expected to validate:

- Python-side tests
- wrapper-specific Node tests
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

## Update Strategy

Current update behavior is reinstall-based.

Use either of these forms:

```bash
npx skill-automation-package install --target /path/to/target-repo
```

or

```bash
python3 scripts/install.py --target /path/to/target-repo
```

Current policy:

- packaged files are overwritten on reinstall
- managed `AGENTS.md` and `CLAUDE.md` blocks are refreshed unless skipped
- repo-local skills, usage tracking, and archived skills are preserved
- old package files that are no longer shipped are not removed automatically

A dedicated `update` command remains out of scope unless reinstall stops being sufficient for normal upgrade flows.
