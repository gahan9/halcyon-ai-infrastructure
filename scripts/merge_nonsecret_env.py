# SPDX-License-Identifier: MIT
"""Merge non-secret keys from deploy/staging.nonsecret.env into gitignored .env."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "deploy" / "staging.nonsecret.env"
DST = ROOT / ".env"

# Never write these from the non-secret file (commented templates only).
SECRET_KEYS = frozenset(
    {
        "DATABASE_URL",
        "VALKEY_URL",
        "SPACES_CREDENTIALS_JSON",
        "LLM_CREDENTIALS_JSON",
        "DIGITALOCEAN_TOKEN",
        "DIGITALOCEAN_ACCESS_ID",
        "DIGITALOCEAN_SECRET_KEY",
        "SPACES_ACCESS_ID",
        "SPACES_SECRET_KEY",
    }
)

ASSIGN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def parse_env(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        match = ASSIGN.match(line)
        if not match:
            continue
        key, value = match.group(1), match.group(2)
        if key in SECRET_KEYS:
            continue
        out[key] = value
    return out


def merge(existing: str, updates: dict[str, str]) -> str:
    lines = existing.splitlines()
    seen: set[str] = set()
    result: list[str] = []
    for line in lines:
        match = ASSIGN.match(line)
        if match and match.group(1) in updates and match.group(1) not in SECRET_KEYS:
            key = match.group(1)
            result.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            result.append(line)
    missing = [k for k in updates if k not in seen]
    if missing:
        if result and result[-1].strip():
            result.append("")
        result.append("# --- merged from deploy/staging.nonsecret.env ---")
        for key in missing:
            result.append(f"{key}={updates[key]}")
    return "\n".join(result) + "\n"


def main() -> int:
    if not SRC.is_file():
        print(f"missing {SRC}", file=sys.stderr)
        return 1
    updates = parse_env(SRC.read_text(encoding="utf-8"))
    if DST.is_file():
        merged = merge(DST.read_text(encoding="utf-8"), updates)
    else:
        example = ROOT / ".env.example"
        base = example.read_text(encoding="utf-8") if example.is_file() else ""
        merged = merge(base, updates)
        # Keep secret placeholders from example if present
    DST.write_text(merged, encoding="utf-8", newline="\n")
    print(f"Updated {DST} with {len(updates)} non-secret keys (secrets untouched).")
    print("Still required in .env (secrets): DATABASE_URL, VALKEY_URL,")
    print("  SPACES_CREDENTIALS_JSON; LLM_CREDENTIALS_JSON if using real inference.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
