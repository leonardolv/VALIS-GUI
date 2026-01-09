from __future__ import annotations

import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Callable

import numpy as np

from valis_workstation.models.config import Config
from valis_workstation.utils.exceptions import UserVisibleError
from valis_workstation.models.config import Config

logger = logging.getLogger(__name__)


def build_registrar_kwargs(config: Config) -> dict:
    return {
        "max_image_dim_px": config.max_image_size,
        "do_rigid": config.rigid_registration,
        "non_rigid_registrar_cls": "default" if config.non_rigid_registration else None,
    }


def _valis_available() -> bool:
    return importlib.util.find_spec("valis") is not None


def _collect_transform_paths(output_dir: Path, slide_obj) -> dict:
    transforms_dir = output_dir / "transforms"
    transforms_dir.mkdir(parents=True, exist_ok=True)
    transform_payload: dict[str, str | list[list[float]]] = {}
    if slide_obj.M is not None:
        transform_payload["rigid_matrix"] = slide_obj.M.tolist()
    if slide_obj.stored_dxdy:
        transform_payload["bk_dxdy_path"] = slide_obj._bk_dxdy_f
        transform_payload["fwd_dxdy_path"] = slide_obj._fwd_dxdy_f
    elif slide_obj.bk_dxdy is not None:
        bk_path = transforms_dir / f"{slide_obj.name}_bk_dxdy.npy"
        fwd_path = transforms_dir / f"{slide_obj.name}_fwd_dxdy.npy"
        np.save(bk_path, slide_obj.bk_dxdy)
        np.save(fwd_path, slide_obj.fwd_dxdy)
        transform_payload["bk_dxdy_path"] = str(bk_path)
        transform_payload["fwd_dxdy_path"] = str(fwd_path)
    return transform_payload


def run_valis_pipeline(
    config: Config,
    slides: list[Path],
    output_dir: Path,
    progress_callback: Callable[[int], None] | None = None,
) -> dict:
    if not slides:
        raise UserVisibleError("No slides provided for registration.")
    if not _valis_available():
        raise UserVisibleError("VALIS library not available. Please install valis-wsi.")

    output_dir.mkdir(parents=True, exist_ok=True)
    slides = [Path(slide) for slide in slides]
    slide_paths = [str(slide) for slide in slides]

    valis_module = importlib.import_module("valis")
    valis_registration = importlib.import_module("valis.registration")
    valis_serial_non_rigid = importlib.import_module("valis.serial_non_rigid")
    logger.info("Starting VALIS pipeline with %d slides", len(slides))
    if progress_callback:
        progress_callback(10)

    registrar_kwargs = build_registrar_kwargs(config)
    if config.non_rigid_registration:
        registrar_kwargs["non_rigid_registrar_cls"] = valis_serial_non_rigid.SerialNonRigidRegistrar

    registrar = valis_registration.Valis(
        src_dir=str(slides[0].parent),
        dst_dir=str(output_dir),
        img_list=slide_paths,
        imgs_ordered=True,
        reference_img_f=slide_paths[0],
        **registrar_kwargs,
    )

    try:
        rigid_registrar, non_rigid_registrar, summary_df = registrar.register()
        if progress_callback:
            progress_callback(60)

        registered_dir = output_dir / "registered"
        registrar.warp_and_save_slides(
            str(registered_dir), non_rigid=config.non_rigid_registration
        )
        if progress_callback:
            progress_callback(90)
    except Exception as exc:
        logger.exception("VALIS pipeline failed")
        raise UserVisibleError(f"VALIS registration failed: {exc}") from exc

    summary_csv = output_dir / "summary.csv"
    summary_df.to_csv(summary_csv, index=False)

    slides_info: list[dict] = []
    for slide_path in slide_paths:
        slide_obj = registrar.get_slide(slide_path)
        slide_entry = {
            "name": slide_obj.name,
            "src": slide_obj.src_f,
            "registered_thumbnail": slide_obj.non_rigid_reg_img_f
            if config.non_rigid_registration
            else slide_obj.rigid_reg_img_f,
        }
        slide_entry.update(_collect_transform_paths(output_dir, slide_obj))
        slides_info.append(slide_entry)
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

    return {
        "output_dir": output_dir,
        "registered_dir": registered_dir,
        "summary_csv": summary_csv,
        "summary_df": summary_df,
        "slides": slides_info,
        "registrar": registrar,
        "rigid_registrar": rigid_registrar,
        "non_rigid_registrar": non_rigid_registrar,
    }
