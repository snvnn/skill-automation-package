# Update Candidates

Date: 2026-05-26

## Scope

This document lists candidate features and enhancement work for the next updates of `skill-automation-package`.
It is based on the current repository state after the npm wrapper work:

- package version: `0.2.2`
- public entrypoints: `npx skill-automation-package install ...`, `npx skill-automation-package update ...`, and direct `python3 scripts/install.py ...`
- Python core: `scripts/install.py`, `scripts/package_layout.py`, `assets/.claude/tools/skill_agent.py`
- npm wrapper: `bin/skill-automation-package.js`
- packaged assets: `assets/.claude/tools/skill_agent.py`, packaged core skills, optional packaged test, and managed templates

Baseline verification completed before writing this document:

```bash
npm run release:check
```

Result:

- Python package tests passed
- packaged asset tests passed
- Node wrapper tests passed
- installer dry-run passed
- `npm pack --dry-run` produced a 20-file package surface

## Selection Criteria

Candidates are ranked by:

- user impact during install, update, or agent runtime
- ability to reduce accidental data loss or operator confusion
- ability to keep the Python core and npm wrapper contracts aligned
- implementation risk and testability
- whether the work unlocks later improvements

## Priority Summary

### P0. Bring docs and release metadata back to current product truth

Category: documentation / release hygiene

Why this matters:

- `package.json` is at `0.2.2`, but `CHANGELOG.md` currently stops at `v0.1.3`.
- `docs/README.md` still says the npm wrapper work is not implemented yet, even though `bin/skill-automation-package.js`, wrapper tests, npm package fields, and npm release workflow now exist.
- `docs/operations/npm-release-workflow.md` says a dedicated `update` command remains out of scope, while the wrapper currently supports `update`.

Candidate work:

- add changelog entries for the npm wrapper releases through `v0.2.2`
- update `docs/README.md` so npm wrapper docs are no longer described as unimplemented working docs
- update `docs/operations/npm-release-workflow.md` to describe current `install` versus `update` behavior
- decide whether old npm wrapper planning docs under `docs/working/npm-wrapper/` should remain working docs, become archive docs, or be summarized into active operations docs

Reason to do first:

- Future feature work will be harder to reason about if the canonical docs describe a pre-wrapper state.
- This is low-risk and makes the next engineering changes easier to review.

Risk:

- Low implementation risk.
- Main risk is accidentally deleting useful decision history instead of archiving or reclassifying it.

Suggested validation:

- run `npm run release:check`
- add or update guidance-content tests if canonical documentation claims are important enough to lock

### P1. Add an install/update diff preview

Category: install/update UX

Why this matters:

- Current dry-run output is truthful but summary-level.
- It reports counts and managed doc status, but not which packaged files or managed blocks would change.
- Users updating an existing repo need better visibility before allowing packaged files to be overwritten.

Candidate work:

- add a diff-preview mode for install/update dry runs
- report changed, unchanged, missing, and orphaned packaged paths
- summarize whether `AGENTS.md` and `CLAUDE.md` managed blocks would be created, replaced, appended, or skipped
- keep full text diffs optional to avoid noisy default output

Reason to prioritize:

- It improves trust in `install` and `update` without changing the core install contract.
- It pairs naturally with the current reinstall-based lifecycle.

Risk:

- Medium.
- Requires careful comparison logic so dry-run remains side-effect free.
- Managed block diff output can become noisy if not summarized well.

Suggested validation:

- installer tests for new dry-run summary states
- wrapper tests proving `update --dry-run` surfaces the same preview
- fixture tests for new install, same-version reinstall, older-version update, malformed metadata, and missing managed markers

### P2. Define a safe stale packaged-file cleanup model

Category: lifecycle safety

Why this matters:

- Current reinstall intentionally does not remove old packaged files that are no longer shipped.
- This behavior is safe, but it leaves target repos with orphaned package files after package contents shrink.
- The docs already mention manual cleanup, so this is a known lifecycle gap.

Candidate work:

- use prior `.claude/skill-automation-package.json` asset lists to detect previously installed files that are no longer shipped
- report stale packaged files during dry-run before any delete behavior exists
- add a separate explicit cleanup command or flag only after ownership rules are proven
- never remove user-created skills or files outside the previous install manifest

Reason to prioritize:

- This unlocks safer long-term updates as the packaged core skills evolve.
- It should be designed before adding partial update behavior.

Risk:

- High if delete behavior is introduced too early.
- Medium if first implemented as detect-and-report only.
- Ownership ambiguity is the central risk: a previously shipped path may have been manually edited after install.

Suggested validation:

- reinstall tests with prior manifest assets that no longer exist in `package.json`
- tests where stale files are reported but preserved by default
- tests proving local skills, `usage.json`, registry files, and archived skills are never treated as cleanup candidates

### P3. Harden install metadata validation and recovery

Category: lifecycle correctness

Why this matters:

- The npm wrapper already handles malformed install metadata conservatively.
- Recovery is still message-driven: `update` stops and asks the user to use `install`, while `install` proceeds with a warning.
- There is no explicit manifest schema validation beyond version checks.

Candidate work:

- define a manifest schema for `.claude/skill-automation-package.json`
- validate `name`, `version`, `installed_at`, and `assets`
- distinguish recoverable metadata problems from unsafe ones
- add a `doctor` or `status` style report for installed targets

Reason to prioritize:

- Better metadata validation supports diff preview, stale cleanup, and safer version-aware updates.
- It also improves debugging when users report broken installs.

Risk:

- Medium.
- Strict validation can block older installs if backwards compatibility is not handled explicitly.

Suggested validation:

- wrapper tests for malformed, partial, future-version, missing-assets, and older-schema metadata
- Python tests for manifest write compatibility
- docs that describe the recovery path for each state

### P4. Add a wrapper `status` or `doctor` command

Category: diagnostics / supportability

Why this matters:

- Users currently have to infer state from `install`, `update`, direct Python commands, or the install metadata file.
- A diagnostic command would make support much easier without changing install behavior.

Candidate work:

- add `npx skill-automation-package status --target <repo>` or `doctor --target <repo>`
- report:
  - installed package version
  - current package version
  - Python launcher detected by wrapper
  - presence of packaged runtime
  - presence of core skills
  - manifest health
  - registry health
  - whether update would be no-op, upgrade, downgrade-blocked, or unknown
- optionally support `--json` for automation

Reason to prioritize:

- It makes the version-aware lifecycle easier to understand.
- It reduces the need for users to inspect `.claude/skill-automation-package.json` manually.

Risk:

- Medium.
- A diagnostic command can become too broad if it tries to validate all runtime skill behavior at once.

Suggested validation:

- Node wrapper tests with fixture targets
- integration test against a real installed target in a temporary directory
- JSON schema-like assertions if `--json` is added

### P5. Add machine-readable output for npm wrapper lifecycle commands

Category: automation

Why this matters:

- `skill_agent.py` already supports JSON output for many runtime commands.
- The npm wrapper currently prints human-oriented lifecycle messages.
- CI, setup scripts, or agent workflows may need structured output for install/update/status decisions.

Candidate work:

- add `--json` support to wrapper-level `install`, `update`, and any future `status` command
- include fields such as:
  - `command`
  - `target`
  - `current_version`
  - `installed_version`
  - `state`
  - `action`
  - `python`
  - `installer_exit_code`
- keep Python installer stdout/stderr passthrough behavior clear when `--json` is used

Reason to prioritize:

- It gives automation a stable interface without requiring users to parse human strings.
- It aligns wrapper behavior with the existing Python runtime's JSON-friendly design.

Risk:

- Medium.
- The hardest part is preserving human passthrough output while providing valid JSON from the wrapper.

Suggested validation:

- wrapper tests that parse JSON output
- tests for no-op update, update-available, downgrade-blocked, and malformed metadata

### P6. Improve release workflow integrity

Category: release engineering

Why this matters:

- `npm run release:check` is good, but release metadata can still drift.
- The current repo already shows drift: `package.json` is `0.2.2`, while `CHANGELOG.md` stops at `v0.1.3`.

Candidate work:

- add a release metadata check that verifies:
  - `package.json` version appears in `CHANGELOG.md`
  - `README.md` references current commands accurately
  - npm tarball contents match the expected publish surface
  - no `__pycache__` or `.pyc` files are included in git or npm package output
- consider a small script under `scripts/` or an npm script that performs these checks

Reason to prioritize:

- Release drift undermines trust in published packages.
- This is especially important now that `package.json` is both npm metadata and Python-side package manifest.

Risk:

- Low to medium.
- Overly strict text checks can become brittle if docs are reorganized.

Suggested validation:

- run the new check inside `npm run release:check`
- keep assertions focused on stable facts, not exact prose

### P7. Add semver-aware version handling in the wrapper

Category: compatibility

Why this matters:

- The wrapper's version comparison is currently numeric `major.minor.patch`.
- That is enough for stable releases, but it does not account for prerelease tags or build metadata.

Candidate work:

- decide whether prerelease versions are supported
- if supported, implement semver-compatible comparison for install metadata
- if not supported, document that lifecycle comparison requires stable `X.Y.Z` versions

Reason to prioritize:

- This matters before publishing prerelease channels such as `0.3.0-beta.1`.

Risk:

- Low if the project explicitly rejects prerelease comparison for now.
- Medium if semver support is implemented without a dependency and gets edge cases wrong.

Suggested validation:

- wrapper tests for stable versions, prerelease versions, malformed versions, and newer installed versions

### P8. Strengthen Windows coverage for launcher behavior

Category: portability

Why this matters:

- The wrapper includes a Windows-specific `py -3` launcher branch.
- Current tests run well on the local platform, but cross-platform behavior is still mostly inferred unless CI covers Windows.

Candidate work:

- add CI matrix coverage for macOS, Linux, and Windows
- add tests or dependency-injected probing so Windows launcher ordering can be verified without requiring a Windows host for every assertion
- verify quoting and argument forwarding for paths with spaces

Reason to prioritize:

- npm distribution increases the chance of Windows usage.
- Launcher detection is one of the wrapper's core portability responsibilities.

Risk:

- Medium.
- Cross-platform test setup can be noisy if temporary path handling is not normalized carefully.

Suggested validation:

- GitHub Actions matrix if CI is available
- fixture tests for path spaces and `--target=<path>` on all supported platforms

### P9. Add package-surface and asset-manifest consistency checks

Category: packaging correctness

Why this matters:

- `package.json` now has two meanings:
  - npm package manifest
  - Python-side managed asset manifest
- The npm `files` list and Python `managed_assets` / `optional_assets` lists must stay aligned enough that published packages include every install-required file.

Candidate work:

- add a check that every file needed by `scripts/package_layout.py` is included in the npm package surface
- detect packaged bytecode or cache files under `assets/`
- compare `npm pack --dry-run` output against expected runtime files

Reason to prioritize:

- It prevents a class of bugs where tests pass locally but the published package lacks files needed by `npx`.

Risk:

- Medium.
- Parsing `npm pack --dry-run` output can be brittle unless done through a structured npm command or stable package metadata.

Suggested validation:

- package-layout tests for asset presence
- release-check integration that fails if required assets are missing from the npm tarball

### P10. Clarify and enforce core skill ownership

Category: runtime safety

Why this matters:

- The package now ships multiple core default skills.
- Core skills should be refreshed by package reinstall, protected from accidental prune/archive flows, and clearly separated from user-created local skills.

Candidate work:

- make core skill ownership explicit in metadata or install manifest
- ensure runtime commands such as `review`, `update`, and `prune` consistently treat core skills as read-only package assets
- document how downstream users should customize behavior without editing shipped core skills directly

Reason to prioritize:

- This reduces accidental modification of package-managed skills in target repos.
- It also helps future stale-file cleanup avoid confusing user skills with package-owned skills.

Risk:

- Medium.
- Too much protection can make legitimate local customization awkward.

Suggested validation:

- runtime tests for prune/update behavior around core skills
- install tests proving core skills are overwritten on reinstall but local skills are preserved

### P11. Improve target repo onboarding output

Category: user experience

Why this matters:

- After install, users need to know the next exact command to run in the target repo.
- The README explains this, but the installer/wrapper output could be more actionable.

Candidate work:

- print the post-install runtime command using the resolved target path
- when `--skip-agents` or `--skip-claude` is used, summarize that top-level guidance was skipped
- optionally show a concise verification command

Reason to prioritize:

- It helps first-time users move from install to actual runtime usage.

Risk:

- Low.
- Output can become verbose if not kept concise.

Suggested validation:

- installer output tests
- wrapper passthrough tests if wrapper adds pre/post messages

### P12. Decide whether partial update belongs in the product

Category: long-term lifecycle

Why this matters:

- Current `update` is version-aware reinstall, not partial update.
- Partial update could reduce overwrite noise, but it would add ownership and diff complexity.

Candidate work:

- write a design decision record for partial update
- define whether partial update means:
  - only copying changed packaged files
  - only refreshing selected asset groups
  - skipping managed docs by default
  - preserving locally edited package files
- decide whether checksums are needed in install metadata

Reason to deprioritize:

- It is useful but not required while the package remains small.
- Diff preview and manifest hardening should come first.

Risk:

- High.
- Partial update can give a false sense of safety if file ownership is not explicit.

Suggested validation:

- design review before implementation
- extensive fixture tests with locally edited shipped files, removed assets, and changed templates

## Recommended Next Batch

The most practical next update should focus on correctness and trust rather than broad new features.

Recommended batch:

1. P0: docs and release metadata truth sync
2. P6: release workflow integrity checks
3. P1: install/update diff preview design and first implementation
4. P3: metadata validation hardening

Reason:

- P0 fixes visible drift.
- P6 prevents the same drift from recurring.
- P1 improves update confidence without changing ownership policy.
- P3 gives future lifecycle features a safer foundation.

## Deferred Until Later

These should not be first in the next update:

- partial update behavior
- automatic stale-file deletion
- runtime helper expansion beyond installer/update/status lifecycle
- prerelease semver support unless prerelease publishing is planned

The current package is small enough that reinstall-based updates remain acceptable.
The next version should first improve visibility, validation, and release correctness.
