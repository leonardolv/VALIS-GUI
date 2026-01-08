from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from typing import Callable

from valis_workstation.models.config import Config

logger = logging.getLogger(__name__)


def build_registrar_kwargs(config: Config) -> dict:
    return {
        "rigid_registrar": config.rigid_registration,
        "non_rigid_registrar": config.non_rigid_registration,
        "max_image_size": config.max_image_size,
        "match_threshold": config.match_threshold,
        "use_gpu": config.use_gpu,
    }


def _valis_available() -> bool:
    return importlib.util.find_spec("valis") is not None


def run_valis_pipeline(
    config: Config,
    slides: list[Path],
    output_dir: Path,
    progress_callback: Callable[[int], None] | None = None,
) -> dict:
    if not slides:
        raise ValueError("No slides provided for registration.")

    output_dir.mkdir(parents=True, exist_ok=True)
    registrar_kwargs = build_registrar_kwargs(config)

    if not _valis_available():
        logger.info("VALIS library not available; running dry pipeline.")
        if progress_callback:
            progress_callback(100)
        return {"output_dir": output_dir, "slides": slides, "kwargs": registrar_kwargs}

    valis_module = importlib.import_module("valis")
    logger.info("Starting VALIS pipeline with %d slides", len(slides))

    if progress_callback:
        progress_callback(25)

    registrar = valis_module.Valis(
        slide_src=str(slides[0].parent),
        slide_dst=str(output_dir),
        **registrar_kwargs,
    )
    registrar.register()

    if progress_callback:
        progress_callback(100)

    return {"output_dir": output_dir, "registrar": registrar}
