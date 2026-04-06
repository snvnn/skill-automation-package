# npm Wrapper Phase 1-5 GitHub Update Prep

## Summary

- Added a Node CLI entrypoint at `bin/skill-automation-package.js`.
- `install` wraps `scripts/install.py` and preserves the Python installer as the source of truth.
- `update` is now explicitly supported as a version-aware reinstall path.

## Key Features

### Install

- `npx skill-automation-package install --target <repo>`
- Always allowed
- Reinstall-friendly
- Preserves Python installer behavior and passthrough flags

### npm wrapper

- Python launcher discovery:
  - `python3`
  - `python`
  - Windows `py -3`
- Wrapper resolves `scripts/install.py` from its own package location, not caller cwd.
- Child process stdio and exit code are preserved.

### Version detection

- Reads current version from `package.json`
- Reads installed version from `.claude/skill-automation-package.json`
- Distinguishes:
  - not installed
  - already current
  - update available
  - newer installed version
  - malformed metadata

### Update UX

- `npx skill-automation-package update --target <repo>`
- No-op when already current
- Reinstalls only when the target is older
- Blocks implicit downgrade attempts
- Explains overwrite/preserve behavior before reinstall

## Current Known Limitations

- `update` is still a full reinstall, not a partial update.
- Downgrade requires using `install`; `update` blocks it.
- Malformed metadata is handled conservatively with guidance rather than automatic repair.
- Old files that are no longer shipped are not cleaned up automatically.

## Verification Status

- Node wrapper tests cover install/update boundary behavior.
- Python-side install/package-layout tests still pass.
- `npm pack --dry-run` keeps the published surface minimal.

## Phase 6 Link

- See `docs/working/npm-wrapper/phase-6-roadmap.md`
