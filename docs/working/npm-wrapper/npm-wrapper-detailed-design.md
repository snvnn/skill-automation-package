# npm Wrapper Detailed Design

## TL;DR

This repository should adopt npm as a distribution and onboarding layer, not as a replacement runtime.
The authoritative install flow must remain `scripts/install.py`, and the authoritative installed runtime must remain `.claude/tools/skill_agent.py`.
The initial npm surface should support only `npx skill-automation-package install ...` and should forward that call to the packaged Python installer.
The current repository contract already supports Python 3.10+, so the wrapper should follow that contract unless the project explicitly chooses a separate breaking change.
The design below treats npm introduction as a packaging and entrypoint problem, not as a rewrite of the Python core.

## Scope and Non-Goals

### Decision

The scope of this design is limited to adding a Node-based installer wrapper in front of the existing Python packaging flow.

In scope:

- defining the npm wrapper responsibility boundary
- defining the wrapper directory layout
- defining Python executable discovery
- defining the wrapper-to-installer CLI contract
- defining `package.json` expansion for npm distribution
- defining npm publish-surface rules
- defining wrapper-specific tests
- defining README changes for dual entrypoints

Out of scope:

- rewriting `scripts/install.py` in Node
- rewriting `assets/.claude/tools/skill_agent.py` in Node
- changing the installed `.claude` output structure
- changing packaged skill contents under `assets/.claude/skills/`
- adding a required runtime helper CLI in the first rollout
- changing `scripts/sync_assets.py` semantics as part of npm introduction

### Rationale

The repository already has a stable Python installer, a stable Python runtime asset, a manifest-driven asset layout, and documentation that frames the package as Python-installed automation.
Changing those components while introducing npm would combine packaging change, runtime change, and compatibility change in one rollout.

### Alternatives Considered

- Full Node rewrite of install and runtime
- Dual implementation where Node and Python both implement installer behavior
- npm-only surface that hides the direct Python path completely

### Rejected Alternatives and Why

- Full Node rewrite was rejected because it duplicates working Python logic and creates long-term parity risk.
- Dual implementation was rejected because install behavior would drift across platforms and releases.
- Hiding the direct Python path was rejected because the installed runtime remains Python-based and direct Python usage is still a valid operational path.

### Risk / Tradeoff

The narrower scope reduces rollout risk but also means npm does not immediately improve every workflow.
That tradeoff is acceptable because installer portability is the highest-value problem and can be solved without disturbing the existing Python core.

## Current-State Assumptions

### Decision

This design assumes the current repository contracts remain authoritative until explicitly changed by a future implementation PR.

Current-state assumptions:

- [README.md](/Users/yunhyeon/claudecode/code_agent_skill_automation/skill-automation-package/README.md) describes the project as a Python-installed automation bundle and currently documents `Python 3.10 or newer`.
- [scripts/install.py](/Users/yunhyeon/claudecode/code_agent_skill_automation/skill-automation-package/scripts/install.py) is the only supported installer and already owns:
  - asset selection
  - managed `AGENTS.md` and `CLAUDE.md` updates
  - install manifest writes
  - registry refresh
- [scripts/package_layout.py](/Users/yunhyeon/claudecode/code_agent_skill_automation/skill-automation-package/scripts/package_layout.py) treats [package.json](/Users/yunhyeon/claudecode/code_agent_skill_automation/skill-automation-package/package.json) as the packaging manifest for `name`, `version`, `managed_assets`, `optional_assets`, and `executable_assets`.
- [scripts/sync_assets.py](/Users/yunhyeon/claudecode/code_agent_skill_automation/skill-automation-package/scripts/sync_assets.py) is a package-maintenance tool and auto-detects the nearest matching source root.
- `assets/` contains the packaged `.claude` runtime and skill assets that the installer copies into target repositories.
- `templates/` contains the managed block templates that `scripts/install.py` inserts into `AGENTS.md` and `CLAUDE.md`.

### Rationale

Detailed design must start from what the repository actually does today, not from a hypothetical cleaned-up future state.
That is especially important here because `package.json` already has Python-side meaning and because the README already makes an explicit claim about the distribution model.

### Alternatives Considered

- Designing the wrapper against an aspirational future structure
- Treating `package.json` as free to be repurposed for npm only
- Assuming the Python minimum version is undecided

### Rejected Alternatives and Why

- Designing against a future structure was rejected because it produces a document that cannot safely guide implementation against the current repo.
- Repurposing `package.json` as npm-only metadata was rejected because [scripts/package_layout.py](/Users/yunhyeon/claudecode/code_agent_skill_automation/skill-automation-package/scripts/package_layout.py) already consumes it.
- Treating Python minimum version as undefined was rejected because the current README and Python compatibility work already establish a live contract.

### Risk / Tradeoff

Basing the design on current contracts means the document may look conservative.
That is a deliberate tradeoff to keep the eventual implementation compatible with the repository as it exists now.

## Proposed Architecture

### Decision

The proposed architecture is a hybrid model:

- Python remains the core packaging and runtime layer
- npm provides a lightweight distribution and onboarding layer
- the only required npm entrypoint in the first rollout is an installer wrapper

Recommended repository-level addition:

- `bin/skill-automation-package.js` as the npm-facing executable
- optional helper modules under `lib/` if the wrapper logic should be split

Authoritative flow:

```text
npx skill-automation-package install --target <repo>
        ↓
Node wrapper resolves packaged installer path
        ↓
Python executable runs scripts/install.py
        ↓
install.py copies assets, updates templates, writes manifest, refreshes registry
```

### Rationale

This architecture preserves the current authoritative boundaries:

- installer logic remains in Python
- runtime logic remains in Python
- packaged `.claude` outputs remain unchanged

It also addresses the main portability problem:

- users get an npm-friendly entrypoint
- the repository does not have to maintain a second implementation of install behavior

### Alternatives Considered

- Node wrapper plus Node runtime helper in the initial rollout
- putting the wrapper under `src/` instead of `bin/`
- treating `scripts/sync_assets.py` as another npm-facing command in the first phase

### Rejected Alternatives and Why

- Runtime helper support in the first rollout was rejected because it expands the wrapper from entrypoint layer into orchestration layer.
- A `src/`-first structure was rejected because npm executable packages are easiest to understand when the published executable lives under `bin/`.
- Exposing `sync_assets.py` immediately was rejected because it is a maintainer workflow, not the first-use end-user workflow.

### Risk / Tradeoff

Keeping npm limited to the installer path means some users may ask why runtime commands are not also wrapped.
That tradeoff is preferred over expanding scope and diluting the clean Python-core boundary.

## CLI Contract Design

### Decision

The first npm CLI contract is installer-only.

Supported form:

```bash
npx skill-automation-package install --target /path/to/target-repo [installer options]
```

Unsupported in the first rollout:

- `npx skill-automation-package run ...`
- `npx skill-automation-package sync-assets ...`
- any wrapper-only shorthand flags that do not already exist in the Python installer

The wrapper must treat `install` as a named subcommand rather than mapping bare arguments directly to `scripts/install.py`.

### Rationale

An explicit `install` subcommand makes the wrapper self-describing and leaves room for future expansion without making the first release ambiguous.
It also keeps npm command semantics aligned with the repository's actual role: installing packaged automation into another repository.

### Alternatives Considered

- Bare command form: `npx skill-automation-package --target <repo>`
- Multi-command first release: `install`, `run`, `sync-assets`
- No subcommand at all, with all arguments forwarded directly

### Rejected Alternatives and Why

- The bare command form was rejected because it leaves no clean namespace for future optional commands.
- Multi-command first release was rejected because only the install path is currently justified by the repository's existing public workflow.
- Full direct forwarding without a subcommand was rejected because it makes help text and future compatibility harder.

### Risk / Tradeoff

Introducing a subcommand adds a small amount of syntax overhead.
That is acceptable because it creates a stable public CLI boundary and limits ambiguity.

## Python Discovery Strategy

### Decision

The wrapper should implement ordered launcher discovery and version verification.

Ordered discovery policy:

1. `python3`
2. `python`
3. On Windows, `py -3`

Version policy:

- default contract: Python 3.10 or newer
- the wrapper must verify the detected interpreter version before launching the installer
- the wrapper must emit a clear message when Python is missing or below the supported minimum

Path policy:

- the wrapper must resolve the packaged installer path from its own installed package location
- the wrapper must not resolve `scripts/install.py` relative to the caller's current working directory

### Rationale

Portability depends on launcher normalization.
`npx` execution contexts vary by OS and by how the package is installed, so the wrapper cannot assume:

- a particular launcher name
- a particular working directory
- a particular shell path resolution order

The working-directory constraint is especially important because `npx` runs the package executable from outside the package root in common real-world cases.

### Alternatives Considered

- Require users to pass an explicit `PYTHON` path
- Search only `python3`
- Search only `python`
- Shell out through platform-specific scripts instead of direct process spawning

### Rejected Alternatives and Why

- Requiring an explicit Python path was rejected because it weakens the onboarding value of npm.
- Searching only `python3` was rejected because many Windows and some local environments expose only `python` or `py -3`.
- Searching only `python` was rejected because `python3` is the clearer and more common cross-platform Unix-style entrypoint.
- Shell-script indirection was rejected because it adds another portability layer without solving the core detection problem.

### Risk / Tradeoff

Launcher discovery adds platform-specific complexity.
That tradeoff is necessary because portability is one of the primary goals of the wrapper.

## Argument Passthrough Design

### Decision

The wrapper must preserve the Python installer as the source of truth for option semantics.

Passthrough policy:

- the wrapper accepts `install`
- all arguments after `install` are forwarded to `scripts/install.py`
- the wrapper does not rename, reinterpret, or normalize installer flags beyond platform-safe process invocation

Authoritative passthrough set in the current design:

- `--target`
- `--dry-run`
- `--no-tests`
- `--skip-agents`
- `--skip-claude`

Process contract:

- the wrapper must propagate the Python installer's exit code
- the wrapper must preserve installer stdout and stderr as the user-facing output

### Rationale

The Python installer already defines behavior for dry runs, optional packaged tests, and managed-document updates.
Duplicating or remapping that logic in the wrapper would create contract drift.

### Alternatives Considered

- Wrapper-specific aliases such as `--no-docs`
- Parsing and validating installer flags inside Node
- Wrapping installer output in a custom Node UI layer

### Rejected Alternatives and Why

- Wrapper-specific aliases were rejected because they create long-term mismatch with Python CLI documentation.
- Node-side flag validation was rejected because it duplicates the installer parser and increases maintenance burden.
- Custom output wrapping was rejected because the Python installer's current output is already the authoritative operational summary.

### Risk / Tradeoff

The wrapper will feel thin by design.
That is acceptable because thin passthrough is exactly what keeps the Python installer authoritative and minimizes compatibility risk.

## package.json Design

### Decision

`package.json` must become a dual-role manifest.

Fields whose current meaning must be preserved:

- `name`
- `version`
- `managed_assets`
- `optional_assets`
- `executable_assets`

Fields that may be added for npm distribution:

- `bin`
- `files`
- `engines`
- npm-oriented `scripts` that do not conflict with current developer workflows
- optionally `repository`, `homepage`, `bugs`, and `keywords`

Preservation rule:

- no npm change may break [scripts/package_layout.py](/Users/yunhyeon/claudecode/code_agent_skill_automation/skill-automation-package/scripts/package_layout.py), which currently reads `name`, `version`, `managed_assets`, `optional_assets`, and `executable_assets`

### Rationale

The repository already treats `package.json` as a packaging manifest for the Python side.
That means npm metadata must be additive and non-destructive.

### Alternatives Considered

- Split the Python manifest into a separate JSON file and repurpose `package.json`
- Keep `package.json` minimal and add npm metadata elsewhere
- Keep npm metadata out of the repo and publish from a transformed build artifact

### Rejected Alternatives and Why

- Splitting the Python manifest now was rejected because it expands the npm rollout into a packaging-format refactor.
- Storing npm metadata elsewhere was rejected because npm expects `package.json` as the canonical package manifest.
- Publishing from a transformed artifact was rejected because it introduces a build pipeline before the wrapper itself is validated.

### Risk / Tradeoff

Using one manifest for both Python-side packaging and npm distribution is efficient but increases coupling.
That tradeoff is acceptable only if the preserved fields remain clearly protected in implementation and tests.

## Publish-Surface Design

### Decision

The npm tarball should contain only files required to execute the installer wrapper and the packaged Python install flow.

Include by default:

- `bin/`
- `scripts/`
- `assets/`
- `templates/`
- `README.md`
- `LICENSE`
- `package.json`

Exclude by default:

- `docs/archive/reviews/`
- planning-only documents under `docs/`
- most repository-local tests, unless the project deliberately wants packaged self-tests
- local development artifacts
- Python bytecode and caches

### Rationale

The npm tarball should represent a clean distribution surface, not the full development history of the repository.
That matters here because the repository contains internal review and rollout documents that are useful in git but irrelevant to npm consumers.

### Alternatives Considered

- Publish the full repository by default
- Include `docs/` wholesale for transparency
- Include all tests in the npm tarball

### Rejected Alternatives and Why

- Publishing the full repository was rejected because it widens the support surface and leaks internal planning artifacts into the package.
- Including all `docs/` was rejected because internal review notes are not part of the runtime contract.
- Including all tests was rejected because most tests are developer-facing verification, not runtime dependencies.

### Risk / Tradeoff

An overly narrow `files` list can accidentally exclude runtime-critical assets such as `templates/` or `assets/`.
That tradeoff means publish-surface validation must be explicit and not inferred.

## Test Strategy

### Decision

Testing must be split into two layers with separate responsibilities.

Python core tests remain responsible for:

- installer behavior
- asset layout behavior
- runtime skill-agent behavior
- sync-assets behavior

Node wrapper tests become responsible for:

- launcher discovery behavior
- Python version gating
- current working directory independence
- argument passthrough
- installer exit-code passthrough
- platform-specific launcher fallback assumptions

Test-ownership rule:

- behavior already guaranteed by Python tests should not be duplicated in Node tests
- behavior unique to npm execution should not be backfilled into Python tests

### Rationale

The Python core already has a meaningful test surface.
The wrapper introduces a new failure layer, but not a new implementation of install logic.
Testing should reflect that boundary instead of mixing concerns.

### Alternatives Considered

- Reuse only the existing Python tests
- Move installer tests from Python to Node
- Duplicate the same install scenarios in both test layers

### Rejected Alternatives and Why

- Reusing only Python tests was rejected because they cannot verify npm-specific launcher failure modes.
- Moving installer tests into Node was rejected because the installer is still implemented in Python.
- Full duplication was rejected because it increases maintenance cost without increasing confidence proportionally.

### Risk / Tradeoff

Two test layers increase repository complexity.
That tradeoff is justified because the wrapper introduces new portability behavior that the Python suite cannot cover.

## Documentation Update Strategy

### Decision

README should move to a dual-entrypoint explanation while preserving Python as the primary implementation identity.

Required documentation changes:

- `Quick Start` should show:
  - npm / `npx` install path
  - direct Python install path
- `Installation Guide` should explain that npm wraps the Python installer
- a new `Distribution Model` section should explicitly state:
  - npm is the distribution and onboarding layer
  - Python remains the core runtime
  - Python is still required even when using `npx`

Documentation rule:

- the README must not imply that npm replaces the installed Python runtime
- the README must not imply that Node alone is sufficient

### Rationale

The current README explicitly says the project is not an npm runtime package.
If npm is introduced, that statement must evolve without losing the core message that Python remains authoritative.

### Alternatives Considered

- Replace the Python-first docs with npm-first docs only
- Keep npm entirely out of the README and rely on package metadata
- Move dual-entrypoint explanation to a separate document instead of README

### Rejected Alternatives and Why

- npm-only docs were rejected because they obscure the actual runtime dependency model.
- Leaving npm out of the README was rejected because the wrapper would then exist without first-party explanation.
- Hiding the explanation in a separate document was rejected because entrypoint decisions belong in README-level onboarding.

### Risk / Tradeoff

Dual-entrypoint documentation is longer and slightly more complex.
That tradeoff is necessary to prevent users from misunderstanding the relationship between Node and Python in this package.

## Compatibility and Portability Considerations

### Decision

Compatibility and portability are first-class design constraints, not implementation afterthoughts.

The design must explicitly account for:

- Python 3.10+ versus 3.11+ policy conflict
- `npx` current working directory independence
- Windows / macOS / Linux launcher differences
- `package.json` coupling with Python-side packaging
- npm tarball contamination by non-runtime internal documents
- scope-creep risk if runtime helper commands are added too early

### Rationale

The wrapper is being introduced specifically for portability.
A design that does not explicitly handle launcher differences, cwd differences, and contract differences would fail its primary purpose.

### Alternatives Considered

- Resolve compatibility details during implementation only
- Treat Windows as a later concern
- Ignore the Python minimum-version conflict until after the wrapper exists

### Rejected Alternatives and Why

- Deferring compatibility details to implementation was rejected because they determine the wrapper contract itself.
- Treating Windows as a later concern was rejected because launcher detection is part of the initial value proposition.
- Ignoring the Python version conflict was rejected because it would create contradictory documentation on day one.

### Risk / Tradeoff

Being explicit about compatibility constraints increases document size and upfront design effort.
That tradeoff is acceptable because it lowers the risk of shipping a wrapper that is technically present but operationally brittle.

## Tradeoffs and Rejected Options

### Decision

The project should explicitly reject several tempting expansions in the first npm rollout.

Rejected for the first rollout:

- full Node rewrite of install flow
- full Node rewrite of runtime flow
- runtime helper commands as a required part of the initial CLI
- npm-driven asset sync as a first-class public command
- repurposing `package.json` as npm-only metadata

### Rationale

Each rejected option increases either:

- implementation duplication
- platform-specific behavior risk
- release-surface size
- ambiguity about whether Python or Node is authoritative

### Alternatives Considered

- Incrementally replacing Python pieces with Node over time
- Shipping an ambitious multi-command npm CLI from the first release
- Building a general-purpose project management CLI around the skill package

### Rejected Alternatives and Why

- Incremental Python replacement was rejected because it creates a long transition period with split ownership.
- Multi-command CLI launch was rejected because it creates scope creep before installer portability is proven.
- General-purpose CLI expansion was rejected because it changes the repository's product identity.

### Risk / Tradeoff

The project may appear conservative compared with tools that expose a large Node CLI immediately.
That tradeoff is deliberate because the current repository's strength is its stable Python core and install contract.

## Open Questions

### Decision

The following items remain unresolved and must be decided before coding starts.

Open questions:

- Should the wrapper inherit the current Python 3.10+ policy, or should the project deliberately raise the minimum version as a separate breaking change?
- Should helper modules live under `lib/` or `src/` once the wrapper grows beyond a single file?
- Should Node wrapper tests live under `tests/node/` or a separate top-level directory?
- Should `CHANGELOG.md` be part of the npm tarball, or should publication stay limited to runtime-essential files?
- Is npm publication itself part of the first implementation milestone, or is GitHub-distributed `npx` usage enough for the first release?
- Should runtime helper commands remain explicitly out of scope until after wrapper stabilization, or should a roadmap note promise them?

### Rationale

These questions affect implementation details, release expectations, and compatibility promises.
They do not block the architecture decision itself, but they do need explicit resolution before code is written.

### Alternatives Considered

- Resolve all open questions only during the implementation PR
- Leave policy questions implicit and let implementation choose defaults

### Rejected Alternatives and Why

- Resolving everything inside the implementation PR was rejected because several of these questions define the public contract.
- Leaving them implicit was rejected because the resulting code would encode policy choices without prior agreement.

### Risk / Tradeoff

Keeping explicit open questions slows the start of coding slightly.
That tradeoff is better than silently embedding product and compatibility policy into the first wrapper implementation.

## Recommended Next Implementation Sequence

### Decision

Implementation should proceed in a strict sequence that matches the dependency structure of the design.

Recommended sequence:

1. Resolve the Python minimum-version policy for the npm wrapper.
2. Define the exact wrapper public CLI for `install`.
3. Implement wrapper path resolution so packaged `scripts/install.py` is resolved from the package location, not the caller's current working directory.
4. Add launcher discovery and version gating.
5. Extend `package.json` with npm fields while preserving Python-side manifest consumers.
6. Add wrapper-specific tests for launcher detection, cwd independence, argument passthrough, and exit-code behavior.
7. Update README to a dual-entrypoint model.
8. Validate the npm publish surface explicitly before any registry publication decision.
9. Only after that, decide whether runtime helper expansion is warranted.

### Rationale

This sequence keeps the public contract and the most failure-prone portability assumptions in front of packaging polish.
It also ensures that documentation and publish behavior describe tested reality rather than planned behavior.

### Alternatives Considered

- Update README first, then implement the wrapper
- Add npm publish metadata before locking launcher behavior
- Bundle runtime helper work into the same implementation cycle

### Rejected Alternatives and Why

- README-first rollout was rejected because documentation should not lead the actual CLI contract.
- Publish-metadata-first rollout was rejected because `bin` and `files` should describe a known wrapper structure.
- Bundling runtime helpers was rejected because it would mix portability work with product-surface expansion.

### Risk / Tradeoff

This sequence is slower than doing wrapper code, README, and publish metadata all at once.
That tradeoff is intentional because it reduces the chance of creating a public npm contract that later has to be walked back.

### Implementation Readiness Checklist

- The project has an explicit decision on Python minimum version for npm entrypoints.
- The installer-only CLI contract is approved.
- The wrapper directory layout is approved.
- The rule for resolving packaged `scripts/install.py` independent of caller cwd is approved.
- The launcher discovery order across macOS, Linux, and Windows is approved.
- The preserved `package.json` fields for Python-side packaging are documented and protected.
- The npm tarball include/exclude policy is approved.
- The split between Python core tests and Node wrapper tests is approved.
- The README dual-entrypoint framing is approved.

### Questions That Must Be Resolved Before Coding

- Is the npm wrapper contract officially Python 3.10+ or Python 3.11+?
- Will the first implementation include npm publication, or only local/GitHub-distributed wrapper usage?
- Will helper modules use `lib/` or `src/`?
- Where will Node wrapper tests live in the repository?
- Will `CHANGELOG.md` ship in the npm tarball?
- Is runtime-helper work explicitly deferred beyond the first wrapper implementation?
