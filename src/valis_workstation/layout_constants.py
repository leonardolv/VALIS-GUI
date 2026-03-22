"""Layout design tokens for the VALIS Workstation splitter-based layout.

All numeric sizing values (pixels) are centralised here so that every
module references the same source of truth.  When migrating to a
different screen class (HiDPI, tablet, etc.) only this file needs to
change.
"""

from __future__ import annotations

# ── Left sidebar (Project + Slide Preview tabs) ────────────────
LEFT_SIDEBAR_MIN: int = 200
LEFT_SIDEBAR_INIT: int = 260
LEFT_SIDEBAR_MAX: int = 400

# ── Right sidebar (Properties + Layers tabs) ───────────────────
RIGHT_SIDEBAR_MIN: int = 240
RIGHT_SIDEBAR_INIT: int = 320
RIGHT_SIDEBAR_MAX: int = 480

# ── Central canvas (Napari viewer) ─────────────────────────────
CANVAS_MIN_W: int = 400
CANVAS_MIN_H: int = 300

# ── Bottom status / timeline panel ─────────────────────────────
TIMELINE_MIN_H: int = 160
TIMELINE_INIT_H: int = 240
TIMELINE_MAX_H: int = 500

# ── Splitter handles ───────────────────────────────────────────
SPLITTER_HANDLE_W: int = 6

# ── General spacing ────────────────────────────────────────────
GRID_SPACING: int = 8

# ── Minimum window size ────────────────────────────────────────
WINDOW_MIN_W: int = (
    LEFT_SIDEBAR_MIN + CANVAS_MIN_W + RIGHT_SIDEBAR_MIN + 2 * SPLITTER_HANDLE_W
)
WINDOW_MIN_H: int = (
    CANVAS_MIN_H + TIMELINE_MIN_H + SPLITTER_HANDLE_W + 80
)  # 80 for menus/status bar
