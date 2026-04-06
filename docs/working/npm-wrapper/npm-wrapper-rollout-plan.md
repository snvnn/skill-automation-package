# npm Wrapper Rollout Plan

## TL;DR

This repository should not replace its Python core with Node.
The safest path is a hybrid model where npm adds a portable installer entrypoint while `scripts/install.py` and the installed `.claude` runtime remain authoritative.
Phase 1 should add only an installer wrapper, Phase 2 should stabilize npm packaging and wrapper tests, and Phase 3 should remain optional.
The most important planning constraint is to keep the current Python install flow and `.claude` output structure unchanged.
The current repository already documents Python 3.10+ support, so any npm wrapper should follow that same minimum-version contract unless a separate breaking-change decision is made.

## Architecture Decision

The right insertion point for npm in this repository is the install entrypoint, not the runtime core.

Current structure analysis:

- `README.md` presents the package as a Python-installed automation bundle, not an npm runtime package.
- `scripts/install.py` is the authoritative installer that copies packaged assets, updates managed docs, writes install metadata, and refreshes the skill registry.
- `assets/.claude/tools/skill_agent.py` is the installed runtime CLI used inside the target repository after installation.
- `assets/.claude/skills/project-skill-router/` is shipped as a packaged default skill and should remain part of the installed `.claude` tree.
- `scripts/sync_assets.py` is a package-maintenance utility and does not need to sit on the npm entry path.
- `package.json` already acts as package metadata and asset-manifest input for the Python packaging layer.

Because of that structure, npm should be treated as a distribution and onboarding layer only:

```text
npx skill-automation-package install --target <repo>
        ↓
Node CLI wrapper
        ↓
python3 scripts/install.py --target <repo>
```

The hybrid decision is preferable because it preserves:

- one implementation of install logic
- one implementation of runtime logic
- one installed `.claude` output contract
- one source of truth for packaged assets

### Work Breakdown Rationale

The work is split into three phases because the risks are different and should not be coupled.

- Phase 1 is limited to wrapper introduction so the repository gains a new entrypoint without changing the Python core contract.
- Phase 2 is packaging stabilization so npm metadata, publish surface, tests, and documentation can be validated independently from the wrapper bootstrap itself.
- Phase 3 is optional expansion because runtime helpers and broader CLI ambitions are not required to achieve the primary portability goal.

This work is not combined into one phase for three reasons:

- wrapper bootstrap failures and npm publish failures have different recovery paths
- runtime helper expansion is not required for installer portability
- version-policy changes should not be hidden inside a distribution-layer rollout

Dependency order:

- Phase 2 depends on Phase 1 because publish metadata and documentation should describe a real wrapper contract, not a hypothetical one
- Phase 3 depends on Phase 1 and should usually wait until Phase 2 is stable
- none of the phases should change `scripts/install.py`, `assets/.claude/tools/skill_agent.py`, or the installed `.claude` layout as part of the npm introduction itself

## Phase 1

### Goal

Introduce an npm installer wrapper while leaving the Python core and installed runtime untouched.

### Work Item 1: Define the wrapper scope

What:

- add one npm-facing entrypoint
- support only the `install` subcommand at first
- pass installer arguments through to `scripts/install.py`

Why:

- the current first-touch user action is installation
- the installer is already the correct system boundary for npm to wrap

Ordering rationale:

- the command contract must be frozen before package metadata, tests, and docs are updated

Risk:

- if the wrapper surface grows beyond installer passthrough in this phase, the rollout turns into a CLI redesign rather than a portability improvement

### Work Item 2: Define Python interpreter discovery

What:

- search `python3`
- fall back to `python`
- on Windows, also support `py -3`
- resolve the packaged `scripts/install.py` path from the npm package location rather than the caller's current directory

Why:

- portability gains come from launcher normalization, not from rewriting the installer

Ordering rationale:

- interpreter and script-path resolution must be designed before the wrapper contract is documented or tested

Risk:

- if the wrapper resolves `scripts/install.py` relative to the caller's current working directory, `npx` execution will break immediately

### Work Item 3: Align the Python version contract

What:

- define the wrapper's minimum supported Python version to match the current repository contract
- default assumption: Python 3.10 or newer, because that is what the repository currently documents and supports

Why:

- the npm wrapper should not silently impose a stricter compatibility policy than direct Python usage unless that is a deliberate breaking change

Ordering rationale:

- version checks affect the wrapper's error messages, test expectations, and README wording

Risk:

- if the wrapper enforces Python 3.11+ while the direct path supports 3.10+, users will see conflicting compatibility behavior

### Work Item 4: Freeze passthrough semantics

What:

- preserve current installer options:
  - `--target`
  - `--dry-run`
  - `--no-tests`
  - `--skip-agents`
  - `--skip-claude`
- avoid inventing wrapper-specific alternative flags

Why:

- the Python installer is already the authoritative CLI contract

Ordering rationale:

- argument semantics should be locked before README examples and test cases are written

Risk:

- if the wrapper reinterprets flags, the Python and npm entrypoints will drift over time

### Phase 1 Exit Criteria

- the repository has a clear design for `npx skill-automation-package install --target <repo>`
- the wrapper acts only as an install front-end
- the Python core remains unchanged in responsibility and install output

## Phase 2

### Goal

Stabilize npm packaging, documentation, and wrapper verification without altering the Python core.

### Work Item 1: Expand `package.json` into a dual-role manifest safely

What:

- add npm-oriented fields such as `bin`, `files`, and `engines`
- preserve the existing fields that the Python packaging layer already reads

Why:

- `package.json` already matters to the Python side, so npm metadata must be additive rather than disruptive

Ordering rationale:

- this should happen after the wrapper contract is defined so `bin` and `files` can describe real package contents

Risk:

- an overly aggressive edit to `package.json` can break `scripts/package_layout.py` consumers or omit required packaged assets

### Work Item 2: Define the npm publish surface

What:

- include the minimum runtime-required package contents:
  - `bin/`
  - `scripts/`
  - `assets/`
  - `templates/`
  - `README.md`
  - `LICENSE`
  - `package.json`
- exclude non-runtime materials such as `docs/archive/reviews/` and most development-only tests unless a specific publish need exists

Why:

- portability improves when the published package is smaller, clearer, and less coupled to local repository history

Ordering rationale:

- publish-surface decisions should be made after wrapper responsibilities are fixed but before npm release automation is considered

Risk:

- if `files` excludes `templates/` or `assets/`, installs may succeed partially while generating incomplete target repositories

### Work Item 3: Add wrapper-specific tests

What:

- create a Node-side test layer for wrapper behavior
- cover:
  - missing Python
  - unsupported Python version
  - exact argument passthrough
  - exit-code passthrough
  - platform-specific launcher fallback

Why:

- existing Python `unittest` coverage validates core behavior, not npm launch behavior

Ordering rationale:

- tests belong after the wrapper contract is stable but before npm publication

Risk:

- publishing without wrapper tests creates a high chance of shipping a package that installs correctly but fails at process launch

### Work Item 4: Convert README to a dual-entrypoint model

What:

- keep the direct Python path in the documentation
- add an npm / `npx` install path alongside it
- add a `Distribution Model` section that explains:
  - npm is a lightweight distribution layer
  - the installed runtime remains Python-based
  - Python is still required

Why:

- without explicit wording, users may assume the project has become a Node-native runtime package

Ordering rationale:

- documentation should describe the finalized Phase 1 wrapper contract and the publish assumptions from Phase 2

Risk:

- ambiguous wording will create support friction, especially around the question of whether Node alone is enough

### Phase 2 Exit Criteria

- `package.json` supports npm distribution without breaking Python-side manifest consumers
- wrapper tests are defined or implemented as a separate verification layer
- README reflects both entrypoints and preserves the Python-core identity of the project
- publish-surface decisions are explicit rather than implicit

## Phase 3

### Goal

Evaluate optional expansions without making them part of the required npm rollout.

### Work Item 1: Consider runtime helper commands

What:

- optionally evaluate commands such as:
  - `npx skill-automation-package run --target <repo> auto "<task>" --json`

Why:

- some users may want a wrapper for common runtime operations after installation

Ordering rationale:

- this should happen only after the installer wrapper and npm packaging are stable

Risk:

- if introduced too early, the wrapper may become a second orchestration layer that competes with the installed Python runtime

### Work Item 2: Cross-platform polish

What:

- harden quoting behavior
- normalize Windows-specific launcher handling
- refine help and error text across macOS, Linux, and Windows

Why:

- the real value of a wrapper comes from predictable launcher behavior across environments

Ordering rationale:

- platform polish is easier once the base wrapper flow already exists and has tests

Risk:

- doing this before core wrapper behavior is stable will slow the rollout and blur the source of failures

### Work Item 3: Publish and release process integration

What:

- decide how npm publication should line up with:
  - `package.json` version bumps
  - git tags such as `vX.Y.Z`
  - changelog updates

Why:

- npm introduction changes the release surface, even if it does not change the Python core

Ordering rationale:

- release-process integration should be handled only after the package contents and wrapper contract are stable

Risk:

- mixing code rollout and registry publication design too early increases rollback complexity

### Phase 3 Exit Criteria

- optional wrapper expansion remains clearly optional
- npm publication rules do not redefine the Python core
- release sequencing is explicit if npm publication is adopted

## Risk Analysis

### Compatibility risk

The biggest immediate planning risk is Python version drift.
The repository currently documents Python 3.10+ support, so a wrapper plan that assumes 3.11+ would introduce a silent policy fork.

### Manifest risk

`package.json` already has meaning for the Python packaging layer.
Any npm metadata expansion must preserve the fields that `scripts/package_layout.py` expects.

### Path-resolution risk

The wrapper must resolve the packaged `scripts/install.py` from its installed package location.
If it depends on the caller's current working directory, `npx` execution will fail.

### Publish-surface risk

The npm `files` list can accidentally omit required assets or templates.
This risk is especially high because the repository contains both runtime-required files and internal documentation that should not ship.

### Scope-creep risk

The primary portability win comes from a lightweight installer front-end.
If the project tries to add runtime helpers, full Node parity, and publication automation in the same change set, the rollout will become harder to validate and harder to unwind.

## Open Questions

- Should the npm wrapper inherit the current Python 3.10+ contract, or should the project deliberately raise the minimum supported Python version as a separate breaking change?
- Should the wrapper live under `bin/` plus helper modules under `lib/`, or under `bin/` plus `src/`?
- Should Node-side wrapper tests live under `tests/node/` or in a separate top-level directory?
- Should `CHANGELOG.md` be included in the npm tarball, or should the published package include only runtime-essential files?
- Should the initial npm rollout remain installer-only, or should a future runtime helper path be considered part of the roadmap?
- Is npm publication itself a required deliverable for the first rollout, or is local / GitHub-distributed `npx` usage enough for the first phase?
