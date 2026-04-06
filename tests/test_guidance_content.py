from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SUBTASK_ROUTING_PHRASE = 'auto "<sub-task>" --json'


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


if __name__ == "__main__":
    unittest.main()
