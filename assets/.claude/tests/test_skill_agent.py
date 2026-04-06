from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / ".claude" / "tools" / "skill_agent.py"

SPEC = importlib.util.spec_from_file_location("skill_agent", SCRIPT_PATH)
assert SPEC and SPEC.loader
skill_agent = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = skill_agent
SPEC.loader.exec_module(skill_agent)


class SkillAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        self.skills_dir = self.repo_root / ".claude" / "skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_discover_skills_reads_companion_metadata(self) -> None:
        self.write_skill(
            "pr-review",
            description=(
                "Review pull request feedback and summarize requested changes. "
                "Use when handling review comments."
            ),
            metadata={
                "category": "github",
                "summary": "Triage pull request review feedback.",
                "tags": ["pull-request", "reviews"],
                "triggers": ["address PR comments"],
                "steps": ["Read the latest review comments first."],
                "related_skills": ["project-skill-router"],
            },
        )

        records = skill_agent.discover_skills(self.skills_dir)

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.name, "pr-review")
        self.assertEqual(record.category, "github")
        self.assertEqual(record.tags, ["pull-request", "reviews"])
        self.assertEqual(record.related_skills, ["project-skill-router"])
        self.assertEqual(record.validation, [])
        self.assertEqual(record.examples, [])

    def test_search_prefers_trigger_overlap(self) -> None:
        self.write_skill(
            "ocr-debug",
            description="Debug OCR extraction issues. Use when OCR parsing fails.",
            metadata={
                "category": "ios",
                "summary": "Investigate OCR pipeline regressions.",
                "triggers": ["ocr parsing fails", "vision extraction error"],
            },
        )
        self.write_skill(
            "cloudkit-sync",
            description="Inspect CloudKit sync behavior. Use when sync is inconsistent.",
            metadata={
                "category": "ios",
                "summary": "Investigate CloudKit sync state.",
                "triggers": ["cloudkit sync bug"],
            },
        )

        records = skill_agent.discover_skills(self.skills_dir)
        matches = skill_agent.search_records(records, "vision extraction error", limit=2)

        self.assertGreaterEqual(len(matches), 1)
        self.assertEqual(matches[0][2].name, "ocr-debug")

    def test_cli_create_refresh_and_search(self) -> None:
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "create",
                "Skill Router",
                "--summary",
                "Route agents to the right reusable workflow",
                "--when",
                "an agent needs to find or create a repeatable local skill",
                "--category",
                "workflow",
                "--tag",
                "skills",
                "--trigger",
                "find the right skill",
                "--repo-root",
                str(self.repo_root),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        registry_path = self.skills_dir / "registry.json"
        self.assertTrue(registry_path.exists())
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        self.assertEqual(registry["skills"][0]["name"], "skill-router")

        search = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "search",
                "find the right skill",
                "--repo-root",
                str(self.repo_root),
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(search.stdout)
        self.assertEqual(payload[0]["name"], "skill-router")

    def test_bootstrap_dry_run_infers_rich_ios_skill(self) -> None:
        preview = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "bootstrap",
                "debug CloudKit sync regressions in the iOS app",
                "--repo-root",
                str(self.repo_root),
                "--dry-run",
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(preview.stdout)
        self.assertEqual(payload["category"], "ios")
        self.assertIn("cloudkit", payload["tags"])
        self.assertIn("## Validation", payload["markdown"])
        self.assertIn("## Example Requests", payload["markdown"])
        self.assertFalse((self.skills_dir / payload["name"]).exists())

    def test_auto_reuses_existing_skill_for_future_sessions(self) -> None:
        self.write_skill(
            "ocr-debug",
            description="Debug OCR extraction issues. Use when OCR parsing fails.",
            metadata={
                "category": "ios",
                "summary": "Investigate OCR pipeline regressions.",
                "tags": ["ocr", "vision"],
                "triggers": ["ocr parsing fails", "vision extraction error"],
            },
        )

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "auto",
                "vision extraction error on the OCR screen",
                "--repo-root",
                str(self.repo_root),
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["action"], "reuse")
        self.assertEqual(payload["match"]["name"], "ocr-debug")
        usage = json.loads((self.skills_dir / "usage.json").read_text(encoding="utf-8"))
        self.assertEqual(usage["skills"]["ocr-debug"]["reuse_count"], 1)
        self.assertEqual(usage["skills"]["ocr-debug"]["auto_hits"], 1)

    def test_auto_creates_new_skill_and_refreshes_registry(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "auto",
                "draft a reusable privacy policy update workflow",
                "--repo-root",
                str(self.repo_root),
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["action"], "created")
        created_name = payload["created_skill"]["name"]
        self.assertTrue((self.skills_dir / created_name / "SKILL.md").exists())

        registry = json.loads((self.skills_dir / "registry.json").read_text(encoding="utf-8"))
        registry_names = [item["name"] for item in registry["skills"]]
        self.assertIn(created_name, registry_names)
        usage = json.loads((self.skills_dir / "usage.json").read_text(encoding="utf-8"))
        self.assertEqual(usage["skills"][created_name]["create_count"], 1)

    def test_auto_does_not_reuse_router_for_domain_task(self) -> None:
        self.write_skill(
            "project-skill-router",
            description=(
                "Search, rank, scaffold, and refresh repo-local skills. "
                "Use when an agent is managing skills."
            ),
            metadata={
                "category": "workflow",
                "summary": "Route agents to the right local skill.",
                "tags": ["skills", "automation"],
                "triggers": ["automatically resolve or create a local skill"],
            },
        )

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "auto",
                "draft a reusable privacy policy update workflow",
                "--repo-root",
                str(self.repo_root),
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["action"], "created")
        self.assertNotEqual(payload["created_skill"]["name"], "project-skill-router")

    def test_usage_reports_candidate_for_old_unused_skill(self) -> None:
        old_timestamp = (datetime.now(UTC) - timedelta(days=60)).replace(microsecond=0).isoformat()
        self.write_skill(
            "dusty-skill",
            description="Handle a dusty workflow. Use when needed.",
            metadata={
                "category": "workflow",
                "summary": "Handle a dusty workflow.",
                "created_at": old_timestamp,
                "updated_at": old_timestamp,
            },
        )

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "usage",
                "--repo-root",
                str(self.repo_root),
                "--status",
                "candidate",
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(result.stdout)
        self.assertEqual(payload[0]["name"], "dusty-skill")
        self.assertEqual(payload[0]["status"], "candidate")

    def test_prune_apply_archives_candidate_skill(self) -> None:
        old_timestamp = (datetime.now(UTC) - timedelta(days=60)).replace(microsecond=0).isoformat()
        self.write_skill(
            "dusty-skill",
            description="Handle a dusty workflow. Use when needed.",
            metadata={
                "category": "workflow",
                "summary": "Handle a dusty workflow.",
                "created_at": old_timestamp,
                "updated_at": old_timestamp,
            },
        )

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "prune",
                "--repo-root",
                str(self.repo_root),
                "--apply",
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(result.stdout)
        self.assertEqual(payload[0]["name"], "dusty-skill")
        self.assertTrue((self.skills_dir / "_archived" / "dusty-skill" / "SKILL.md").exists())
        self.assertFalse((self.skills_dir / "dusty-skill").exists())
        registry = json.loads((self.skills_dir / "registry.json").read_text(encoding="utf-8"))
        self.assertEqual(registry["skills"], [])

    def write_skill(self, name: str, *, description: str, metadata: dict[str, object]) -> None:
        skill_dir = self.skills_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_md = (
            "---\n"
            f"name: {name}\n"
            f"description: {description}\n"
            "---\n\n"
            f"# {name.replace('-', ' ').title()}\n"
        )
        (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")
        (skill_dir / "skill.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
