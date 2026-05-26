#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
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
    iter_asset_files,
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

GITIGNORE_MARKERS = (
    "# SKILL-AUTOMATION:GITIGNORE:START",
    "# SKILL-AUTOMATION:GITIGNORE:END",
)

GITIGNORE_PATTERNS = {
    "generated": (
        "# Generated skill automation state",
        ".claude/skills/registry.json",
        ".claude/skills/usage.json",
        ".claude/skills/_archived/",
        ".claude/skill-automation-package.json",
        ".claude/**/__pycache__/",
        ".claude/**/*.pyc",
    ),
    "local-only": (
        "# Local-only skill automation install",
        ".claude/",
        "AGENTS.md",
        "CLAUDE.md",
    ),
}


@dataclass(frozen=True, slots=True)
class ManagedBlockPlan:
    changed: bool
    state: str
    updated: str


@dataclass(frozen=True, slots=True)
class PackageFilePreview:
    would_create: tuple[Path, ...]
    would_update: tuple[Path, ...]
    unchanged: tuple[Path, ...]
    stale: tuple[Path, ...]


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
    agents_plan = ManagedBlockPlan(changed=False, state="skipped", updated="")
    claude_plan = ManagedBlockPlan(changed=False, state="skipped", updated="")

    if not args.skip_agents:
        agents_plan = install_managed_block(
            target_file=target / "AGENTS.md",
            template_path=TEMPLATES_ROOT / "agents_block.md",
            markers=AGENTS_MARKERS,
            title="# AGENTS.md\n\n",
            dry_run=args.dry_run,
        )

    if not args.skip_claude:
        claude_plan = install_managed_block(
            target_file=target / "CLAUDE.md",
            template_path=TEMPLATES_ROOT / "claude_block.md",
            markers=CLAUDE_MARKERS,
            title="# CLAUDE.md\n\n",
            dry_run=args.dry_run,
        )

    gitignore_plan = install_gitignore_block(
        target_file=target / ".gitignore",
        mode=args.gitignore_mode,
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
    copied_label = "Would copy files" if args.dry_run else "Copied files"
    gitignore_label = "Would update .gitignore" if args.dry_run else "Updated .gitignore"
    print(f"Installed skill automation package {layout.version} into {target}")
    print(f"{copied_label}: {len(copied_files)}")
    print(f"{agents_label}: {'yes' if agents_plan.changed else 'no'}")
    print(f"{claude_label}: {'yes' if claude_plan.changed else 'no'}")
    print(f"{gitignore_label}: {'yes' if gitignore_plan.changed else 'no'}")
    print(f"{manifest_label}: {'yes' if wrote_manifest else 'no'}")
    print(f"Refreshed registry: {'yes' if refreshed else 'no'}")
    if args.dry_run:
        print_dry_run_preview(
            build_package_file_preview(
                layout=layout,
                target_root=target,
                asset_paths=selected_assets,
            ),
            agents_state=agents_plan.state,
            claude_state=claude_plan.state,
            gitignore_state=gitignore_plan.state,
        )
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
    parser.add_argument(
        "--gitignore-mode",
        choices=("generated", "local-only", "none"),
        default="generated",
        help=(
            "Manage a package-owned .gitignore block. `generated` ignores only "
            "generated state, `local-only` ignores the whole local install, and "
            "`none` leaves .gitignore untouched."
        ),
    )
    return parser


def install_managed_block(
    *,
    target_file: Path,
    template_path: Path,
    markers: tuple[str, str],
    title: str,
    dry_run: bool,
) -> ManagedBlockPlan:
    plan = build_managed_block_plan(
        target_file=target_file,
        template_path=template_path,
        markers=markers,
        title=title,
    )
    if not dry_run:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(plan.updated, encoding="utf-8")
    return plan


def build_managed_block_plan(
    *,
    target_file: Path,
    template_path: Path,
    markers: tuple[str, str],
    title: str,
) -> ManagedBlockPlan:
    block = template_path.read_text(encoding="utf-8").strip() + "\n"
    start_marker, end_marker = markers
    existing = target_file.read_text(encoding="utf-8") if target_file.exists() else ""
    updated = upsert_block(existing, block, start_marker, end_marker, title)
    state = classify_managed_block_state(existing, updated, start_marker, end_marker)
    return ManagedBlockPlan(changed=updated != existing, state=state, updated=updated)


def install_gitignore_block(
    *,
    target_file: Path,
    mode: str,
    dry_run: bool,
) -> ManagedBlockPlan:
    if mode == "none":
        return ManagedBlockPlan(changed=False, state="skipped", updated="")

    block = build_gitignore_block(mode)
    existing = target_file.read_text(encoding="utf-8") if target_file.exists() else ""
    updated = upsert_block(
        existing,
        block,
        GITIGNORE_MARKERS[0],
        GITIGNORE_MARKERS[1],
        "",
    )
    state = classify_managed_block_state(
        existing,
        updated,
        GITIGNORE_MARKERS[0],
        GITIGNORE_MARKERS[1],
    )

    if not dry_run:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(updated, encoding="utf-8")
    return ManagedBlockPlan(changed=updated != existing, state=state, updated=updated)


def build_gitignore_block(mode: str) -> str:
    patterns = GITIGNORE_PATTERNS[mode]
    return "\n".join([GITIGNORE_MARKERS[0], *patterns, GITIGNORE_MARKERS[1]]) + "\n"


def classify_managed_block_state(
    existing: str,
    updated: str,
    start_marker: str,
    end_marker: str,
) -> str:
    if updated == existing:
        return "unchanged"
    if not existing.strip():
        return "create"
    start_index = existing.find(start_marker)
    end_index = existing.find(end_marker)
    if start_index != -1 and end_index != -1 and end_index >= start_index:
        return "replace"
    return "append"


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


def build_package_file_preview(
    *,
    layout: PackageLayout,
    target_root: Path,
    asset_paths: list[Path],
) -> PackageFilePreview:
    current_assets: set[Path] = set()
    would_create: list[Path] = []
    would_update: list[Path] = []
    unchanged: list[Path] = []

    for source_path, relative_path in iter_asset_files(ASSETS_ROOT, asset_paths):
        current_assets.add(relative_path)
        target_path = target_root / relative_path
        if not target_path.exists():
            would_create.append(relative_path)
            continue
        if files_match(source_path, target_path):
            unchanged.append(relative_path)
            continue
        would_update.append(relative_path)

    stale = [
        path
        for path in read_previous_install_assets(target_root)
        if path not in current_assets and (target_root / path).exists()
    ]

    return PackageFilePreview(
        would_create=tuple(sorted(would_create)),
        would_update=tuple(sorted(would_update)),
        unchanged=tuple(sorted(unchanged)),
        stale=tuple(sorted(stale)),
    )


def files_match(source_path: Path, target_path: Path) -> bool:
    if not target_path.is_file():
        return False
    return source_path.read_bytes() == target_path.read_bytes()


def read_previous_install_assets(target_root: Path) -> list[Path]:
    manifest_path = target_root / ".claude" / "skill-automation-package.json"
    if not manifest_path.exists():
        return []
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    assets = payload.get("assets")
    if not isinstance(assets, list):
        return []

    previous: list[Path] = []
    for value in assets:
        if not isinstance(value, str):
            continue
        path = Path(value)
        if path.is_absolute():
            continue
        previous.append(path)
    return previous


def print_dry_run_preview(
    preview: PackageFilePreview,
    *,
    agents_state: str,
    claude_state: str,
    gitignore_state: str,
) -> None:
    print("Package file preview:")
    print_preview_paths("would create", preview.would_create)
    print_preview_paths("would update", preview.would_update)
    print_preview_paths("unchanged", preview.unchanged)
    print_preview_paths("previously installed but no longer shipped", preview.stale)
    print("Managed file preview:")
    print(f"  AGENTS.md: {agents_state}")
    print(f"  CLAUDE.md: {claude_state}")
    print(f"  .gitignore: {gitignore_state}")


def print_preview_paths(label: str, paths: tuple[Path, ...]) -> None:
    print(f"  {label}: {len(paths)}")
    for path in paths:
        print(f"    - {path}")


if __name__ == "__main__":
    raise SystemExit(main())
