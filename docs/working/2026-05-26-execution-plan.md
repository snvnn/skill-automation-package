# Execution Plan for Next Update

Date: 2026-05-26

## Goal

Turn `docs/working/2026-05-26-update-candidates.md` into an immediately actionable update plan.
This plan focuses on the next practical batch, not the entire long-term backlog.

Execution status:

- Completed on 2026-05-26
- Implemented P0, P6, P1, and P3
- Added gitignore automation to the same working batch after follow-up review
- Released in the working tree as `0.3.0` pending commit/tag/publish
- Verified with `npm run release:check`

Recommended batch:

1. P0: docs and release metadata truth sync
2. P6: release workflow integrity checks
3. P1: install/update diff preview
4. P3: install metadata validation hardening
5. P4: safe target `.gitignore` automation for generated install state

## Current Baseline

Repository state used for planning:

- `package.json` version: `0.2.2`
- npm wrapper exists at `bin/skill-automation-package.js`
- wrapper supports `install` and `update`
- Python installer remains authoritative at `scripts/install.py`
- package layout remains manifest-driven through `scripts/package_layout.py`
- current release check passes:

```bash
npm run release:check
```

Known drift to address first:

- `CHANGELOG.md` stops at `v0.1.3`
- `docs/README.md` still describes npm wrapper work as not implemented
- `docs/operations/npm-release-workflow.md` still says a dedicated `update` command is out of scope

## Execution Principles

- Keep Python core behavior authoritative.
- Keep npm wrapper behavior focused on lifecycle orchestration around install/update.
- Prefer explicit diagnostics over implicit mutation.
- Add tests before or alongside each behavior change.
- Keep delete or cleanup behavior out of this batch.
- Default gitignore automation should ignore generated state only, not shared skill definitions.

## Phase 1: Documentation and Release Truth Sync

Source candidate: P0

### Objective

Make the canonical docs match the current product state before adding more behavior.

### Files To Touch

- `CHANGELOG.md`
- `docs/README.md`
- `docs/operations/npm-release-workflow.md`
- optionally `tests/test_guidance_content.py`

### Work Items

1. Add missing changelog entries.

What:

- add entries for the npm wrapper work up to `v0.2.2`
- include `install`, `update`, packaged core skills, wrapper tests, npm package surface, and release check changes

Why:

- `package.json` is already at `0.2.2`, so release history should not stop at `v0.1.3`

Acceptance criteria:

- `CHANGELOG.md` includes a `v0.2.2` section
- the latest changelog section describes current public commands accurately

2. Update docs index truth.

What:

- update `docs/README.md` so npm wrapper docs are no longer framed as unimplemented
- distinguish current canonical docs from historical working docs

Why:

- the npm wrapper has already shipped in the repository

Acceptance criteria:

- `docs/README.md` names active npm release docs as canonical
- old planning docs are described as historical or background material, not current implementation status

3. Update npm release workflow.

What:

- rewrite the sections that say `update` is out of scope
- document current `install` versus `update` behavior:
  - `install` always reinstalls
  - `update` is version-aware and may no-op
  - `update` blocks implicit downgrades
  - malformed metadata requires deliberate `install`

Why:

- operational docs should match `bin/skill-automation-package.js`

Acceptance criteria:

- `docs/operations/npm-release-workflow.md` describes current wrapper lifecycle behavior
- no canonical doc says the wrapper is not implemented

### Tests / Verification

Run:

```bash
npm run test
npm run test:wrapper
npm run release:check
```

If content tests are added or updated, they should verify stable facts rather than exact prose.

### Risk

Low.
The main risk is over-editing historical documents instead of preserving decision history.

## Phase 2: Release Workflow Integrity Checks

Source candidate: P6

### Objective

Prevent the same release/docs drift from recurring.

### Files To Touch

- new script under `scripts/`, likely `scripts/check_release_integrity.py`
- `package.json`
- `tests/`, only if the check has unit-testable helpers
- `README.md` or `docs/operations/npm-release-workflow.md` if command documentation changes

### Work Items

1. Add a release integrity check.

What:

- verify `package.json` version appears in `CHANGELOG.md`
- verify `package.json` has required npm wrapper fields:
  - `bin`
  - `files`
  - `engines`
  - `managed_assets`
  - `optional_assets`
  - `executable_assets`
- verify the npm `files` list includes every file required by the Python package layout
- verify no tracked or package-included Python bytecode is present

Why:

- `package.json` is now both npm metadata and Python-side asset manifest
- manual review already missed changelog drift

Acceptance criteria:

- the check fails when `CHANGELOG.md` does not mention the current package version
- the check fails when an install-required asset is absent from the npm publish surface
- the check passes on the current corrected repository state

2. Wire the check into release verification.

What:

- add an npm script such as `release:integrity`
- include it in `release:check`

Why:

- release checks should catch metadata drift before tags or npm publication

Acceptance criteria:

- `npm run release:check` runs the new integrity check
- failure output is actionable and names the missing or mismatched file/field

### Tests / Verification

Run:

```bash
npm run release:check
```

Also run the new check directly:

```bash
npm run release:integrity
```

### Risk

Low to medium.
The check can become brittle if it asserts exact README prose.
Keep it focused on stable metadata facts and package-surface invariants.

## Phase 3: Install/Update Diff Preview

Source candidate: P1

### Objective

Make dry-run and version-aware update previews specific enough that users can see what will change before reinstalling.

### Files To Touch

- `scripts/install.py`
- `scripts/package_layout.py` if reusable asset comparison helpers are needed
- `bin/skill-automation-package.js` only if wrapper-level text needs to summarize update state differently
- `tests/test_install.py`
- `tests/node/wrapper.test.js`
- `README.md`

### Work Items

1. Define preview output format.

What:

- keep default dry-run concise
- report asset status groups:
  - `would copy`
  - `would update`
  - `unchanged`
  - `previously installed but no longer shipped`
- report managed doc states:
  - create
  - replace
  - append
  - unchanged
  - skipped

Why:

- current dry-run only reports total copied files and yes/no document updates

Acceptance criteria:

- output remains readable for first-time installs
- update previews identify stale packaged files without deleting them

2. Implement side-effect-free comparison.

What:

- compare package assets under `assets/` with target files
- compare managed block output with current `AGENTS.md` and `CLAUDE.md`
- read prior install metadata when present to identify stale packaged files
- do not mutate target files in dry-run

Why:

- diff preview must preserve the current dry-run guarantee

Acceptance criteria:

- dry-run does not create the target directory
- dry-run does not write package files, manifest, registry, or docs
- stale files are reported only from prior install metadata, not from arbitrary `.claude` contents

3. Update wrapper behavior if needed.

What:

- ensure `npx skill-automation-package update --target ... --dry-run` surfaces the Python preview cleanly
- avoid duplicating Python diff logic in Node

Why:

- wrapper should remain lifecycle orchestration, not install implementation

Acceptance criteria:

- wrapper tests prove update dry-runs pass through and preserve installer output

### Tests / Verification

Add or update tests for:

- first install dry-run
- reinstall where packaged files changed
- reinstall where packaged files are unchanged
- managed docs create/replace/append/skipped
- stale files reported from prior manifest
- stale files preserved by default

Run:

```bash
npm run test
npm run test:wrapper
npm run install:dry-run
```

### Risk

Medium.
The main risk is accidentally turning dry-run into a mutating operation or making output too noisy.
Keep full diffs out of the default path unless a separate flag is intentionally added.

## Phase 4: Install Metadata Validation Hardening

Source candidate: P3

### Objective

Make install metadata states explicit and reusable across wrapper lifecycle features.

### Files To Touch

- `bin/skill-automation-package.js`
- `tests/node/wrapper.test.js`
- possibly a new wrapper helper module if the current bin file becomes too large
- `docs/operations/npm-release-workflow.md`
- `README.md`

### Work Items

1. Define metadata state categories.

What:

- classify install metadata as:
  - not installed
  - valid same version
  - valid older version
  - valid newer version
  - malformed JSON
  - missing version
  - invalid version
  - wrong package name
  - invalid assets list

Why:

- wrapper update behavior already depends on metadata, but validation is currently narrow

Acceptance criteria:

- each state maps to an explicit `install` and `update` behavior
- unsafe states are handled conservatively

2. Harden wrapper validation.

What:

- validate `name`, `version`, and `assets`
- preserve compatibility with older metadata if fields are missing but recovery is safe
- keep `install` as the deliberate recovery path
- keep `update` conservative when state is unknown

Why:

- lifecycle commands need predictable behavior when target metadata is partial or broken

Acceptance criteria:

- `install` proceeds with clear warnings for recoverable unknown states
- `update` no-ops, upgrades, or blocks based on explicit state
- downgrade behavior remains blocked by default

3. Document recovery behavior.

What:

- update README and operations docs with the metadata recovery table

Why:

- users should know when to use `install` versus `update`

Acceptance criteria:

- docs explain how to recover from malformed metadata without editing files manually

### Tests / Verification

Add wrapper tests for:

- missing metadata
- malformed JSON
- missing version
- invalid version
- wrong package name
- invalid assets
- newer installed version
- older installed version

Run:

```bash
npm run test:wrapper
npm run release:check
```

### Risk

Medium.
Overly strict validation can block older installs.
The implementation should distinguish warning states from hard-stop states.

## Phase 5: Review and Release Prep

## Phase 5: Gitignore Automation

Follow-up candidate added during execution.

### Objective

Automatically manage safe generated-state `.gitignore` entries when installing into existing Git repositories or directories that may become Git repositories later.

### Files To Touch

- `scripts/install.py`
- `tests/test_install.py`
- `README.md`
- `docs/operations/npm-release-workflow.md`
- `tests/test_guidance_content.py`

### Work Items

1. Add `--gitignore-mode`.

What:

- support `generated`, `local-only`, and `none`
- default to `generated`

Why:

- generated install state is usually not worth committing, while shared skills and managed docs may be intentionally versioned

Acceptance criteria:

- `generated` ignores registry, usage, archive, install metadata, and Python cache files
- `local-only` ignores `.claude/`, `AGENTS.md`, and `CLAUDE.md`
- `none` leaves `.gitignore` untouched

2. Use a managed `.gitignore` block.

What:

- insert or replace a bounded package-owned block
- avoid duplicate entries across reinstall

Why:

- reinstall should be idempotent and reversible by deleting a single managed block

Acceptance criteria:

- existing unrelated `.gitignore` content is preserved
- dry-run reports create/replace/append/unchanged/skipped without writing

### Tests / Verification

Run:

```bash
npm run test
npm run release:check
```

### Risk

Medium.
The main risk is ignoring too much by default.
The default must stay limited to generated state so shared `.claude` skills remain commit-friendly.

## Phase 6: Review and Release Prep

### Objective

Prepare the completed update for release without mixing in deferred lifecycle features.

### Files To Touch

- `CHANGELOG.md`
- `package.json`
- docs touched by completed phases

### Work Items

1. Decide release version.

Recommendation:

- patch release if only P0 and P6 are completed
- minor release if P1 or P3 changes user-visible lifecycle behavior

2. Update changelog.

What:

- document completed phases only
- mention any intentionally deferred features

3. Run full verification.

Commands:

```bash
npm run release:check
```

Optional direct checks:

```bash
npm pack --dry-run --cache /tmp/skill-automation-package-npm-cache
```

4. Confirm publish surface.

What:

- inspect npm pack file list
- confirm no internal planning docs, bytecode, or cache files are included
- confirm all package assets needed by install are included

## Explicitly Deferred

These should not be included in the next batch unless priorities change:

- automatic deletion of stale packaged files
- partial update that copies only changed assets
- runtime helper commands beyond install/update/status lifecycle
- prerelease semver handling
- broad runtime skill behavior redesign

## Suggested Work Order

1. Phase 1: docs and release metadata truth sync
2. Phase 2: release integrity check
3. Phase 3 design pass: exact dry-run preview output
4. Phase 3 implementation and tests
5. Phase 4 metadata validation state table
6. Phase 4 implementation and tests
7. Phase 5 release prep

## Ready-To-Start Checklist

- The current untracked candidate document is either committed or intentionally included with this plan.
- The next batch scope is limited to P0, P6, P1, and P3.
- No stale-file deletion is implemented in this batch.
- `npm run release:check` passes before code changes begin.
- Tests are added before relying on new installer or wrapper behavior.
