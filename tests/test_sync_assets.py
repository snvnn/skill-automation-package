from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS_DIR))

import package_layout
import sync_assets


CORE_SKILL_NAMES = (
    "project-skill-router",
    "core-project-summary",
    "core-repo-structure-analysis",
    "core-docs-entrypoint-guidance",
    "core-change-summary",
)


class SyncAssetsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.layout = package_layout.PackageLayout(
            name="skill-automation-package",
            version="test",
            managed_assets=(
                Path(".claude/tools/skill_agent.py"),
                Path(".claude/skills/project-skill-router"),
                Path(".claude/skills/core-project-summary"),
                Path(".claude/skills/core-repo-structure-analysis"),
                Path(".claude/skills/core-docs-entrypoint-guidance"),
                Path(".claude/skills/core-change-summary"),
            ),
            optional_assets=(Path(".claude/tests/test_skill_agent.py"),),
            executable_assets=frozenset({Path(".claude/tools/skill_agent.py")}),
        )

    def test_resolve_source_root_uses_explicit_root(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            source_root = Path(tempdir)
            self.write_source_tree(source_root)

            resolved = sync_assets.resolve_source_root(
                self.layout,
                explicit_root=source_root,
            )

            self.assertEqual(resolved, source_root.resolve())

    def test_resolve_source_root_auto_detects_matching_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            repo_root = Path(tempdir) / "source-repo"
            package_root = repo_root / "vendor" / "skill-automation-package"
            package_root.mkdir(parents=True, exist_ok=True)
            self.write_source_tree(repo_root)

            resolved = sync_assets.resolve_source_root(
                self.layout,
                package_root=package_root,
            )

            self.assertEqual(resolved, repo_root)

    def test_resolve_source_root_auto_detects_direct_parent_source_root(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            repo_root = Path(tempdir) / "source-repo"
            package_root = repo_root / "skill-automation-package"
            package_root.mkdir(parents=True, exist_ok=True)
            self.write_source_tree(repo_root)

            resolved = sync_assets.resolve_source_root(
                self.layout,
                package_root=package_root,
            )

            self.assertEqual(resolved, repo_root)

    def test_resolve_source_root_prefers_nearest_matching_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            outer_root = Path(tempdir) / "outer-repo"
            inner_root = outer_root / "nested-source"
            package_root = inner_root / "vendor" / "skill-automation-package"
            package_root.mkdir(parents=True, exist_ok=True)
            self.write_source_tree(outer_root)
            self.write_source_tree(inner_root)

            resolved = sync_assets.resolve_source_root(
                self.layout,
                package_root=package_root,
            )

            self.assertEqual(resolved, inner_root)

    def test_resolve_source_root_raises_when_no_source_tree_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            package_root = Path(tempdir) / "vendor" / "skill-automation-package"
            package_root.mkdir(parents=True, exist_ok=True)

            with self.assertRaises(FileNotFoundError) as context:
                sync_assets.resolve_source_root(
                    self.layout,
                    package_root=package_root,
                )

            self.assertIn("--source-root", str(context.exception))

    def write_source_tree(self, repo_root: Path) -> None:
        skill_agent = repo_root / ".claude" / "tools" / "skill_agent.py"
        skill_agent.parent.mkdir(parents=True, exist_ok=True)
        skill_agent.write_text("#!/usr/bin/env python3\n", encoding="utf-8")

        for skill_name in CORE_SKILL_NAMES:
            skill_dir = repo_root / ".claude" / "skills" / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(f"# {skill_name}\n", encoding="utf-8")
            (skill_dir / "skill.json").write_text("{}\n", encoding="utf-8")

        test_file = repo_root / ".claude" / "tests" / "test_skill_agent.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("print('ok')\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
