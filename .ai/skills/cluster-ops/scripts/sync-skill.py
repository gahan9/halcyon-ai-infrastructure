#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Sync the canonical cluster-ops Agent Skill to every agent/IDE skill home.

The Cursor userwide skill is the single source of truth. This mirrors it to the
other agent homes (Claude today; add more below) so one edit propagates to all
tools that read the Agent Skills open standard.

Usage:
    python sync-skill.py            # sync (overwrite targets)
    python sync-skill.py --dry-run  # show what would change, do nothing
    python sync-skill.py --check    # exit 1 if any target is out of sync (CI)
"""
from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

SKILL_NAME = "cluster-ops"
HOME = Path.home()

#: Single source of truth.
SOURCE = HOME / ".cursor" / "skills" / SKILL_NAME

#: Additional agent/IDE skill homes to mirror into. Extend as needed, e.g.
#: Codex/Copilot/Antigravity user skill directories once they standardize paths.
TARGETS = [
    HOME / ".claude" / "skills" / SKILL_NAME,
    Path(r"C:\Projects\project_template\.ai\skills") / SKILL_NAME,
]

#: Never mirror the sync tooling's own transient artifacts.
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")


def iter_files(root: Path) -> set[Path]:
    """Return skill file paths relative to ``root`` (excludes ignored)."""
    if not root.exists():
        return set()
    files: set[Path] = set()
    for path in root.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            files.add(path.relative_to(root))
    return files


def diff(source: Path, target: Path) -> tuple[list[Path], list[Path]]:
    """Return (to_copy, to_delete) relative paths to make target match source."""
    src_files = iter_files(source)
    tgt_files = iter_files(target)
    to_copy = [
        rel
        for rel in sorted(src_files)
        if rel not in tgt_files
        or not filecmp.cmp(source / rel, target / rel, shallow=False)
    ]
    to_delete = sorted(tgt_files - src_files)
    return to_copy, to_delete


def sync(target: Path, *, dry_run: bool) -> tuple[list[Path], list[Path]]:
    """Mirror SOURCE into ``target``. Returns the (copied, deleted) lists."""
    to_copy, to_delete = diff(SOURCE, target)
    if dry_run:
        return to_copy, to_delete
    for rel in to_copy:
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE / rel, dst)
    for rel in to_delete:
        (target / rel).unlink(missing_ok=True)
    return to_copy, to_delete


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="preview only")
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if any target differs (implies --dry-run)",
    )
    args = parser.parse_args()
    dry_run = args.dry_run or args.check

    if not SOURCE.exists():
        print(f"ERROR: source skill not found: {SOURCE}", file=sys.stderr)
        return 2

    drift = False
    for target in TARGETS:
        to_copy, to_delete = sync(target, dry_run=dry_run)
        if to_copy or to_delete:
            drift = True
            verb = "would update" if dry_run else "updated"
            print(f"{verb} {target}")
            for rel in to_copy:
                print(f"  + {rel.as_posix()}")
            for rel in to_delete:
                print(f"  - {rel.as_posix()}")
        else:
            print(f"in sync: {target}")

    if args.check and drift:
        print("CHECK FAILED: targets out of sync with source.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
