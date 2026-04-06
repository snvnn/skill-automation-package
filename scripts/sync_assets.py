#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from package_layout import ASSETS_ROOT, PACKAGE_ROOT, PackageLayout, copy_assets, load_package_layout


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sync packaged assets from a source repository into assets/."
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        help=(
            "Repository root that contains the live .claude assets. When omitted, "
            "the script searches parent directories for a matching source tree."
        ),
    )
    return parser


def resolve_source_root(
    layout: PackageLayout,
    *,
    package_root: Path = PACKAGE_ROOT,
    explicit_root: Path | None = None,
) -> Path:
    if explicit_root is not None:
        source_root = explicit_root.resolve()
        ensure_source_root(layout, source_root)
        return source_root

    for candidate in package_root.parents:
        if source_root_matches(layout, candidate):
            return candidate

    raise FileNotFoundError(
        "Could not auto-detect a source root that contains the live .claude assets. "
        "Rerun with --source-root /path/to/source-repo."
    )


def ensure_source_root(layout: PackageLayout, source_root: Path) -> None:
    missing = missing_source_assets(layout, source_root)
    if not missing:
        return
    missing_paths = ", ".join(str(path) for path in missing)
    raise FileNotFoundError(
        f"Source root {source_root} is missing expected assets: {missing_paths}"
    )


def source_root_matches(layout: PackageLayout, source_root: Path) -> bool:
    return not missing_source_assets(layout, source_root)


def missing_source_assets(layout: PackageLayout, source_root: Path) -> list[Path]:
    return [
        relative_path
        for relative_path in layout.all_assets
        if not (source_root / relative_path).exists()
    ]


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    layout = load_package_layout()
    source_root = resolve_source_root(
        layout,
        explicit_root=args.source_root,
    )
    synced_files = copy_assets(
        source_root=source_root,
        destination_root=ASSETS_ROOT,
        asset_paths=layout.all_assets,
        executable_assets=layout.executable_assets,
    )
    print(f"Synced {len(synced_files)} files from {source_root} into {ASSETS_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
