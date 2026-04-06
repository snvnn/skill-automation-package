from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
ASSETS_ROOT = PACKAGE_ROOT / "assets"
TEMPLATES_ROOT = PACKAGE_ROOT / "templates"
PACKAGE_MANIFEST = PACKAGE_ROOT / "package.json"
EXECUTABLE_FILE_MODE = 0o755


@dataclass(frozen=True, slots=True)
class PackageLayout:
    name: str
    version: str
    managed_assets: tuple[Path, ...]
    optional_assets: tuple[Path, ...]
    executable_assets: frozenset[Path]

    @property
    def all_assets(self) -> list[Path]:
        return [*self.managed_assets, *self.optional_assets]

    def selected_assets(self, *, include_optional: bool) -> list[Path]:
        if include_optional:
            return self.all_assets
        return list(self.managed_assets)


def load_package_layout(manifest_path: Path = PACKAGE_MANIFEST) -> PackageLayout:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    managed_assets = normalize_manifest_paths(
        payload.get("managed_assets") or payload.get("assets", [])
    )
    optional_assets = normalize_manifest_paths(payload.get("optional_assets", []))
    executable_assets = frozenset(normalize_manifest_paths(payload.get("executable_assets", [])))
    return PackageLayout(
        name=str(payload["name"]),
        version=str(payload["version"]),
        managed_assets=managed_assets,
        optional_assets=optional_assets,
        executable_assets=executable_assets,
    )


def normalize_manifest_paths(values: object) -> tuple[Path, ...]:
    if not isinstance(values, list):
        return ()
    normalized: list[Path] = []
    seen: set[Path] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        path = Path(value)
        if path in seen:
            continue
        normalized.append(path)
        seen.add(path)
    return tuple(normalized)


def iter_asset_files(source_root: Path, asset_paths: list[Path]) -> list[tuple[Path, Path]]:
    resolved_files: list[tuple[Path, Path]] = []
    seen: set[Path] = set()
    for relative_path in asset_paths:
        source_path = source_root / relative_path
        if not source_path.exists():
            raise FileNotFoundError(f"Missing asset: {source_path}")
        if source_path.is_dir():
            for candidate in sorted(source_path.rglob("*")):
                if not candidate.is_file():
                    continue
                asset_file = candidate.relative_to(source_root)
                if asset_file in seen:
                    continue
                resolved_files.append((candidate, asset_file))
                seen.add(asset_file)
            continue
        if relative_path in seen:
            continue
        resolved_files.append((source_path, relative_path))
        seen.add(relative_path)
    return resolved_files


def copy_assets(
    *,
    source_root: Path,
    destination_root: Path,
    asset_paths: list[Path],
    executable_assets: frozenset[Path],
    dry_run: bool = False,
) -> list[Path]:
    copied: list[Path] = []
    for source_path, relative_path in iter_asset_files(source_root, asset_paths):
        destination_path = destination_root / relative_path
        copied.append(destination_path)
        if dry_run:
            continue
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
        if relative_path in executable_assets:
            destination_path.chmod(EXECUTABLE_FILE_MODE)
    return copied
