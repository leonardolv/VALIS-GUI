from __future__ import annotations

from pathlib import Path
from typing import Iterable


DEFAULT_EXTENSIONS = {
    ".tif",
    ".tiff",
    ".svs",
    ".ndpi",
    ".png",
    ".jpg",
    ".jpeg",
}


def scan_slide_folder(folder: Path, extensions: Iterable[str] | None = None) -> list[Path]:
    folder = Path(folder)
    valid_exts = {ext.lower() for ext in (extensions or DEFAULT_EXTENSIONS)}
    slides = [
        path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in valid_exts
    ]
    return sorted(slides, key=lambda p: p.name.lower())
