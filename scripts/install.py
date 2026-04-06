#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from datetime import UTC
except ImportError:
    from datetime import timezone

    UTC = timezone.utc

from package_layout import (
    ASSETS_ROOT,
    PACKAGE_MANIFEST,
    PackageLayout,
    TEMPLATES_ROOT,
    copy_assets,
    load_package_layout,
)

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
    layout = load_package_layout(PACKAGE_MANIFEST)

    target = args.target.resolve()
    if not args.dry_run:
        target.mkdir(parents=True, exist_ok=True)

    selected_assets = layout.selected_assets(include_optional=not args.no_tests)
    copied_files = copy_assets(
        source_root=ASSETS_ROOT,
        destination_root=target,
        asset_paths=selected_assets,
        executable_assets=layout.executable_assets,
        dry_run=args.dry_run,
    )
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
        layout=layout,
        target_root=target,
        copied_files=copied_files,
        dry_run=args.dry_run,
    )

    refreshed = False
    if not args.dry_run:
        refresh_registry(target)
        refreshed = True

    agents_label = "Would update AGENTS.md" if args.dry_run else "Updated AGENTS.md"
    claude_label = "Would update CLAUDE.md" if args.dry_run else "Updated CLAUDE.md"
    manifest_label = "Would write install manifest" if args.dry_run else "Wrote install manifest"
    print(f"Installed skill automation package {layout.version} into {target}")
    print(f"Copied files: {len(copied_files)}")
    print(f"{agents_label}: {'yes' if wrote_agents else 'no'}")
    print(f"{claude_label}: {'yes' if wrote_claude else 'no'}")
    print(f"{manifest_label}: {'yes' if wrote_manifest else 'no'}")
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
    layout: PackageLayout,
    target_root: Path,
    copied_files: list[Path],
    dry_run: bool,
) -> bool:
    payload = {
        "name": layout.name,
        "version": layout.version,
        "installed_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "assets": [str(path.relative_to(target_root)) for path in copied_files],
    }
    if dry_run:
        return False
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
