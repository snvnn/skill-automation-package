#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_JSON = REPO_ROOT / "package.json"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
REQUIRED_PACKAGE_FIELDS = (
    "name",
    "version",
    "bin",
    "files",
    "engines",
    "managed_assets",
    "optional_assets",
    "executable_assets",
)
BYTECODE_SUFFIXES = (".pyc", ".pyo")


def main() -> int:
    errors = check_release_integrity(REPO_ROOT)
    if errors:
        for error in errors:
            print(f"release integrity: {error}", file=sys.stderr)
        return 1

    print("release integrity: ok")
    return 0


def check_release_integrity(repo_root: Path) -> list[str]:
    package_json = repo_root / "package.json"
    errors: list[str] = []

    try:
        package_data = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"could not read package.json: {error}"]

    errors.extend(check_required_fields(package_data))
    errors.extend(check_changelog(package_data, repo_root / "CHANGELOG.md"))
    errors.extend(check_package_files(package_data, repo_root))
    errors.extend(check_tracked_bytecode(repo_root))
    return errors


def check_required_fields(package_data: dict[str, object]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_PACKAGE_FIELDS:
        if field not in package_data:
            errors.append(f"package.json is missing required field `{field}`")
    return errors


def check_changelog(package_data: dict[str, object], changelog_path: Path) -> list[str]:
    version = package_data.get("version")
    if not isinstance(version, str) or not version.strip():
        return ["package.json `version` must be a non-empty string"]

    try:
        changelog = changelog_path.read_text(encoding="utf-8")
    except OSError as error:
        return [f"could not read CHANGELOG.md: {error}"]

    heading = f"## v{version.strip()}"
    if heading not in changelog:
        return [f"CHANGELOG.md does not contain `{heading}`"]
    return []


def check_package_files(package_data: dict[str, object], repo_root: Path) -> list[str]:
    files = package_data.get("files")
    if not isinstance(files, list) or not all(isinstance(item, str) for item in files):
        return ["package.json `files` must be a list of strings"]

    file_entries = tuple(Path(item) for item in files)
    errors: list[str] = []

    for entry in file_entries:
        if not (repo_root / entry).exists():
            errors.append(f"package.json `files` entry does not exist: {entry}")

    required_paths = package_required_paths(package_data)
    for required_path in sorted(required_paths):
        if not package_files_include(required_path, file_entries):
            errors.append(f"npm package files do not include required path: {required_path}")

    for entry in file_entries:
        if is_bytecode_path(entry):
            errors.append(f"package.json `files` includes Python bytecode: {entry}")

    return errors


def package_required_paths(package_data: dict[str, object]) -> set[Path]:
    required = {
        Path("bin/skill-automation-package.js"),
        Path("scripts/install.py"),
        Path("scripts/package_layout.py"),
        Path("templates/agents_block.md"),
        Path("templates/claude_block.md"),
        Path("README.md"),
        Path("LICENSE"),
    }

    for field in ("managed_assets", "optional_assets", "executable_assets"):
        values = package_data.get(field)
        if isinstance(values, list):
            required.update(Path("assets") / value for value in values if isinstance(value, str))

    return required


def package_files_include(required_path: Path, file_entries: tuple[Path, ...]) -> bool:
    for entry in file_entries:
        if entry == required_path:
            return True
        try:
            required_path.relative_to(entry)
        except ValueError:
            continue
        return True
    return False


def check_tracked_bytecode(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return [f"could not inspect tracked files: {result.stderr.strip()}"]

    errors: list[str] = []
    for line in result.stdout.splitlines():
        path = Path(line)
        if is_bytecode_path(path):
            errors.append(f"tracked Python bytecode file found: {path}")
        if "__pycache__" in path.parts:
            errors.append(f"tracked Python cache directory content found: {path}")
    return errors


def is_bytecode_path(path: Path) -> bool:
    return path.suffix in BYTECODE_SUFFIXES or "__pycache__" in path.parts


if __name__ == "__main__":
    raise SystemExit(main())
