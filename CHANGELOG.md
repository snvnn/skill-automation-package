# Changelog

## v0.3.0

Released 2026-05-26.

- added release integrity checks for changelog/version drift, npm package fields, required package files, and tracked Python bytecode
- wired release integrity validation into `npm run release:check`
- expanded installer dry-run output with package file previews for created, updated, unchanged, and previously installed but no longer shipped files
- expanded dry-run managed file previews for create, replace, append, unchanged, and skipped states
- added managed `.gitignore` support with shared-friendly generated-state defaults plus `none` and `local-only` modes
- hardened npm wrapper install metadata validation for wrong-package metadata and invalid assets lists
- documented current `install` versus `update` behavior, dry-run preview behavior, and metadata recovery behavior
- brought canonical docs and changelog history up to date with the shipped npm wrapper lifecycle

## v0.2.2

Released 2026-05-26.

- bumped the published package version to `0.2.2`
- protected packaged core helper skills from prune/archive behavior in the installed runtime
- promoted the npx-first quick start in the README while preserving the Python core contract

## v0.2.1

Released 2026-05-26.

- added four packaged read-only core helper skills for project summaries, repo structure analysis, docs entrypoint guidance, and change summaries
- updated install and package-layout tests so all packaged core skills are installed, listed in the manifest, and refreshed on reinstall
- clarified README wording around packaged core default skills

## v0.2.0

Released 2026-05-26.

- added the npm wrapper entrypoint at `bin/skill-automation-package.js`
- added `npx skill-automation-package install --target <repo>` as the published package install path
- added version-aware wrapper lifecycle behavior and install metadata inspection
- added Node wrapper tests for Python launcher discovery, cwd-independent installer resolution, argument forwarding, and update-state handling
- added npm package metadata, publish surface controls, and `npm run release:check`
- reorganized docs into active operations, working docs, and archive areas
- added npm release workflow documentation

## v0.1.3

Released 2026-04-06.

- widened installer and packaged runtime compatibility to Python 3.10 by falling back from `datetime.UTC` to `timezone.utc`
- made installer dry-run output consistently preview-oriented with `Would ...` status lines
- documented target-repo git hygiene choices for shared installs versus local-only installs
- split the README upgrade guidance into a default reinstall path and a separate skip-docs variant
- added a reinstall regression test that proves shipped assets are overwritten while local skills, `usage.json`, and orphaned stale files behave as documented
- expanded `sync_assets.py` coverage for direct-parent and competing-ancestor source-root detection, and documented the nearest-match rule
- aligned README verification commands with the bytecode-clean `PYTHONDONTWRITEBYTECODE=1` workflow
- recorded the completed follow-up work and evidence under `docs/reviews/`

## v0.1.2

Released 2026-04-06.

- fixed installer `--dry-run` so it no longer reports manifest writes that did not happen
- made installer dry-run avoid creating the target directory
- added installer tests for dry-run behavior, managed block replacement, skip flags, manifest output, and refresh side effects
- made `sync_assets.py` support `--source-root` and ancestor auto-detection instead of relying on a fixed parent depth
- documented install side effects, managed block behavior, and upgrade behavior in the README
- added package maintenance scripts for verification and asset sync
- removed the packaged default skill's reference to an unshipped related skill
- cleaned packaged asset verification so routine checks do not leave bytecode in `assets/`
