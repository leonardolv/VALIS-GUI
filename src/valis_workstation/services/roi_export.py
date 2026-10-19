"""ROI crop export across registered slides (Qt-free, unit-testable)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping


def clamp_bbox(
    bbox: tuple[int, int, int, int], img_w: int, img_h: int
) -> tuple[int, int, int, int] | None:
    """Intersect an (x, y, w, h) box with an image of size img_w x img_h.

    Returns None when the box does not overlap the image at all.
    """
    x, y, w, h = bbox
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(img_w, x + w), min(img_h, y + h)
    if x1 <= x0 or y1 <= y0:
        return None
    return (x0, y0, x1 - x0, y1 - y0)


@dataclass
class ROIExportResult:
    """Outcome of a batch ROI export."""

    files: list[str] = field(default_factory=list)
    clipped: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)
    cancelled: bool = False

    def summary(self) -> str:
        parts = [f"Exported {len(self.files)} ROI crop(s)."]
        if self.clipped:
            parts.append(
                f"{len(self.clipped)} crop(s) were clipped to the slide bounds: "
                + ", ".join(self.clipped)
            )
        if self.failed:
            parts.append(
                f"{len(self.failed)} slide(s) failed: "
                + "; ".join(f"{n} ({e})" for n, e in self.failed.items())
            )
        if self.cancelled:
            parts.append("Export was cancelled before all slides were processed.")
        return "\n".join(parts)


def export_roi_crops(
    slides: Mapping[str, Any],
    bbox: tuple[int, int, int, int],
    out_dir: Path,
    ext: str,
    save_fn: Callable[[str, Any], None],
    on_progress: Callable[[int, str], None] | None = None,
    is_cancelled: Callable[[], bool] | None = None,
) -> ROIExportResult:
    """Crop ``bbox`` from every slide; one bad slide does not abort the rest.

    A box that extends past a slide is clipped to it (and reported); a box
    entirely outside a slide is reported as a failure for that slide only.
    """
    result = ROIExportResult()
    for i, (name, slide) in enumerate(slides.items()):
        if is_cancelled is not None and is_cancelled():
            result.cancelled = True
            break
        if on_progress is not None:
            on_progress(i, name)
        try:
            warped = slide.warp_slide(level=0)
            box = clamp_bbox(bbox, int(warped.width), int(warped.height))
            if box is None:
                raise ValueError(
                    f"ROI lies outside the slide ({warped.width}x{warped.height} px)"
                )
            if box != tuple(bbox):
                result.clipped.append(name)
            roi = warped.extract_area(*box)
            out_file = Path(out_dir) / f"{name}_ROI{ext}"
            save_fn(str(out_file), roi)
            result.files.append(str(out_file))
        except Exception as exc:  # noqa: BLE001 - report per slide
            result.failed[name] = str(exc)
    return result
