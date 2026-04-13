"""DEPRECATED — use `python scripts/run_readiness.py --cycles N` instead.

This script is kept only for backwards compatibility and delegates to run_readiness.py.
See CLAUDE.md "Scripts Policy" for details.

run_bench.py had its own graph.invoke loop without Orchestrator and without P3
providers/fetch_pipeline — this caused the LLM parse 0-claims bug (D-120).
"""

from __future__ import annotations

import subprocess
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    warnings.warn(
        "run_bench.py is deprecated. Use: python scripts/run_readiness.py --cycles N",
        DeprecationWarning,
        stacklevel=2,
    )

    # Forward recognized args to run_readiness.py
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_readiness.py"),
    ]

    args = sys.argv[1:]
    skip_next = False
    for i, arg in enumerate(args):
        if skip_next:
            skip_next = False
            continue
        # --domain → not supported by run_readiness, drop with warning
        if arg == "--domain":
            warnings.warn("--domain is ignored in the deprecated path", stacklevel=2)
            skip_next = True
            continue
        # --dry-run → --evaluate-only
        if arg == "--dry-run":
            cmd.append("--evaluate-only")
            continue
        cmd.append(arg)

    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
