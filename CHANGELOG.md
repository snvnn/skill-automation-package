# Changelog

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
