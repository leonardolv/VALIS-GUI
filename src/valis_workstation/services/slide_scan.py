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


def slide_display_names(slides: Iterable[Path]) -> dict[Path, str]:
    """Map each slide to a unique label for the preview and reference lists.

    The label is the file stem, which is what VALIS uses to name a slide. When
    two slides share a stem (``HE.tif`` and ``HE.svs``, or ``A.tif`` and
    ``a.tif``) a stem-keyed list would show only one of them, so those slides
    are labelled with their full file name instead.
    """
    paths = [Path(s) for s in slides]
    counts: dict[str, int] = {}
    for path in paths:
        key = path.stem.lower()
        counts[key] = counts.get(key, 0) + 1
    return {
        path: (path.name if counts[path.stem.lower()] > 1 else path.stem)
        for path in paths
    }
