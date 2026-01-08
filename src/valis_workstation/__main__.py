"""Module entry point for VALIS Workstation."""
from __future__ import annotations

from pathlib import Path

from valis_workstation.app import run_app


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    return run_app(repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
