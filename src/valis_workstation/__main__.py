"""Module entry point for VALIS Workstation."""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    # Ensure src/ is on sys.path so the package can be found
    src_path = str(repo_root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    from valis_workstation.app import run_app
    return run_app(repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
