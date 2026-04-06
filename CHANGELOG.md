# Changelog

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
