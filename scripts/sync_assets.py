#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from package_layout import ASSETS_ROOT, copy_assets, load_package_layout

REPO_ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    layout = load_package_layout()
    synced_files = copy_assets(
        source_root=REPO_ROOT,
        destination_root=ASSETS_ROOT,
        asset_paths=layout.all_assets,
        executable_assets=layout.executable_assets,
    )
    print(f"Synced {len(synced_files)} files into {ASSETS_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
