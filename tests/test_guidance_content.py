from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
SUBTASK_ROUTING_PHRASE = 'auto "<sub-task>" --json'
CORE_HELPER_SKILLS = (
    "core-project-summary",
    "core-repo-structure-analysis",
    "core-docs-entrypoint-guidance",
    "core-change-summary",
)


class GuidanceContentTests(unittest.TestCase):
    def test_readme_clarifies_distribution_identity(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("Python-installed automation bundle", readme)
        self.assertIn("not an npm runtime package", readme)

    def test_router_skill_documents_subtask_routing(self) -> None:
        router_skill = (
            REPO_ROOT
            / "assets"
            / ".claude"
            / "skills"
            / "project-skill-router"
            / "SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertIn(SUBTASK_ROUTING_PHRASE, router_skill)

    def test_core_helper_skills_are_packaged_as_read_only_guidance(self) -> None:
        for skill_name in CORE_HELPER_SKILLS:
            skill_md = (
                REPO_ROOT / "assets" / ".claude" / "skills" / skill_name / "SKILL.md"
            ).read_text(encoding="utf-8")

            lowered = skill_md.lower()
            self.assertIn("read-only", lowered)
            self.assertIn("do not create, edit, or delete repository files", lowered)

    def test_installed_templates_document_subtask_routing(self) -> None:
        agents_block = (REPO_ROOT / "templates" / "agents_block.md").read_text(encoding="utf-8")
        claude_block = (REPO_ROOT / "templates" / "claude_block.md").read_text(encoding="utf-8")

        self.assertIn(SUBTASK_ROUTING_PHRASE, agents_block)
        self.assertIn(SUBTASK_ROUTING_PHRASE, claude_block)

    def test_readme_documents_recursive_skill_routing(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn(SUBTASK_ROUTING_PHRASE, readme)

    def test_readme_documents_example_outcomes_and_managed_blocks(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("## Example Outcomes", readme)
        self.assertIn("### Why `AGENTS.md` And `CLAUDE.md` Are Updated", readme)
        self.assertIn("five packaged core default skills", readme)

    def test_readme_documents_target_repo_git_hygiene(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("## Target Repo Git Hygiene", readme)
        self.assertIn(".claude/skills/registry.json", readme)
        self.assertIn(".claude/skills/usage.json", readme)
        self.assertIn("### Local-Only Automation", readme)

    def test_readme_separates_default_and_skip_docs_upgrade_paths(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("### Default Upgrade Path", readme)
        self.assertIn("### Upgrade Without Managed Docs", readme)
        self.assertLess(
            readme.index("### Default Upgrade Path"),
            readme.index("### Upgrade Without Managed Docs"),
        )
        self.assertIn("python3 scripts/install.py --target /path/to/target-repo\n```", readme)
        self.assertIn(
            "python3 scripts/install.py --target /path/to/target-repo --skip-agents --skip-claude",
            readme,
        )

    def test_readme_documents_nearest_sync_assets_detection(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("nearest matching parent", readme)
        self.assertIn("python3 scripts/sync_assets.py --source-root /path/to/source-repo", readme)

    def test_readme_verification_commands_avoid_python_bytecode(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn(
            "PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py'",
            readme,
        )
        self.assertIn(
            "PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s assets/.claude/tests -p 'test_*.py'",
            readme,
        )
        self.assertIn(
            "PYTHONDONTWRITEBYTECODE=1 python3 scripts/install.py --target /tmp/skill-automation-package-dry-run --dry-run",
            readme,
        )


if __name__ == "__main__":
    unittest.main()
