from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS_DIR))

import check_release_integrity


class ReleaseIntegrityTests(unittest.TestCase):
    def test_current_repository_passes_release_integrity_check(self) -> None:
        errors = check_release_integrity.check_release_integrity(
            check_release_integrity.REPO_ROOT
        )

        self.assertEqual(errors, [])

    def test_changelog_must_include_package_version(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            repo_root = Path(tempdir)
            self.write_minimal_repo(repo_root, version="9.9.9")
            (repo_root / "CHANGELOG.md").write_text("# Changelog\n\n## v1.0.0\n", encoding="utf-8")

            errors = check_release_integrity.check_release_integrity(repo_root)

            self.assertIn("CHANGELOG.md does not contain `## v9.9.9`", errors)

    def test_required_assets_must_be_in_npm_files_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            repo_root = Path(tempdir)
            package_data = self.write_minimal_repo(repo_root)
            package_data["files"].remove("assets/.claude/tools/skill_agent.py")
            (repo_root / "package.json").write_text(
                json.dumps(package_data, indent=2) + "\n",
                encoding="utf-8",
            )

            errors = check_release_integrity.check_release_integrity(repo_root)

            self.assertIn(
                "npm package files do not include required path: assets/.claude/tools/skill_agent.py",
                errors,
            )

    def write_minimal_repo(self, repo_root: Path, *, version: str = "1.2.3") -> dict[str, object]:
        package_data: dict[str, object] = {
            "name": "skill-automation-package",
            "version": version,
            "bin": {"skill-automation-package": "bin/skill-automation-package.js"},
            "files": [
                "bin/skill-automation-package.js",
                "scripts/install.py",
                "scripts/package_layout.py",
                "assets/.claude/tools/skill_agent.py",
                "templates/agents_block.md",
                "templates/claude_block.md",
                "README.md",
                "LICENSE",
            ],
            "engines": {"node": ">=18"},
            "managed_assets": [".claude/tools/skill_agent.py"],
            "optional_assets": [],
            "executable_assets": [".claude/tools/skill_agent.py"],
        }
        for file_path in package_data["files"]:
            path = repo_root / str(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("placeholder\n", encoding="utf-8")
        (repo_root / "package.json").write_text(
            json.dumps(package_data, indent=2) + "\n",
            encoding="utf-8",
        )
        (repo_root / "CHANGELOG.md").write_text(
            f"# Changelog\n\n## v{version}\n",
            encoding="utf-8",
        )
        return package_data


if __name__ == "__main__":
    unittest.main()
