"""DEPRECATED — use `python scripts/run_readiness.py --cycles 1` instead.

This script is kept only for backwards compatibility and delegates to run_readiness.py.
See CLAUDE.md "Scripts Policy" for details.
"""

from __future__ import annotations

import subprocess
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    warnings.warn(
        "run_one_cycle.py is deprecated. Use: python scripts/run_readiness.py --cycles 1",
        DeprecationWarning,
        stacklevel=2,
    )

    # Forward all args + force --cycles 1
    forward_args = []
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--cycles":
            i += 2  # skip --cycles N
            continue
        forward_args.append(args[i])
        i += 1

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_readiness.py"),
        "--cycles", "1",
        *forward_args,
    ]
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
