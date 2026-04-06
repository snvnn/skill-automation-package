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


CORE_SKILL_NAMES = (
    "project-skill-router",
    "core-project-summary",
    "core-repo-structure-analysis",
    "core-docs-entrypoint-guidance",
    "core-change-summary",
)


class InstallScriptTests(unittest.TestCase):
    def write_local_skill(
        self,
        target_root: Path,
        *,
        name: str,
        title: str,
        description: str,
        summary: str,
        category: str,
    ) -> Path:
        skill_dir = target_root / ".claude" / "skills" / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            (
                "---\n"
                f"description: {description}\n"
                "---\n"
                f"# {title}\n\n"
                f"{summary}\n"
            ),
            encoding="utf-8",
        )
        (skill_dir / "skill.json").write_text(
            json.dumps(
                {
                    "category": category,
                    "summary": summary,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return skill_dir

    def assert_core_skills_installed(self, target_root: Path) -> None:
        for skill_name in CORE_SKILL_NAMES:
            skill_dir = target_root / ".claude" / "skills" / skill_name
            self.assertTrue((skill_dir / "SKILL.md").exists(), skill_name)
            self.assertTrue((skill_dir / "skill.json").exists(), skill_name)

    def assert_manifest_lists_core_skills(self, manifest: dict[str, object]) -> None:
        assets = set(manifest["assets"])
        for skill_name in CORE_SKILL_NAMES:
            self.assertIn(f".claude/skills/{skill_name}/SKILL.md", assets)
            self.assertIn(f".claude/skills/{skill_name}/skill.json", assets)

    def overwrite_packaged_core_skills(self, target_root: Path) -> None:
        for skill_name in CORE_SKILL_NAMES:
            skill_dir = target_root / ".claude" / "skills" / skill_name
            (skill_dir / "SKILL.md").write_text(f"# Old {skill_name}\n", encoding="utf-8")
            (skill_dir / "skill.json").write_text("{}\n", encoding="utf-8")

    def assert_packaged_core_skills_match_assets(self, target_root: Path) -> None:
        for skill_name in CORE_SKILL_NAMES:
            packaged_dir = PACKAGE_ROOT / "assets" / ".claude" / "skills" / skill_name
            installed_dir = target_root / ".claude" / "skills" / skill_name
            self.assertEqual(
                (installed_dir / "SKILL.md").read_text(encoding="utf-8"),
                (packaged_dir / "SKILL.md").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                (installed_dir / "skill.json").read_text(encoding="utf-8"),
                (packaged_dir / "skill.json").read_text(encoding="utf-8"),
            )

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

            self.assertIn("Would update AGENTS.md: yes", result.stdout)
            self.assertIn("Would update CLAUDE.md: yes", result.stdout)
            self.assertIn("Would write install manifest: no", result.stdout)
            self.assertIn("Refreshed registry: no", result.stdout)
            self.assertFalse(target_root.exists())
            self.assertFalse((target_root / ".claude" / "skill-automation-package.json").exists())
            self.assertFalse((target_root / "AGENTS.md").exists())
            self.assertFalse((target_root / "CLAUDE.md").exists())
            self.assertFalse((target_root / ".claude" / "tools" / "skill_agent.py").exists())

    def test_cli_dry_run_reports_no_doc_updates_when_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            target_root = Path(tempdir) / "target-repo"

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "install.py"),
                    "--target",
                    str(target_root),
                    "--dry-run",
                    "--skip-agents",
                    "--skip-claude",
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=PACKAGE_ROOT,
            )

            self.assertIn("Would update AGENTS.md: no", result.stdout)
            self.assertIn("Would update CLAUDE.md: no", result.stdout)
            self.assertIn("Would write install manifest: no", result.stdout)
            self.assertIn("Refreshed registry: no", result.stdout)

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
            self.assert_core_skills_installed(target_root)

            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["name"], "skill-automation-package")
            self.assertNotIn(".claude/tests/test_skill_agent.py", payload["assets"])
            self.assert_manifest_lists_core_skills(payload)

            registry_payload = json.loads(
                (target_root / ".claude" / "skills" / "registry.json").read_text(encoding="utf-8")
            )
            registry_names = {item["name"] for item in registry_payload["skills"]}
            self.assertEqual(registry_names.intersection(CORE_SKILL_NAMES), set(CORE_SKILL_NAMES))

    def test_cli_reinstall_preserves_local_state_and_overwrites_packaged_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            target_root = Path(tempdir) / "target-repo"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "install.py"),
                    "--target",
                    str(target_root),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=PACKAGE_ROOT,
            )

            usage_path = target_root / ".claude" / "skills" / "usage.json"
            usage_path.parent.mkdir(parents=True, exist_ok=True)
            usage_text = (
                json.dumps(
                    {
                        "updated_at": "2026-04-01T12:00:00+00:00",
                        "skills": {
                            "team-workflow": {
                                "name": "team-workflow",
                                "last_action": "auto-reuse",
                                "reuse_count": 4,
                            }
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n"
            )
            usage_path.write_text(usage_text, encoding="utf-8")

            self.write_local_skill(
                target_root,
                name="team-workflow",
                title="Team Workflow",
                description="Handle shared team workflow updates.",
                summary="Handle shared team workflow updates.",
                category="docs",
            )

            installed_skill_agent = target_root / ".claude" / "tools" / "skill_agent.py"
            installed_skill_agent.parent.mkdir(parents=True, exist_ok=True)
            installed_skill_agent.write_text("# old skill agent sentinel\n", encoding="utf-8")

            installed_test = target_root / ".claude" / "tests" / "test_skill_agent.py"
            installed_test.parent.mkdir(parents=True, exist_ok=True)
            installed_test.write_text("# old test sentinel\n", encoding="utf-8")

            self.overwrite_packaged_core_skills(target_root)

            router_dir = target_root / ".claude" / "skills" / "project-skill-router"
            (router_dir / "obsolete.txt").write_text("stale package file\n", encoding="utf-8")

            (target_root / "AGENTS.md").write_text(
                (
                    "# AGENTS.md\n\n"
                    "Team intro.\n\n"
                    f"{install.AGENTS_MARKERS[0]}\n"
                    "Old agents block\n"
                    f"{install.AGENTS_MARKERS[1]}\n"
                    "\nAgent footer.\n"
                ),
                encoding="utf-8",
            )
            (target_root / "CLAUDE.md").write_text(
                (
                    "# CLAUDE.md\n\n"
                    "Claude intro.\n\n"
                    f"{install.CLAUDE_MARKERS[0]}\n"
                    "Old claude block\n"
                    f"{install.CLAUDE_MARKERS[1]}\n"
                    "\nClaude footer.\n"
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "install.py"),
                    "--target",
                    str(target_root),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=PACKAGE_ROOT,
            )

            self.assertIn("Updated AGENTS.md: yes", result.stdout)
            self.assertIn("Updated CLAUDE.md: yes", result.stdout)
            self.assertIn("Wrote install manifest: yes", result.stdout)
            self.assertIn("Refreshed registry: yes", result.stdout)

            packaged_skill_agent = (
                PACKAGE_ROOT / "assets" / ".claude" / "tools" / "skill_agent.py"
            ).read_text(encoding="utf-8")
            packaged_test = (
                PACKAGE_ROOT / "assets" / ".claude" / "tests" / "test_skill_agent.py"
            ).read_text(encoding="utf-8")
            self.assertEqual(installed_skill_agent.read_text(encoding="utf-8"), packaged_skill_agent)
            self.assertEqual(installed_test.read_text(encoding="utf-8"), packaged_test)
            self.assert_packaged_core_skills_match_assets(target_root)
            self.assertTrue((router_dir / "obsolete.txt").exists())
            self.assertEqual(usage_path.read_text(encoding="utf-8"), usage_text)
            self.assertTrue((target_root / ".claude" / "skills" / "team-workflow").exists())

            agents_text = (target_root / "AGENTS.md").read_text(encoding="utf-8")
            claude_text = (target_root / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertIn("Team intro.", agents_text)
            self.assertIn("Agent footer.", agents_text)
            self.assertNotIn("Old agents block", agents_text)
            self.assertEqual(agents_text.count(install.AGENTS_MARKERS[0]), 1)
            self.assertIn(
                (PACKAGE_ROOT / "templates" / "agents_block.md").read_text(encoding="utf-8").strip(),
                agents_text,
            )
            self.assertIn("Claude intro.", claude_text)
            self.assertIn("Claude footer.", claude_text)
            self.assertNotIn("Old claude block", claude_text)
            self.assertEqual(claude_text.count(install.CLAUDE_MARKERS[0]), 1)
            self.assertIn(
                (PACKAGE_ROOT / "templates" / "claude_block.md").read_text(encoding="utf-8").strip(),
                claude_text,
            )

            manifest_path = target_root / ".claude" / "skill-automation-package.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["version"], package_layout.load_package_layout().version)
            self.assertIn(".claude/tools/skill_agent.py", manifest["assets"])
            self.assertIn(".claude/tests/test_skill_agent.py", manifest["assets"])
            self.assert_manifest_lists_core_skills(manifest)

            registry_payload = json.loads(
                (target_root / ".claude" / "skills" / "registry.json").read_text(encoding="utf-8")
            )
            registry_names = {item["name"] for item in registry_payload["skills"]}
            self.assertEqual(registry_names.intersection(CORE_SKILL_NAMES), set(CORE_SKILL_NAMES))
            self.assertIn("team-workflow", registry_names)


if __name__ == "__main__":
    unittest.main()
