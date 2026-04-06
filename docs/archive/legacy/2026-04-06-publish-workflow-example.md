# April 6, 2026 Publish Example

This note preserves the dated example that was previously embedded in the active publish workflow runbook.

The repository was published with the worktree-based flow because:

- the original checkout on `main` was behind `origin/main` by five commits
- the original checkout was intentionally left untouched so local state would not be lost
- the clean publish branch was created from `origin/main` in a temporary worktree
- validation in the worktree initially picked up Python 3.10 instead of the Python 3.12 interpreter used in the original workspace, so checks were rerun with the explicit interpreter path

That publish produced:

- branch: `codex-refactor-package-extensibility`
- commit: `74b6ec0`
- draft PR: `#1`
