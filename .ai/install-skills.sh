#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
#
# Install skills from .ai/skills/ into user-level agent directories.
#
# Thin wrapper around .ai/install-skills.py so POSIX users do not need to
# remember the interpreter or the script path. Every argument is passed
# through unchanged. With no arguments it lists what is available.
#
# Examples:
#   ./.ai/install-skills.sh --list
#   ./.ai/install-skills.sh --all --platform claude,cursor
#   ./.ai/install-skills.sh --skill clean-code --platform all --copy

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
installer="${script_dir}/install-skills.py"

if [[ ! -f "${installer}" ]]; then
  echo "Cannot find ${installer}" >&2
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  python_bin=python3
elif command -v python >/dev/null 2>&1; then
  python_bin=python
else
  echo 'Python 3 is required but was not found on PATH.' >&2
  exit 1
fi

if [[ $# -eq 0 ]]; then
  exec "${python_bin}" "${installer}" --list
fi

exec "${python_bin}" "${installer}" "$@"
