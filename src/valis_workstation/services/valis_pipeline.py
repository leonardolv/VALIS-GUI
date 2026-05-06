from __future__ import annotations

import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Callable

import numpy as np

from valis_workstation.constants import (
    CropModes,
    FeatureDetectors,
    ImageFormats,
    TransformerTypes,
)
from valis_workstation.models.config import Config
from valis_workstation.utils.exceptions import UserVisibleError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Feature detector mapping
# ---------------------------------------------------------------------------


def _get_feature_detector_cls(detector_key: str):
    """Return the VALIS ``FeatureDD`` **class** for *detector_key*.

    The class (not an instance) is returned so that ``Valis.__init__`` can
    instantiate it with the correct parameters internally.

    Returns ``None`` when the default detector (VGG) should be used.
    """
    try:
        from valis import feature_detectors  # type: ignore[import-untyped]
    except ImportError as exc:
        logger.warning("valis.feature_detectors not importable: %s", exc)
        return None

    _map: dict[str, type | None] = {
        FeatureDetectors.VGG: feature_detectors.VggFD,
        FeatureDetectors.KAZE: feature_detectors.KazeFD,
        FeatureDetectors.BRISK: feature_detectors.BriskFD,
        FeatureDetectors.ORB: feature_detectors.OrbFD,
        FeatureDetectors.AKAZE: feature_detectors.AkazeFD,
        FeatureDetectors.SUPERPOINT: feature_detectors.SuperPointFD,
        FeatureDetectors.DISK: feature_detectors.DiskFD,
    }

    # DeDoDe may not exist in older valis versions
    if hasattr(feature_detectors, "DeDoDeFD"):
        _map[FeatureDetectors.DEDODE] = feature_detectors.DeDoDeFD

    cls = _map.get(detector_key)
    if cls is None:
        logger.warning(
            "Unknown feature detector '%s' – falling back to VGG", detector_key
        )
        return None  # VALIS will use its own default (VGG)

    logger.info("Feature detector class: %s", cls.__name__)
    return cls


# ---------------------------------------------------------------------------
# Transformer mapping
# ---------------------------------------------------------------------------


def _get_transformer_cls(transformer_key: str):
    """Return the *uninstantiated* scikit-image transform **class**.

    ``transformer_cls`` in VALIS controls the rigid alignment model only.
    Non-rigid warping is handled separately.
    """
    try:
        from skimage import transform as skt  # type: ignore[import-untyped]
    except ImportError:
        logger.warning("scikit-image not available – using default SimilarityTransform")
        from skimage.transform import (
            SimilarityTransform,  # type: ignore[import-untyped]
        )

        return SimilarityTransform

    _map = {
        TransformerTypes.SIMILARITY: skt.SimilarityTransform,
        TransformerTypes.AFFINE: skt.AffineTransform,
        TransformerTypes.RIGID: skt.EuclideanTransform,
    }

    cls = _map.get(transformer_key, skt.SimilarityTransform)
    logger.info("Rigid transformer class: %s", cls.__name__)
    return cls


# ---------------------------------------------------------------------------
# Crop mode mapping
# ---------------------------------------------------------------------------


def _map_crop_mode(crop_mode: str) -> str | None:
    """Map the UI crop mode key to the string VALIS expects for ``crop``."""
    _map = {
        CropModes.REFERENCE: "reference",
        CropModes.ALL_OVERLAP: "overlap",
        CropModes.ALL: "all",
        CropModes.UNCHANGED: None,
    }
    return _map.get(crop_mode, "reference")


def build_registrar_kwargs(config: Config) -> dict:
    """Build keyword arguments for ``valis.registration.Valis()``.

    Every GUI option that has a corresponding VALIS constructor parameter is
    forwarded here.  Options that do *not* map to a VALIS parameter (e.g.
    output-format settings) are handled elsewhere.

    Parameters
    ----------
    config : Config
        Registration configuration populated from :class:`PropertiesDock`.

    Returns
    -------
    dict
        Keyword arguments suitable for ``Valis(**kwargs)``.
    """
    kwargs: dict = {
        "max_image_dim_px": config.max_image_size,
        "do_rigid": config.rigid_registration,
        "imgs_ordered": config.imgs_ordered,
    }

    # ── Non-rigid registrar ─────────────────────────────────────────
    if config.non_rigid_registration:
        try:
            from valis import non_rigid_registrars  # type: ignore[import-untyped]

            kwargs["non_rigid_registrar_cls"] = non_rigid_registrars.OpticalFlowWarper
        except ImportError:
            try:
                from valis import serial_non_rigid  # type: ignore[import-untyped]

                kwargs["non_rigid_registrar_cls"] = (
                    serial_non_rigid.SerialNonRigidRegistrar
                )
            except ImportError:
                logger.warning("No non-rigid registrar available – disabling non-rigid")
                kwargs["non_rigid_registrar_cls"] = None
    else:
        kwargs["non_rigid_registrar_cls"] = None

    # ── Feature detector (class, not instance) ──────────────────────
    fd_cls = _get_feature_detector_cls(config.feature_detector)
    if fd_cls is not None:
        kwargs["feature_detector_cls"] = fd_cls

    # ── Rigid transformer (class, not instance) ─────────────────────
    kwargs["transformer_cls"] = _get_transformer_cls(config.transformer_type)

    # ── Crop mode ───────────────────────────────────────────────────
    crop = _map_crop_mode(config.crop_mode)
    if crop is not None:
        kwargs["crop"] = crop

    # ── Tissue masks ────────────────────────────────────────────────
    kwargs["create_masks"] = config.use_masks

    # ── Denoise before rigid registration ───────────────────────────
    if config.denoise:
        kwargs["denoise_rigid"] = True

    # ── Micro-registration ──────────────────────────────────────────
    if config.micro_registration:
        try:
            from valis import micro_rigid_registrar  # type: ignore[import-untyped]

            kwargs["micro_rigid_registrar_cls"] = (
                micro_rigid_registrar.MicroRigidRegistrar
            )
            kwargs["micro_rigid_registrar_params"] = {
                "max_image_dim_px": config.micro_max_image_size,
            }
        except ImportError:
            logger.warning(
                "micro_rigid_registrar not importable – skipping micro-registration"
            )

    logger.info("Registrar kwargs: %s", kwargs)
    return kwargs


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
    stage_callback: Callable[[str], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> dict:
    """Run the VALIS registration pipeline.

    Parameters
    ----------
    config : Config
        Registration configuration from the GUI.
    slides : list[Path]
        Slide file paths to register.
    output_dir : Path
        Directory for registration output.
    progress_callback, cancel_check
        Optional callbacks for progress / cancellation.

    Returns
    -------
    dict
        Registration results including registrar, summary DataFrame, etc.

    Raises
    ------
    UserVisibleError
        On missing input, missing library, or pipeline failure.
    """
    if not slides:
        raise UserVisibleError("No slides provided for registration.")
    if not _valis_available():
        raise UserVisibleError("VALIS library not available. Please install valis-wsi.")

    output_dir.mkdir(parents=True, exist_ok=True)
    slides = [Path(s) for s in slides]
    slide_paths = [str(s) for s in slides]

    valis_registration = importlib.import_module("valis.registration")

    logger.info("Starting VALIS pipeline with %d slides", len(slides))
    if stage_callback:
        stage_callback("Preparing pipeline")
    if progress_callback:
        progress_callback(10)

    # ── Build registrar kwargs ─────────────────────────────────────
    registrar_kwargs = build_registrar_kwargs(config)

    # ── Determine reference image ──────────────────────────────────
    reference_img_f: str | None = None
    if config.reference_slide and config.reference_slide != "auto-detect":
        # GUI dropdown contains stem names (no extension).  Match by stem.
        for sp in slide_paths:
            if Path(sp).stem == config.reference_slide:
                reference_img_f = sp
                logger.info("Reference slide (by stem): %s", reference_img_f)
                break
        if reference_img_f is None:
            # Fallback: try full-name match
            for sp in slide_paths:
                if Path(sp).name == config.reference_slide:
                    reference_img_f = sp
                    logger.info("Reference slide (by name): %s", reference_img_f)
                    break

    if reference_img_f is None:
        logger.info("No explicit reference – VALIS will auto-select")

    # ── Initialise VALIS registrar ─────────────────────────────────
    init_kwargs: dict = {
        "src_dir": str(slides[0].parent),
        "dst_dir": str(output_dir),
        "img_list": slide_paths,
        **registrar_kwargs,
    }
    if reference_img_f is not None:
        init_kwargs["reference_img_f"] = reference_img_f

    registrar = valis_registration.Valis(**init_kwargs)

    # ── Run registration ───────────────────────────────────────────
    try:
        if cancel_check and cancel_check():
            raise UserVisibleError("Registration cancelled by user")

        if stage_callback:
            stage_callback("Feature detection and rigid alignment")
        logger.info("Starting registration process")
        rigid_registrar, non_rigid_registrar, summary_df = registrar.register()
        logger.info(
            "Registration completed – rigid: %s, non-rigid: %s",
            rigid_registrar is not None,
            non_rigid_registrar is not None,
        )
        if progress_callback:
            progress_callback(60)

        if cancel_check and cancel_check():
            raise UserVisibleError("Registration cancelled by user")

        # ── Save warped slides ─────────────────────────────────────
        save_kwargs: dict = {}
        if config.pyramid_levels is not None and config.pyramid_levels > 0:
            save_kwargs["pyramid"] = True
        if config.compression_level is not None:
            save_kwargs["compression"] = config.compression_level
        if config.tile_size is not None:
            save_kwargs["tile_wh"] = config.tile_size
        if config.image_quality is not None and config.image_quality > 0:
            save_kwargs["Q"] = config.image_quality

        registered_dir = output_dir / "registered"
        if stage_callback:
            stage_callback("Warping and saving registered slides")
        logger.info(
            "Warping and saving slides to %s with options: %s",
            registered_dir,
            save_kwargs,
        )

        registrar.warp_and_save_slides(
            str(registered_dir),
            non_rigid=config.non_rigid_registration,
            **save_kwargs,
        )

        logger.info("Slides saved successfully")
        if progress_callback:
            progress_callback(90)
    except UserVisibleError:
        raise
    except Exception as exc:
        logger.exception("VALIS pipeline failed")
        raise UserVisibleError(f"VALIS registration failed: {exc}") from exc

    # ── Persist summary CSV ────────────────────────────────────────
    summary_csv = output_dir / "summary.csv"
    if stage_callback:
        stage_callback("Finalizing outputs")
    summary_df.to_csv(summary_csv, index=False)
    logger.info("Summary CSV saved to %s", summary_csv)

    # ── Collect per-slide info ─────────────────────────────────────
    slides_info: list[dict] = []
    for sp in slide_paths:
        slide_obj = registrar.get_slide(sp)
        entry: dict = {
            "name": slide_obj.name,
            "src": slide_obj.src_f,
            "registered_thumbnail": (
                slide_obj.non_rigid_reg_img_f
                if config.non_rigid_registration
                else slide_obj.rigid_reg_img_f
            ),
        }
        entry.update(_collect_transform_paths(output_dir, slide_obj))
        slides_info.append(entry)

    logger.info("VALIS pipeline completed successfully")
    if progress_callback:
        progress_callback(100)

    return {
        "output_dir": output_dir,
        "registered_dir": registered_dir,
        "format": getattr(config, "image_format", ImageFormats.OME_TIFF),
        "summary_csv": summary_csv,
        "summary_df": summary_df,
        "slides": slides_info,
        "registrar": registrar,
        "rigid_registrar": rigid_registrar,
        "non_rigid_registrar": non_rigid_registrar,
    }
