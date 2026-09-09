"""Service for merging registered slides into multi-channel images."""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Callable

from valis_workstation.utils.exceptions import UserVisibleError

logger = logging.getLogger(__name__)

# Matches valis.registration.DEFAULT_COMPRESSION's underlying value
# (pyvips.enums.ForeignTiffCompression.DEFLATE). Kept as a plain string here
# so this module never needs to import pyvips just to read a constant.
_DEFAULT_COMPRESSION = "deflate"

# Pixel formats this module knows the full-range ceiling for. Anything else
# (float, double, complex, ...) is left untouched by `_normalize_channels`
# rather than guessed at.
_FORMAT_MAX_VALUE = {
    "uchar": 255,
    "ushort": 65535,
}


def _normalize_channels(merged_img):
    """Linearly stretch each channel/band to the full range of its pixel format.

    Each band is stretched independently so its own observed minimum maps to
    0 and its own observed maximum maps to the format's maximum value -
    equivalent to per-channel min/max contrast stretching. This is what the
    "Normalize intensities" checkbox in ``MergeSlidesDialog`` has always
    claimed to do ("Recommended for better visualization"); the flag was
    previously read into ``merge_config["normalize"]`` and then never
    consulted anywhere in this module.

    Parameters
    ----------
    merged_img : pyvips.Image
        The merged, multi-band image returned by
        ``Valis.warp_and_merge_slides`` *before* it has been saved to disk.

    Returns
    -------
    pyvips.Image
        A new image with the same number of bands, each independently
        contrast-stretched. If ``merged_img``'s pixel format isn't one this
        function knows the ceiling for, or a band is already flat (constant
        value, so there is nothing to stretch), that band is returned
        unchanged rather than risking a division by zero or guessing at a
        format's range.
    """
    max_value = _FORMAT_MAX_VALUE.get(merged_img.format)
    if max_value is None:
        logger.warning(
            "Skipping channel normalization: unsupported pixel format %r "
            "(only %s are supported)",
            merged_img.format,
            sorted(_FORMAT_MAX_VALUE),
        )
        return merged_img

    stretched_bands = []
    for band_idx in range(merged_img.bands):
        band = merged_img[band_idx]
        band_min = band.min()
        band_max = band.max()
        if band_max <= band_min:
            stretched_bands.append(band)
            continue
        scale = max_value / (band_max - band_min)
        stretched_bands.append(((band - band_min) * scale).cast(merged_img.format))

    if len(stretched_bands) == 1:
        return stretched_bands[0]
    return stretched_bands[0].bandjoin(stretched_bands[1:])


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

    normalize = bool(merge_config.get("normalize"))

    try:
        if cancel_check and cancel_check():
            raise UserVisibleError("Merge cancelled by user")

        # Call VALIS warp_and_merge_slides
        logger.info("Starting slide merge operation")

        if normalize:
            # Normalizing rewrites pixel values before the image is saved,
            # so ask VALIS to build (and return) the merged image instead of
            # having it write to disk directly.
            unsaved_kwargs = dict(merge_kwargs)
            unsaved_kwargs["dst_f"] = None
            merged_img, _all_channel_names, ome_xml = registrar.warp_and_merge_slides(
                **unsaved_kwargs
            )

            if cancel_check and cancel_check():
                raise UserVisibleError("Merge cancelled by user")

            if progress_callback:
                progress_callback(60)

            merged_img = _normalize_channels(merged_img)

            slide_io = importlib.import_module("valis.slide_io")
            tile_wh = merge_kwargs.get("tile_wh")
            if tile_wh is None:
                ref_slide = registrar.get_ref_slide()
                tile_wh = slide_io.get_tile_wh(
                    reader=ref_slide.reader,
                    level=0,
                    out_shape_wh=(merged_img.width, merged_img.height),
                )

            slide_io.save_ome_tiff(
                merged_img,
                dst_f=str(output_file),
                ome_xml=ome_xml,
                tile_wh=tile_wh,
                compression=merge_kwargs.get("compression", _DEFAULT_COMPRESSION),
                Q=merge_kwargs.get("Q", 100),
                pyramid=merge_kwargs.get("pyramid", True),
            )
        else:
            registrar.warp_and_merge_slides(**merge_kwargs)

        if progress_callback:
            progress_callback(90)

        logger.info(f"Merge completed successfully: {output_file}")

        if progress_callback:
            progress_callback(100)

        return output_file

    except Exception as exc:
        logger.exception("Slide merge failed")
        raise UserVisibleError(f"Failed to merge slides: {exc}") from exc
