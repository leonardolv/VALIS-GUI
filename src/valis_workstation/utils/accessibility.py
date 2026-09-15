"""
Accessibility settings: high-contrast theme and reduced-motion behaviour.

``ui/high_contrast`` and ``ui/reduced_motion`` (``settings_keys.py``) are
plain boolean ``QSettings`` keys toggled from Preferences -> User
Interface. Neither owns a single call site the way most Preferences
fields do -- "is the high-contrast theme applied" and "should this
transition run" are questions asked from several places (application
startup, the Preferences dialog itself when a toggle changes, and
individual animated widgets) -- so this module is the one place that
reads them back and applies their effect, mirroring
``app._ToolTipSuppressionFilter`` and ``performance._monitoring_enabled``:
both settings are re-read fresh on every call rather than cached, so a
Preferences change takes effect immediately without restarting the app.

Author: VALIS Workstation Team
Date: 2026-09-15
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)

# Package-relative, not repo_root-relative like the base theme below: this
# file ships inside the package itself (``styles/`` sits right next to this
# module's own ``valis_workstation`` parent), so it resolves correctly
# whether the app is run from a source checkout or an installed wheel, and
# callers don't need to thread a repo root through just to look it up.
_HIGH_CONTRAST_QSS = (
    Path(__file__).resolve().parent.parent / "styles" / "high_contrast_overrides.qss"
)

# The base theme, by contrast, is only ever loaded relative to repo_root
# (matching ``app._load_stylesheet``'s own resolution, which this mirrors
# rather than imports from: ``app.py`` imports ``main_window`` at module
# scope, and ``main_window`` needs to call back into this module when
# Preferences changes, so this module must not import ``app`` or the
# import would be circular).
_BASE_STYLESHEET_RELATIVE = (
    Path("src") / "valis_workstation" / "styles" / "adobe_dark.qss"
)

# Short enough to read as instantaneous -- well under a single frame at
# 60fps -- but still a real, positive duration: a ``QPropertyAnimation``
# with duration 0 still animates correctly in Qt, but keeping it positive
# means ``finished`` still fires asynchronously (on the next event-loop
# turn) rather than every reduced-motion call site needing its own
# "skip the animation and just set the end value directly" branch.
REDUCED_MOTION_DURATION_MS = 1


def _read_bool_setting(key: str, default: bool) -> bool:
    try:
        from PySide6.QtCore import QSettings

        return bool(QSettings("VALIS", "Workstation").value(key, default, type=bool))
    except Exception:
        logger.exception("Failed to read %s; assuming %s", key, default)
        return default


def high_contrast_enabled() -> bool:
    """Whether Preferences > "High contrast mode" is currently on."""
    return _read_bool_setting("ui/high_contrast", False)


def should_reduce_motion() -> bool:
    """Whether Preferences > "Reduce motion" is currently on.

    Call this from any UI transition built on a ``QPropertyAnimation``/
    ``QVariantAnimation`` (a fade, slide, etc.) and skip or shorten the
    animation when it returns ``True``. ``reduced_motion_duration_ms`` is
    the usual way to do that without repeating the same ``if`` at every
    call site.
    """
    return _read_bool_setting("ui/reduced_motion", False)


def reduced_motion_duration_ms(normal_duration_ms: int) -> int:
    """``normal_duration_ms``, unless reduced motion is on.

    When it is, returns ``REDUCED_MOTION_DURATION_MS`` instead -- pass the
    result straight to ``QPropertyAnimation.setDuration``.
    """
    if should_reduce_motion():
        return REDUCED_MOTION_DURATION_MS
    return normal_duration_ms


def base_stylesheet(repo_root: Path) -> str:
    """The base dark theme's CSS text, or ``""`` if the file isn't there.

    Same path resolution as ``app._load_stylesheet``, which now delegates
    to this function so there is exactly one implementation.
    """
    qss_path = repo_root / _BASE_STYLESHEET_RELATIVE
    if qss_path.exists():
        return qss_path.read_text(encoding="utf-8")
    return ""


def compose_stylesheet(base_css: str) -> str:
    """``base_css`` with the high-contrast overrides appended, when on.

    Appended, not substituted: Qt stylesheets resolve a tie between two
    rules of equal specificity in favour of whichever was parsed last, so
    appending after the base theme is enough to override its colours
    without duplicating every selector the base theme already defines.
    """
    if not high_contrast_enabled():
        return base_css
    if not _HIGH_CONTRAST_QSS.exists():
        logger.warning(
            "ui/high_contrast is on but %s is missing", _HIGH_CONTRAST_QSS
        )
        return base_css
    overrides = _HIGH_CONTRAST_QSS.read_text(encoding="utf-8")
    if not overrides:
        return base_css
    return f"{base_css}\n{overrides}" if base_css else overrides


def apply_theme(base_css: str, app: QApplication | None = None) -> None:
    """(Re-)apply the stylesheet for the current settings to ``app``.

    Called once at startup (``run_app``, with the freshly-loaded base
    theme) and again from ``MainWindow._on_preferences_changed`` whenever
    the Preferences dialog closes, so toggling "High contrast mode" is
    visible immediately -- no restart required, matching every other
    setting in this module.

    ``app`` defaults to ``QApplication.instance()``; a missing instance
    (e.g. a headless unit test that never constructed one) is a silent
    no-op rather than an error, since there is nothing to style.
    """
    if app is None:
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
    if app is None:
        return
    app.setStyleSheet(compose_stylesheet(base_css))
