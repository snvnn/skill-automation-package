from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS_DIR))

import package_layout


CORE_SKILL_PATHS = (
    Path(".claude/skills/project-skill-router"),
    Path(".claude/skills/core-project-summary"),
    Path(".claude/skills/core-repo-structure-analysis"),
    Path(".claude/skills/core-docs-entrypoint-guidance"),
    Path(".claude/skills/core-change-summary"),
)


class PackageLayoutTests(unittest.TestCase):
    def test_load_package_layout_reads_grouped_assets(self) -> None:
        layout = package_layout.load_package_layout()

        self.assertIn(Path(".claude/tools/skill_agent.py"), layout.managed_assets)
        for skill_path in CORE_SKILL_PATHS:
            self.assertIn(skill_path, layout.managed_assets)
        self.assertIn(Path(".claude/tests/test_skill_agent.py"), layout.optional_assets)
        self.assertIn(Path(".claude/tools/skill_agent.py"), layout.executable_assets)

    def test_copy_assets_expands_directories_and_marks_executable(self) -> None:
        with tempfile.TemporaryDirectory() as source_dir, tempfile.TemporaryDirectory() as dest_dir:
            source_root = Path(source_dir)
            destination_root = Path(dest_dir)

            skill_agent = source_root / ".claude" / "tools" / "skill_agent.py"
            skill_agent.parent.mkdir(parents=True, exist_ok=True)
            skill_agent.write_text("#!/usr/bin/env python3\n", encoding="utf-8")

            skill_dir = source_root / ".claude" / "skills" / "router"
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text("# Router\n", encoding="utf-8")
            (skill_dir / "skill.json").write_text("{}\n", encoding="utf-8")

            copied_files = package_layout.copy_assets(
                source_root=source_root,
                destination_root=destination_root,
                asset_paths=[
                    Path(".claude/tools/skill_agent.py"),
                    Path(".claude/skills/router"),
                ],
                executable_assets=frozenset({Path(".claude/tools/skill_agent.py")}),
            )

            copied_relative = sorted(path.relative_to(destination_root) for path in copied_files)
            self.assertEqual(
                copied_relative,
                [
                    Path(".claude/skills/router/SKILL.md"),
                    Path(".claude/skills/router/skill.json"),
                    Path(".claude/tools/skill_agent.py"),
                ],
            )
            self.assertTrue(os.access(destination_root / ".claude" / "tools" / "skill_agent.py", os.X_OK))


if __name__ == "__main__":
    unittest.main()
