from __future__ import annotations

from pathlib import Path


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()
