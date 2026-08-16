# SPDX-License-Identifier: MIT
"""Module entrypoint selector.

Prefer explicit ``python -m halcyon_sim.api`` or ``python -m halcyon_sim.worker``.
"""

from __future__ import annotations

import sys


def main() -> None:
    """Print usage when invoked as ``python -m halcyon_sim``."""

    print(
        "Use: python -m halcyon_sim.api  OR  python -m halcyon_sim.worker",
        file=sys.stderr,
    )
    raise SystemExit(2)


if __name__ == "__main__":
    main()
