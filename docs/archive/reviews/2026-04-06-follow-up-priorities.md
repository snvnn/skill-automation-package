# Follow-up Priorities After v0.1.2 Review

## Scope

This priority list combines two inputs:

- the release review recorded in `docs/archive/reviews/2026-04-06-v0.1.2-code-review.md`
- the observed install session against the `Flippers` repository on 2026-04-06

The goal is to rank follow-up work by practical user impact, not just code cleanliness.

## Priority List

### P1. Fix Python version failure mode for both install-time and runtime paths

Status:

- Completed on 2026-04-06
- `scripts/install.py`, `assets/.claude/tools/skill_agent.py`, and `assets/.claude/tests/test_skill_agent.py` now fall back to `timezone.utc` when `datetime.UTC` is unavailable
- verified with Python 3.10 and Python 3.12 in this repository

Why this is first:

- This is the only issue that caused a real installation failure in the observed terminal session.
- The installer failed under the environment's default `python3` because it imported `datetime.UTC`.
- After forcing installation with Python 3.12, the installed runtime asset still needed a local compatibility patch before `python3 .claude/tools/skill_agent.py ...` became usable in that repository.

Observed evidence:

- install dry-run failed under default `python3` with `ImportError: cannot import name 'UTC' from 'datetime'`
- the target repository's default `python3` was Python 3.10
- the installed `.claude/tools/skill_agent.py` also needed a Python 3.10 compatibility fallback during the session

Why it matters:

- README examples consistently use `python3`, so users are likely to run the package with whatever `python3` resolves to in their shell.
- The current prerequisite is documented, but the failure mode is late and unfriendly.
- This affects both package maintainers testing installs and downstream repositories trying to use the installed tool.

Recommended direction:

- either add explicit Python version guards with actionable error messages before import-sensitive code paths
- or widen compatibility if Python 3.10 support is intended

Implemented direction:

- widened compatibility to Python 3.10 for the affected install/runtime/test imports

Relevant references:

- `scripts/install.py:8`
- `assets/.claude/tools/skill_agent.py:9`
- `assets/.claude/tests/test_skill_agent.py:9`
- `README.md:32`
- `README.md:40`
- `README.md:88`

### P2. Make dry-run output fully truthful

Status:

- Completed on 2026-04-06
- dry-run status lines now use `Would ...` wording for preview-only changes
- added test coverage for dry-run `AGENTS.md`, `CLAUDE.md`, and manifest status output

Why this is next:

- The release review already found that dry-run still reports `Updated AGENTS.md: yes` and `Updated CLAUDE.md: yes`.
- That did not block installation, but it still undermines operator trust in preview mode.

Why it matters:

- Dry-run output is supposed to tell users what would happen without ambiguity.
- Partial truthfulness is especially risky when the tool edits top-level guidance files.

Recommended direction:

- switch dry-run reporting to explicit preview wording such as `Would update ...`
- add test coverage for the `AGENTS.md` and `CLAUDE.md` status lines, not only the manifest line

Implemented direction:

- changed dry-run output labels to preview-oriented wording
- added direct CLI assertions for dry-run status lines

Relevant references:

- `docs/archive/reviews/2026-04-06-v0.1.2-code-review.md`
- `scripts/install.py:51`
- `scripts/install.py:60`
- `scripts/install.py:85`
- `README.md:139`
- `tests/test_install.py:65`

### P3. Document and possibly automate target-repo git hygiene

Status:

- Documentation completed on 2026-04-06
- README now explains shared-versus-local target-repo policies and includes example `.gitignore` patterns
- automation support for generating ignore snippets is still optional future work

Why this is high enough to matter:

- In the observed install session, the target repository owner explicitly wanted install-created files added to `.gitignore`.
- The package currently documents what it installs, but not whether those installed assets are normally expected to be committed, ignored, or team-policy dependent.

Observed evidence:

- the install into `Flippers` required a manual `.gitignore` decision for `.claude/`, `AGENTS.md`, `CLAUDE.md`, and install metadata
- the session had to separate shipped assets from generated metadata by hand

Why it matters:

- Without clear guidance, different users will make inconsistent choices about whether repo-local skill assets belong in source control.
- That creates friction during adoption and upgrade.

Recommended direction:

- document a clear policy for target repos:
  - what is usually committed
  - what is optional
  - what is purely generated metadata
- consider a helper mode or printed snippet for `.gitignore` recommendations if the package wants to support ignore-first workflows

Implemented direction:

- documented two explicit target-repo policies in the README
- included separate ignore guidance for shared automation and local-only automation

Relevant references:

- `README.md:20`
- `README.md:35`
- `README.md:154`

### P4. Add a realistic reinstall and upgrade integration test

Status:

- Completed on 2026-04-06
- added an installer CLI regression test that reruns install into a pre-populated target repository
- verified packaged asset overwrite, managed block replacement, preserved `usage.json`, preserved local skills, regenerated registry, and surviving orphaned files

Why this follows the top three:

- The review already identified that reinstall behavior is documented but not exercised against a real pre-existing installation.
- The observed session reinforces that upgrade and reinstall flows are where environment-specific assumptions surface.

Why it matters:

- Current tests prove small installer behaviors, but not the full story of reinstalling into a repository that already has:
  - managed guidance files
  - existing `usage.json`
  - existing local skills
  - stale package files that are no longer shipped

Recommended direction:

- add one integration-style reinstall test fixture covering an already-installed target repo
- verify which files are preserved, overwritten, regenerated, or left orphaned

Implemented direction:

- added a reinstall fixture to `tests/test_install.py`
- locked the documented cleanup caveat by proving that unshipped stale files under a managed directory are left behind on reinstall

Relevant references:

- `docs/archive/reviews/2026-04-06-v0.1.2-code-review.md`
- `README.md:146`
- `tests/test_install.py:91`

### P5. Clarify the default upgrade path versus the skip-docs variant

Status:

- Completed on 2026-04-06
- README now separates the default reinstall path from the skip-docs variant under distinct subsections
- added guidance-content coverage so the default path remains visually primary in future edits

Why it still deserves follow-up:

- The release review found that the README upgrade section is easy to skim incorrectly.
- This is mainly a documentation structure issue, but it affects real operator behavior.

Why it matters:

- Users may copy the two-command block and treat the `--skip-agents --skip-claude` form as the default upgrade path.
- That can leave managed guidance files stale even while the package itself is updated.

Recommended direction:

- separate the default upgrade path and the skip-docs variant into clearly labeled subsections
- keep the default path visually primary

Implemented direction:

- split the README into `Default Upgrade Path` and `Upgrade Without Managed Docs`
- kept the managed-docs update path as the primary reinstall example and moved the skip-docs variant into its own explicitly limited section

Relevant references:

- `README.md:146`
- `README.md:173`
- `README.md:180`

### P6. Expand `sync_assets.py` detection coverage at the edges

Status:

- Completed on 2026-04-06
- added tests for direct-parent detection and nearest-ancestor preference when multiple parent candidates match
- clarified the nearest-match rule in both the CLI help text and README maintenance guidance

Why this is lower priority:

- The new `--source-root` and ancestor auto-detection logic is directionally good.
- No real failure was observed in the install session because the session used the package directly rather than `sync_assets.py`.
- The remaining risk is edge-case ambiguity rather than a proven regression.

Why it matters:

- Multi-match ancestor trees or unusual vendoring layouts could still pick the wrong source root.
- The current tests cover happy paths, not ambiguous ones.

Recommended direction:

- add tests for ambiguous ancestor matches
- add a colocated-source test
- decide whether auto-detection should stop at the first match or reject multiple plausible matches

Implemented direction:

- chose the nearest matching ancestor as the stable auto-detection rule
- added tests that lock both the direct-parent case and the nearest-match case

Relevant references:

- `scripts/sync_assets.py:25`
- `tests/test_sync_assets.py:42`

## Suggested Execution Order

1. Python version compatibility and failure messaging
2. Dry-run truthfulness and dry-run test coverage
3. Target-repo git hygiene guidance
4. Reinstall and upgrade integration coverage
5. Upgrade section structure cleanup
6. `sync_assets.py` edge-case coverage

## Summary

All six ranked follow-ups from the v0.1.2 review are now completed.
The resulting release work closed the real-world Python compatibility failure, made preview output and upgrade docs more trustworthy, and added stronger regression coverage around reinstall and asset-sync behavior.
An additional documentation cleanup also aligned the README verification commands with the package's bytecode-clean maintenance scripts.
