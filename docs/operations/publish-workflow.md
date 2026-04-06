# Publish Workflow

## Goal

Publish changes safely even when the current local checkout is behind `origin/main`, contains unrelated local state, or resolves a different Python interpreter than the one used for development.

## Why This Exists

The repository can end up in a state where:

- the current checkout is several commits behind `origin/main`
- the working tree is dirty and should not be rewritten casually
- validation depends on a specific Python installation that is not the default in every directory

In that case, publishing directly from the current checkout is risky. The safer approach is to create a separate worktree from the latest remote base, move only the intended changes, validate there, and push a branch from that clean context.

## Recommended Flow

1. Inspect the current repository state.

```bash
git status -sb
git fetch origin
git rev-list --left-right --count main...origin/main
```

2. If the current checkout is behind or otherwise not a safe publish base, create a separate worktree from the latest remote branch.

```bash
git worktree add -b codex/<description> /tmp/<repo>-publish origin/main
```

If slash-separated branch names are blocked by existing refs, fall back to a hyphenated branch name such as `codex-<description>`.

3. Move only the intended files into the publish worktree.

- Copy the edited files explicitly.
- Do not bulk-copy unrelated local state.
- Ignore transient directories such as `__pycache__/`.

4. Validate inside the publish worktree.

Use the same interpreter and commands that succeeded in the original development environment. If `/tmp` or another worktree path resolves a different `python3`, call the intended interpreter explicitly.

Example:

```bash
/opt/anaconda3/bin/python3 -m unittest discover -s tests -p 'test_*.py'
/opt/anaconda3/bin/python3 -m unittest discover -s assets/.claude/tests -p 'test_*.py'
/opt/anaconda3/bin/python3 scripts/install.py --target /tmp/skill-automation-package-dry-run --dry-run
```

5. Stage only the intended files and commit tersely.

```bash
git add <paths...>
git commit -m "<summary>"
```

6. Push the branch and open a draft PR.

```bash
git push -u origin <branch-name>
```

Then open a draft PR through the GitHub app or a direct GitHub URL. If `gh auth status` reports an invalid token, do not block on repairing `gh` if the GitHub app path is already available.

Historical example:

- A dated example from the April 6, 2026 publish is preserved in `docs/archive/legacy/2026-04-06-publish-workflow-example.md`.
- Keep this runbook focused on the repeatable procedure above; use the archived note only when you need the specific historical case.

## Cleanup

After the PR is merged or no longer needed:

```bash
git worktree remove /tmp/<repo>-publish
git branch -d <branch-name>
```

Delete the local branch only after it is merged or otherwise no longer needed.
