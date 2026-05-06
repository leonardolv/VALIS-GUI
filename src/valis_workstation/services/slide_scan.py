from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

from valis_workstation.constants import SUPPORTED_EXTENSIONS, has_supported_extension

logger = logging.getLogger(__name__)


DEFAULT_EXTENSIONS = SUPPORTED_EXTENSIONS


def scan_slide_folder(
    folder: Path, extensions: Iterable[str] | None = None
) -> list[Path]:
    folder = Path(folder)
    if not folder.exists():
        logger.warning("Folder does not exist: %s", folder)
        return []
    if not folder.is_dir():
        logger.warning("Path is not a directory: %s", folder)
        return []

    valid_exts = {ext.lower() for ext in (extensions or DEFAULT_EXTENSIONS)}
    slides = [
        path
        for path in folder.iterdir()
        if path.is_file()
        and (has_supported_extension(path) if extensions is None else any(str(path).lower().endswith(ext) for ext in valid_exts))
    ]
    logger.info(
        "Scanned folder %s: found %d slides with extensions %s",
        folder,
        len(slides),
        valid_exts,
    )
    return sorted(slides, key=lambda p: p.name.lower())
