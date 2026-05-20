"""Pre-registration validation utilities."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from valis_workstation.constants import has_supported_extension

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of pre-registration validation."""

    def __init__(
        self,
        is_valid: bool,
        warnings: list[str] | None = None,
        errors: list[str] | None = None,
    ):
        self.is_valid = is_valid
        self.warnings = warnings or []
        self.errors = errors or []

    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def has_errors(self) -> bool:
        return len(self.errors) > 0


def validate_slides(
    slides: list[Path], output_dir: Path, min_disk_space_gb: float = 10.0
) -> ValidationResult:
    """
    Validate slides before registration.

    Args:
        slides: List of slide file paths
        output_dir: Output directory for registration results
        min_disk_space_gb: Minimum required disk space in GB

    Returns:
        ValidationResult with errors and warnings
    """
    errors = []
    warnings = []

    # Check that all files exist
    missing_files = [s for s in slides if not s.exists()]
    if missing_files:
        errors.append(
            f"{len(missing_files)} slide file(s) not found: {', '.join(f.name for f in missing_files[:3])}"
        )

    # Check file formats (basic check - just extension)
    unsupported_files = [
        s for s in slides if not has_supported_extension(s)
    ]
    if unsupported_files:
        warnings.append(
            f"{len(unsupported_files)} file(s) may not be supported slide formats: "
            f"{', '.join(f.name for f in unsupported_files[:3])}"
        )

    # Calculate total size
    existing_slides = [s for s in slides if s.exists()]
    if existing_slides:
        total_size_bytes = 0
        for s in existing_slides:
            try:
                total_size_bytes += s.stat().st_size
            except OSError as exc:
                warnings.append(f"Could not read file size for {s.name}: {exc}")
        total_size_gb = total_size_bytes / (1024**3)

        logger.info(f"Total slide size: {total_size_gb:.2f} GB")

        # Estimate required disk space (slides + registration results ~2-3x)
        estimated_space_needed = total_size_gb * 3

        # Check available disk space
        try:
            disk_usage = shutil.disk_usage(
                output_dir.parent if output_dir.exists() else Path.cwd()
            )
            available_gb = disk_usage.free / (1024**3)

            logger.info(f"Available disk space: {available_gb:.2f} GB")
            logger.info(f"Estimated space needed: {estimated_space_needed:.2f} GB")

            if available_gb < min_disk_space_gb:
                errors.append(
                    f"Insufficient disk space: {available_gb:.1f} GB available, {min_disk_space_gb:.1f} GB minimum required"
                )
            elif available_gb < estimated_space_needed:
                warnings.append(
                    f"Low disk space: {available_gb:.1f} GB available, "
                    f"~{estimated_space_needed:.1f} GB estimated needed. "
                    f"Registration may fail if space runs out."
                )
        except Exception:
            logger.exception("Failed to check disk space")
            warnings.append("Could not verify available disk space")

        # Warn about very large slides
        large_slides = [
            s for s in existing_slides if s.stat().st_size > 5 * 1024**3
        ]  # > 5GB
        if large_slides:
            warnings.append(
                f"{len(large_slides)} very large slide(s) detected (>5GB). "
                f"Registration may require significant memory and time."
            )

    # Check if output path is a file (not a directory)
    if output_dir.exists() and not output_dir.is_dir():
        errors.append("Output path exists as a file, not a directory")

    # Check if output directory is writable
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        test_file = output_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        errors.append(f"Output directory is not writable: {str(e)}")

    is_valid = len(errors) == 0
    return ValidationResult(is_valid, warnings, errors)


def log_validation_result(
    result: ValidationResult, slide_count: int, output_dir: Path
) -> None:
    """Log a structured summary of validation results.

    Parameters
    ----------
    result : ValidationResult
        Validation result from validate_slides()
    slide_count : int
        Number of slides to be registered
    output_dir : Path
        Output directory path
    """
    logger.info(
        "Validation: %d slides, output → %s",
        slide_count,
        output_dir,
    )
    if result.warnings:
        for warning in result.warnings:
            logger.warning("  ⚠ %s", warning)
    if result.errors:
        for error in result.errors:
            logger.error("  ✗ %s", error)
    if result.is_valid:
        logger.info("Validation passed")
