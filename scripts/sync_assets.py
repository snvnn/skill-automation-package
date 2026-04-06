#!/usr/bin/env python3
from __future__ import annotations

import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
ASSETS_ROOT = PACKAGE_ROOT / "assets"

SOURCE_TO_DEST = {
    REPO_ROOT / ".claude" / "tools" / "skill_agent.py": ASSETS_ROOT / ".claude" / "tools" / "skill_agent.py",
    REPO_ROOT / ".claude" / "skills" / "project-skill-router" / "SKILL.md": ASSETS_ROOT / ".claude" / "skills" / "project-skill-router" / "SKILL.md",
    REPO_ROOT / ".claude" / "skills" / "project-skill-router" / "skill.json": ASSETS_ROOT / ".claude" / "skills" / "project-skill-router" / "skill.json",
    REPO_ROOT / ".claude" / "tests" / "test_skill_agent.py": ASSETS_ROOT / ".claude" / "tests" / "test_skill_agent.py",
}


def main() -> int:
    for source, destination in SOURCE_TO_DEST.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    print(f"Synced {len(SOURCE_TO_DEST)} files into {ASSETS_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
