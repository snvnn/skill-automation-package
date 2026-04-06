from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PACKAGE_ROOT / "scripts"
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS_DIR))

import install
import package_layout


class InstallScriptTests(unittest.TestCase):
    def test_upsert_block_replaces_existing_managed_block(self) -> None:
        existing = (
            "# AGENTS.md\n\n"
            "Existing intro.\n\n"
            "<!-- SKILL-AUTOMATION:AGENTS:START -->\n"
            "Old block\n"
            "<!-- SKILL-AUTOMATION:AGENTS:END -->\n"
            "\nTrailing notes.\n"
        )
        block = (
            "<!-- SKILL-AUTOMATION:AGENTS:START -->\n"
            "New block\n"
            "<!-- SKILL-AUTOMATION:AGENTS:END -->\n"
        )

        updated = install.upsert_block(
            existing,
            block,
            install.AGENTS_MARKERS[0],
            install.AGENTS_MARKERS[1],
            "# AGENTS.md\n\n",
        )

        self.assertIn("Existing intro.", updated)
        self.assertIn("New block", updated)
        self.assertIn("Trailing notes.", updated)
        self.assertNotIn("Old block", updated)

    def test_write_install_manifest_skips_writes_in_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            target_root = Path(tempdir)
            manifest_path = target_root / ".claude" / "skill-automation-package.json"

            wrote_manifest = install.write_install_manifest(
                manifest_path=manifest_path,
                layout=package_layout.load_package_layout(),
                target_root=target_root,
                copied_files=[target_root / ".claude" / "tools" / "skill_agent.py"],
                dry_run=True,
            )

            self.assertFalse(wrote_manifest)
            self.assertFalse(manifest_path.exists())

    def test_cli_dry_run_reports_no_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            target_root = Path(tempdir) / "target-repo"

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "install.py"),
                    "--target",
                    str(target_root),
                    "--dry-run",
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=PACKAGE_ROOT,
            )

            self.assertIn("Wrote install manifest: no", result.stdout)
            self.assertIn("Refreshed registry: no", result.stdout)
            self.assertFalse(target_root.exists())
            self.assertFalse((target_root / ".claude" / "skill-automation-package.json").exists())
            self.assertFalse((target_root / "AGENTS.md").exists())
            self.assertFalse((target_root / "CLAUDE.md").exists())
            self.assertFalse((target_root / ".claude" / "tools" / "skill_agent.py").exists())

    def test_cli_respects_skip_flags_and_omits_optional_test_asset(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            target_root = Path(tempdir) / "target-repo"

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "install.py"),
                    "--target",
                    str(target_root),
                    "--no-tests",
                    "--skip-agents",
                    "--skip-claude",
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=PACKAGE_ROOT,
            )

            manifest_path = target_root / ".claude" / "skill-automation-package.json"
            self.assertIn("Updated AGENTS.md: no", result.stdout)
            self.assertIn("Updated CLAUDE.md: no", result.stdout)
            self.assertIn("Refreshed registry: yes", result.stdout)
            self.assertTrue(manifest_path.exists())
            self.assertFalse((target_root / "AGENTS.md").exists())
            self.assertFalse((target_root / "CLAUDE.md").exists())
            self.assertFalse((target_root / ".claude" / "tests" / "test_skill_agent.py").exists())
            self.assertTrue((target_root / ".claude" / "skills" / "registry.json").exists())

            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["name"], "skill-automation-package")
            self.assertNotIn(".claude/tests/test_skill_agent.py", payload["assets"])


if __name__ == "__main__":
    unittest.main()
