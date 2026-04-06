#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
ASSETS_ROOT = PACKAGE_ROOT / "assets"
TEMPLATES_ROOT = PACKAGE_ROOT / "templates"
PACKAGE_MANIFEST = PACKAGE_ROOT / "package.json"

MANAGED_ASSETS = [
    Path(".claude/tools/skill_agent.py"),
    Path(".claude/skills/project-skill-router/SKILL.md"),
    Path(".claude/skills/project-skill-router/skill.json"),
]

OPTIONAL_TEST_ASSETS = [
    Path(".claude/tests/test_skill_agent.py"),
]

AGENTS_MARKERS = (
    "<!-- SKILL-AUTOMATION:AGENTS:START -->",
    "<!-- SKILL-AUTOMATION:AGENTS:END -->",
)

CLAUDE_MARKERS = (
    "<!-- SKILL-AUTOMATION:CLAUDE:START -->",
    "<!-- SKILL-AUTOMATION:CLAUDE:END -->",
)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    package = json.loads(PACKAGE_MANIFEST.read_text(encoding="utf-8"))

    target = args.target.resolve()
    target.mkdir(parents=True, exist_ok=True)

    assets = list(MANAGED_ASSETS)
    if not args.no_tests:
        assets.extend(OPTIONAL_TEST_ASSETS)

    copied_files = copy_assets(target=target, asset_paths=assets, dry_run=args.dry_run)
    wrote_agents = False
    wrote_claude = False

    if not args.skip_agents:
        wrote_agents = install_managed_block(
            target_file=target / "AGENTS.md",
            template_path=TEMPLATES_ROOT / "agents_block.md",
            markers=AGENTS_MARKERS,
            title="# AGENTS.md\n\n",
            dry_run=args.dry_run,
        )

    if not args.skip_claude:
        wrote_claude = install_managed_block(
            target_file=target / "CLAUDE.md",
            template_path=TEMPLATES_ROOT / "claude_block.md",
            markers=CLAUDE_MARKERS,
            title="# CLAUDE.md\n\n",
            dry_run=args.dry_run,
        )

    manifest_path = target / ".claude" / "skill-automation-package.json"
    wrote_manifest = write_install_manifest(
        manifest_path=manifest_path,
        package=package,
        assets=assets,
        dry_run=args.dry_run,
    )

    refreshed = False
    if not args.dry_run:
        refresh_registry(target)
        refreshed = True

    print(f"Installed skill automation package {package['version']} into {target}")
    print(f"Copied files: {len(copied_files)}")
    print(f"Updated AGENTS.md: {'yes' if wrote_agents else 'no'}")
    print(f"Updated CLAUDE.md: {'yes' if wrote_claude else 'no'}")
    print(f"Wrote install manifest: {'yes' if wrote_manifest else 'no'}")
    print(f"Refreshed registry: {'yes' if refreshed else 'no'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install the repo-local skill automation bundle into another directory."
    )
    parser.add_argument(
        "--target",
        type=Path,
        required=True,
        help="Target repository or directory that should receive the automation bundle.",
    )
    parser.add_argument(
        "--no-tests",
        action="store_true",
        help="Do not install the packaged verification test.",
    )
    parser.add_argument(
        "--skip-agents",
        action="store_true",
        help="Do not create or update AGENTS.md.",
    )
    parser.add_argument(
        "--skip-claude",
        action="store_true",
        help="Do not create or update CLAUDE.md.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the installation without writing files.",
    )
    return parser


def copy_assets(
    *,
    target: Path,
    asset_paths: list[Path],
    dry_run: bool,
) -> list[Path]:
    copied: list[Path] = []
    for relative_path in asset_paths:
        source = ASSETS_ROOT / relative_path
        destination = target / relative_path
        copied.append(destination)
        if dry_run:
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        if destination.name == "skill_agent.py":
            destination.chmod(0o755)
    return copied


def install_managed_block(
    *,
    target_file: Path,
    template_path: Path,
    markers: tuple[str, str],
    title: str,
    dry_run: bool,
) -> bool:
    block = template_path.read_text(encoding="utf-8").strip() + "\n"
    start_marker, end_marker = markers
    existing = target_file.read_text(encoding="utf-8") if target_file.exists() else ""
    updated = upsert_block(existing, block, start_marker, end_marker, title)

    if not dry_run:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(updated, encoding="utf-8")
    return updated != existing


def upsert_block(
    existing: str,
    block: str,
    start_marker: str,
    end_marker: str,
    title: str,
) -> str:
    if not existing.strip():
        return f"{title}{block}"

    start_index = existing.find(start_marker)
    end_index = existing.find(end_marker)
    if start_index != -1 and end_index != -1 and end_index >= start_index:
        end_index += len(end_marker)
        replacement = block.rstrip()
        return (existing[:start_index] + replacement + existing[end_index:]).rstrip() + "\n"

    base = existing.rstrip() + "\n\n"
    return base + block


def write_install_manifest(
    *,
    manifest_path: Path,
    package: dict[str, object],
    assets: list[Path],
    dry_run: bool,
) -> bool:
    payload = {
        "name": package["name"],
        "version": package["version"],
        "installed_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "assets": [str(path) for path in assets],
    }
    if not dry_run:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return True


def refresh_registry(target: Path) -> None:
    subprocess.run(
        [sys.executable, str(target / ".claude" / "tools" / "skill_agent.py"), "refresh"],
        check=True,
        cwd=target,
    )


if __name__ == "__main__":
    raise SystemExit(main())
