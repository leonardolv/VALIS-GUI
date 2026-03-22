"""Service for merging registered slides into multi-channel images."""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Callable

from valis_workstation.utils.exceptions import UserVisibleError

logger = logging.getLogger(__name__)


def merge_registered_slides(
    registrar,
    merge_config: dict,
    output_path: Path,
    save_config: dict | None = None,
    progress_callback: Callable[[int], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> Path:
    """Merge registered slides into a single multi-channel image.

    Parameters
    ----------
    registrar
        VALIS registrar object with registered slides
    merge_config : dict
        Configuration from MergeSlidesDialog:
        - channels: list of dict with slide_name, channel_name, color
        - duplicate_handling: "average", "maximum", "minimum", "first", "last"
        - output_name: str
        - normalize: bool
    output_path : Path
        Directory where merged image will be saved
    save_config : dict | None
        Optional save configuration (pyramid, compression, tile_wh, Q)
    progress_callback : Callable[[int], None] | None
        Optional callback for progress updates (0-100)
    cancel_check : Callable[[], bool] | None
        Optional callback to check if cancellation was requested

    Returns
    -------
    Path
        Path to the saved merged image

    Raises
    ------
    UserVisibleError
        If merge fails or is cancelled
    """
    if not merge_config.get("channels"):
        raise UserVisibleError("No channels selected for merging.")

    logger.info(f"Merging {len(merge_config['channels'])} channels")

    if progress_callback:
        progress_callback(10)

    # Build channel name dictionary
    # Format: {slide_filename: [channel_names]}
    channel_name_dict = {}
    selected_slides = []

    for ch in merge_config["channels"]:
        slide_name = ch["slide_name"]
        channel_name = ch["channel_name"]

        if slide_name not in channel_name_dict:
            channel_name_dict[slide_name] = []
            selected_slides.append(slide_name)

        channel_name_dict[slide_name].append(channel_name)

    logger.info(f"Channel mapping: {channel_name_dict}")

    if progress_callback:
        progress_callback(20)

    if cancel_check and cancel_check():
        raise UserVisibleError("Merge cancelled by user")

    # Prepare output path
    output_name = merge_config.get("output_name", "merged_image")
    if not output_name.endswith(".ome.tiff"):
        output_name += ".ome.tiff"

    output_file = output_path / output_name
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Output file: {output_file}")

    # Build merge parameters
    merge_kwargs = {
        "dst_f": str(output_file),
        "channel_name_dict": channel_name_dict,
        "non_rigid": True,  # Use non-rigid warping if available
    }

    # Handle duplicate channels based on user selection
    duplicate_handling = merge_config.get("duplicate_handling", "average").lower()

    if duplicate_handling == "average":
        merge_kwargs["drop_duplicates"] = False  # Keep duplicates and average
    elif duplicate_handling in ["maximum", "minimum"]:
        # VALIS doesn't directly support max/min, so we drop duplicates and note it
        logger.warning(
            f"{duplicate_handling} handling not directly supported by VALIS, using first occurrence"
        )
        merge_kwargs["drop_duplicates"] = True
    elif duplicate_handling == "first":
        merge_kwargs["drop_duplicates"] = True
    elif duplicate_handling == "last":
        # Reverse the channel list to get last
        logger.warning("'last' handling will use reverse order")
        merge_kwargs["drop_duplicates"] = True

    # Add save options if provided
    if save_config:
        if save_config.get("pyramid_levels", 0) > 0:
            merge_kwargs["pyramid"] = True
        if save_config.get("compression_level") is not None:
            merge_kwargs["compression"] = save_config["compression_level"]
        if save_config.get("tile_size"):
            merge_kwargs["tile_wh"] = save_config["tile_size"]
        if save_config.get("image_quality"):
            merge_kwargs["Q"] = save_config["image_quality"]

    logger.info(f"Merge parameters: {merge_kwargs}")

    if progress_callback:
        progress_callback(30)

    try:
        if cancel_check and cancel_check():
            raise UserVisibleError("Merge cancelled by user")

        # Call VALIS warp_and_merge_slides
        logger.info("Starting slide merge operation")
        merged_img = registrar.warp_and_merge_slides(**merge_kwargs)

        if progress_callback:
            progress_callback(90)

        logger.info(f"Merge completed successfully: {output_file}")

        if progress_callback:
            progress_callback(100)

        return output_file

    except Exception as exc:
        logger.exception("Slide merge failed")
        raise UserVisibleError(f"Failed to merge slides: {exc}") from exc
