#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Install skills from .ai/skills/ into user-level agent directories.

Every supported platform reads skills from `<config-dir>/skills/<name>/SKILL.md`,
so one installer serves all of them. Skills are linked by default (a directory
symlink on POSIX, a junction on Windows) so edits in this repo take effect
immediately; `--copy` produces a standalone copy for machines that cannot link
or for handing the skill to someone else.

Usage:
    python .ai/install-skills.py --list
    python .ai/install-skills.py --all --platform all
    python .ai/install-skills.py --skill clean-code,code-reviewer --platform claude
    python .ai/install-skills.py --all --platform cursor,codex --copy
    python .ai/install-skills.py --uninstall --skill clean-code --platform all

Platform directories can be overridden with `AI_SKILLS_<PLATFORM>_DIR`, for
example `AI_SKILLS_CLAUDE_DIR=/opt/claude/skills`.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / ".ai" / "skills"

# Marker dropped inside copied skills so --uninstall can tell what it owns.
MARKER_NAME = ".installed-by-ai-skills"

# Relative to the user's home directory. Every platform uses the same
# `<config>/skills/<name>/` convention.
PLATFORM_DIRS: dict[str, str] = {
    "claude": ".claude/skills",
    "cursor": ".cursor/skills",
    "codex": ".codex/skills",
    "copilot": ".copilot/skills",
    "antigravity": ".antigravity/skills",
}


def platform_dir(platform: str) -> Path:
    """Resolve the install directory for a platform, honouring env overrides."""
    override = os.environ.get(f"AI_SKILLS_{platform.upper()}_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / PLATFORM_DIRS[platform]


def available_skills() -> list[Path]:
    """Return every skill directory in the repo that has a SKILL.md."""
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(
        d for d in SKILLS_DIR.iterdir() if d.is_dir() and (d / "SKILL.md").is_file()
    )


def is_link(path: Path) -> bool:
    """Report whether path is a symlink or a Windows junction."""
    try:
        os.readlink(path)
    except OSError:
        return False
    return True


def make_link(target: Path, link: Path) -> bool:
    """Link target at link. Return True on success, False to fall back to copy."""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(target)],
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        link.symlink_to(target, target_is_directory=True)
        return True
    except OSError:
        return False


def remove_existing(dest: Path) -> None:
    """Remove an installed skill, whether it is a link or a copied tree."""
    if is_link(dest):
        # Never recurse into a link target; unlink the link itself.
        if sys.platform == "win32" and dest.is_dir():
            dest.rmdir()
        else:
            dest.unlink()
    else:
        shutil.rmtree(dest)


def owned_by_installer(dest: Path) -> bool:
    """Report whether this installer created dest (link, or copy with marker)."""
    return is_link(dest) or (dest / MARKER_NAME).is_file()


def install_one(
    skill: Path,
    dest_dir: Path,
    *,
    copy: bool,
    force: bool,
    overwrite_foreign: bool,
    dry_run: bool,
) -> str:
    """Install a single skill into dest_dir. Return a one-word status."""
    dest = dest_dir / skill.name

    if dest.exists() or is_link(dest):
        if not owned_by_installer(dest) and not overwrite_foreign:
            # Someone else's directory. Refuse rather than destroy their work.
            return "foreign"
        if not force and not overwrite_foreign:
            return "exists"
        if dry_run:
            return "replace"
        remove_existing(dest)
    elif dry_run:
        return "copy" if copy else "link"

    dest_dir.mkdir(parents=True, exist_ok=True)

    if not copy and make_link(skill, dest):
        return "link"

    shutil.copytree(skill, dest, dirs_exist_ok=True)
    (dest / MARKER_NAME).write_text(
        f"Installed from {skill.relative_to(REPO_ROOT).as_posix()}\n", encoding="utf-8"
    )
    return "copy"


def uninstall_one(
    skill_name: str, dest_dir: Path, *, overwrite_foreign: bool, dry_run: bool
) -> str:
    """Remove one installed skill from dest_dir. Return a one-word status."""
    dest = dest_dir / skill_name
    if not dest.exists() and not is_link(dest):
        return "absent"
    if not owned_by_installer(dest) and not overwrite_foreign:
        return "foreign"
    if dry_run:
        return "remove"
    remove_existing(dest)
    return "removed"


def resolve_platforms(requested: str) -> list[str]:
    """Expand a comma-separated platform list, where 'all' means every platform."""
    if requested.strip().lower() == "all":
        return list(PLATFORM_DIRS)
    names = [p.strip().lower() for p in requested.split(",") if p.strip()]
    unknown = [p for p in names if p not in PLATFORM_DIRS]
    if unknown:
        sys.exit(
            f"Unknown platform(s): {', '.join(unknown)}. "
            f"Choose from: {', '.join(PLATFORM_DIRS)}, all"
        )
    return names


def resolve_skills(requested: str | None, install_all: bool) -> list[Path]:
    """Expand a comma-separated skill list against what exists in the repo."""
    found = available_skills()
    if not found:
        sys.exit(f"No skills found in {SKILLS_DIR}")
    if install_all:
        return found

    by_name = {d.name: d for d in found}
    names = [s.strip() for s in (requested or "").split(",") if s.strip()]
    missing = [n for n in names if n not in by_name]
    if missing:
        sys.exit(
            f"Unknown skill(s): {', '.join(missing)}.\n"
            f"Run with --list to see what is available."
        )
    return [by_name[n] for n in names]


def print_listing() -> None:
    """Print available skills and detected platform directories."""
    skills = available_skills()
    print(f"Skills in {SKILLS_DIR.relative_to(REPO_ROOT).as_posix()} ({len(skills)}):")
    for skill in skills:
        print(f"  {skill.name}")

    print("\nPlatform directories:")
    for platform in PLATFORM_DIRS:
        target = platform_dir(platform)
        state = "found" if target.parent.is_dir() else "not installed"
        print(f"  {platform:<12} {target}  [{state}]")


def main() -> None:
    """Parse arguments and run the install or uninstall pass."""
    parser = argparse.ArgumentParser(
        description="Install .ai/skills/ into user-level agent directories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--list", action="store_true", help="show skills and platforms")
    parser.add_argument("--skill", help="comma-separated skill names")
    parser.add_argument("--all", action="store_true", help="every skill in .ai/skills/")
    parser.add_argument(
        "--platform",
        default="all",
        help=f"comma-separated: {', '.join(PLATFORM_DIRS)}, or all (default: all)",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="copy instead of linking (standalone, does not track repo edits)",
    )
    parser.add_argument(
        "--force", action="store_true", help="replace a skill this installer created"
    )
    parser.add_argument(
        "--overwrite-foreign",
        action="store_true",
        help="also replace or remove directories this installer did not create",
    )
    parser.add_argument("--uninstall", action="store_true", help="remove instead")
    parser.add_argument(
        "--create-missing",
        action="store_true",
        help="create platform directories that do not exist yet",
    )
    parser.add_argument("--dry-run", action="store_true", help="print, do not change")
    args = parser.parse_args()

    if args.list:
        print_listing()
        return

    if not args.all and not args.skill:
        parser.error("pass --all or --skill NAME[,NAME...] (or --list to see options)")

    platforms = resolve_platforms(args.platform)
    skills = resolve_skills(args.skill, args.all)
    verb = "Uninstalling" if args.uninstall else "Installing"
    mode = "copy" if args.copy else "link"
    prefix = "[DRY-RUN] " if args.dry_run else ""
    print(f"{prefix}{verb} {len(skills)} skill(s) for: {', '.join(platforms)}")
    if not args.uninstall:
        print(f"Mode: {mode}")

    tallies: dict[str, int] = {}
    for platform in platforms:
        dest_dir = platform_dir(platform)
        if not dest_dir.is_dir():
            parent_missing = not dest_dir.parent.is_dir()
            if parent_missing and not args.create_missing:
                print(f"\n{platform}: skipped - {dest_dir.parent} not found")
                tallies["skipped"] = tallies.get("skipped", 0) + len(skills)
                continue
            if not args.dry_run:
                dest_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{platform} -> {dest_dir}")
        for skill in skills:
            if args.uninstall:
                status = uninstall_one(
                    skill.name,
                    dest_dir,
                    overwrite_foreign=args.overwrite_foreign,
                    dry_run=args.dry_run,
                )
            else:
                status = install_one(
                    skill,
                    dest_dir,
                    copy=args.copy,
                    force=args.force,
                    overwrite_foreign=args.overwrite_foreign,
                    dry_run=args.dry_run,
                )
            tallies[status] = tallies.get(status, 0) + 1
            print(f"  {status:<9} {skill.name}")

    print("\nSummary: " + ", ".join(f"{v} {k}" for k, v in sorted(tallies.items())))
    if tallies.get("exists"):
        print("Re-run with --force to replace skills reported as 'exists'.")
    if tallies.get("foreign"):
        print(
            "'foreign' means a directory this installer did not create - most "
            "likely one you installed by hand. Move it aside, or re-run with "
            "--overwrite-foreign to replace it."
        )


if __name__ == "__main__":
    main()
