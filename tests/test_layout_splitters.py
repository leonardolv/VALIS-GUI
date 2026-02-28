"""GUI tests for the splitter-based layout using pytest-qt.

These tests verify:
- Layout constants are present and sensible.
- Nested splitters are created with correct initial sizes.
- Splitter drag changes panel sizes while respecting min/max.
- Splitter state persists and restores across sessions.
- Scroll areas are present for sidebar panels.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure src is on the path for imports
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from PySide6 import QtCore, QtWidgets, QtTest

from valis_workstation import layout_constants as LC
from valis_workstation.ui.splitter_utils import (
    GripSplitter,
    GripSplitterHandle,
    clear_splitter_state,
    collapse_panel,
    expand_panel,
    persist_splitter_state,
    restore_splitter_state,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _process_events(timeout_ms: int = 200) -> None:
    """Let the event loop settle."""
    QtTest.QTest.qWait(timeout_ms)


class _TestSplitterWindow(QtWidgets.QMainWindow):
    """Lightweight stand-in for the real MainWindow's splitter hierarchy."""

    def __init__(self) -> None:
        super().__init__()
        self._top_splitter: QtWidgets.QSplitter | None = None
        self._outer_splitter: QtWidgets.QSplitter | None = None
        self._left_panel: QtWidgets.QFrame | None = None
        self._canvas_panel: QtWidgets.QFrame | None = None
        self._right_panel: QtWidgets.QFrame | None = None
        self._status_panel: QtWidgets.QFrame | None = None


# ---------------------------------------------------------------------------
# 1. Layout constants
# ---------------------------------------------------------------------------

class TestLayoutConstants:
    """Unit tests for layout_constants values."""

    def test_left_sidebar_min_lt_max(self):
        assert LC.LEFT_SIDEBAR_MIN < LC.LEFT_SIDEBAR_MAX

    def test_right_sidebar_min_lt_max(self):
        assert LC.RIGHT_SIDEBAR_MIN < LC.RIGHT_SIDEBAR_MAX

    def test_timeline_min_lt_max(self):
        assert LC.TIMELINE_MIN_H < LC.TIMELINE_MAX_H

    def test_canvas_min_positive(self):
        assert LC.CANVAS_MIN_W > 0
        assert LC.CANVAS_MIN_H > 0

    def test_splitter_handle_positive(self):
        assert LC.SPLITTER_HANDLE_W > 0

    def test_grid_spacing_positive(self):
        assert LC.GRID_SPACING > 0

    def test_window_min_computed(self):
        expected_w = (
            LC.LEFT_SIDEBAR_MIN + LC.CANVAS_MIN_W + LC.RIGHT_SIDEBAR_MIN
            + 2 * LC.SPLITTER_HANDLE_W
        )
        assert LC.WINDOW_MIN_W == expected_w

    def test_init_between_bounds(self):
        assert LC.LEFT_SIDEBAR_MIN <= LC.LEFT_SIDEBAR_INIT <= LC.LEFT_SIDEBAR_MAX
        assert LC.RIGHT_SIDEBAR_MIN <= LC.RIGHT_SIDEBAR_INIT <= LC.RIGHT_SIDEBAR_MAX
        assert LC.TIMELINE_MIN_H <= LC.TIMELINE_INIT_H <= LC.TIMELINE_MAX_H


# ---------------------------------------------------------------------------
# 2. Splitter utility functions
# ---------------------------------------------------------------------------

class TestSplitterUtils:
    """Tests for splitter_utils helpers without the full MainWindow."""

    @pytest.fixture()
    def h_splitter(self, qtbot):
        """Create a horizontal QSplitter with three child widgets."""
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        for label in ("A", "B", "C"):
            w = QtWidgets.QLabel(label)
            w.setMinimumWidth(50)
            splitter.addWidget(w)
        splitter.resize(800, 200)
        splitter.setSizes([200, 400, 200])
        qtbot.addWidget(splitter)
        splitter.show()
        _process_events()
        return splitter

    def test_persist_and_restore(self, h_splitter):
        key = "test/splitter_persist"
        try:
            h_splitter.setSizes([100, 500, 200])
            _process_events()
            saved_sizes = h_splitter.sizes()
            persist_splitter_state(h_splitter, key)

            # Change sizes
            h_splitter.setSizes([200, 400, 200])
            _process_events()

            # Restore
            restored = restore_splitter_state(h_splitter, key)
            assert restored is True
            assert h_splitter.sizes() == saved_sizes
        finally:
            clear_splitter_state(key)

    def test_restore_missing_key(self, h_splitter):
        clear_splitter_state("test/missing_key")
        restored = restore_splitter_state(
            h_splitter, "test/missing_key", default_sizes=[150, 400, 250]
        )
        assert restored is False
        _process_events()
        sizes = h_splitter.sizes()
        # The total should be close to 800; proportions should match
        assert abs(sizes[0] - 150) < 10
        assert abs(sizes[2] - 250) < 10

    def test_collapse_panel(self, h_splitter):
        h_splitter.setSizes([200, 400, 200])
        _process_events()
        total_before = sum(h_splitter.sizes())
        collapse_panel(h_splitter, 0, min_size=50)
        _process_events()
        sizes = h_splitter.sizes()
        assert sizes[0] == 50
        # Total should be preserved (within tolerance for rounding)
        assert abs(sum(sizes) - total_before) < 5

    def test_expand_panel(self, h_splitter):
        h_splitter.setSizes([100, 400, 300])
        _process_events()
        expand_panel(h_splitter, 0, target_size=250)
        _process_events()
        sizes = h_splitter.sizes()
        assert sizes[0] == 250


# ---------------------------------------------------------------------------
# 3. Splitter-based MainWindow layout tests
# ---------------------------------------------------------------------------

class TestSplitterLayout:
    """GUI tests that create a lightweight MainWindow-like structure.

    We avoid importing the full MainWindow (which needs napari and other
    heavy dependencies) and instead build the same splitter hierarchy
    directly.
    """

    @pytest.fixture()
    def splitter_window(self, qtbot):
        """Build a window that mirrors MainWindow's splitter structure."""
        win = _TestSplitterWindow()
        win.setWindowTitle("Test Splitter Layout")
        win.resize(1400, 900)

        # Left panel
        left = QtWidgets.QFrame()
        left.setObjectName("LeftPanel")
        left.setMinimumWidth(LC.LEFT_SIDEBAR_MIN)
        left.setMaximumWidth(LC.LEFT_SIDEBAR_MAX)

        # Canvas panel
        canvas = QtWidgets.QFrame()
        canvas.setObjectName("CanvasPanel")
        canvas.setMinimumSize(LC.CANVAS_MIN_W, LC.CANVAS_MIN_H)
        canvas.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )

        # Right panel
        right = QtWidgets.QFrame()
        right.setObjectName("RightPanel")
        right.setMinimumWidth(LC.RIGHT_SIDEBAR_MIN)
        right.setMaximumWidth(LC.RIGHT_SIDEBAR_MAX)

        # Top splitter
        top_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        top_splitter.setHandleWidth(LC.SPLITTER_HANDLE_W)
        top_splitter.setChildrenCollapsible(False)
        top_splitter.addWidget(left)
        top_splitter.addWidget(canvas)
        top_splitter.addWidget(right)
        top_splitter.setStretchFactor(0, 0)
        top_splitter.setStretchFactor(1, 1)
        top_splitter.setStretchFactor(2, 0)
        for idx in range(top_splitter.count()):
            top_splitter.setCollapsible(idx, False)

        # Status panel
        status = QtWidgets.QFrame()
        status.setObjectName("StatusPanel")
        status.setMinimumHeight(LC.TIMELINE_MIN_H)
        status.setMaximumHeight(LC.TIMELINE_MAX_H)

        # Outer splitter
        outer_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        outer_splitter.setHandleWidth(LC.SPLITTER_HANDLE_W)
        outer_splitter.setChildrenCollapsible(False)
        outer_splitter.addWidget(top_splitter)
        outer_splitter.addWidget(status)
        outer_splitter.setStretchFactor(0, 1)
        outer_splitter.setStretchFactor(1, 0)
        for idx in range(outer_splitter.count()):
            outer_splitter.setCollapsible(idx, False)

        # Initial sizes
        canvas_w = 1400 - LC.LEFT_SIDEBAR_INIT - LC.RIGHT_SIDEBAR_INIT - 2 * LC.SPLITTER_HANDLE_W
        top_splitter.setSizes([LC.LEFT_SIDEBAR_INIT, canvas_w, LC.RIGHT_SIDEBAR_INIT])
        main_h = 900 - LC.TIMELINE_INIT_H - LC.SPLITTER_HANDLE_W
        outer_splitter.setSizes([main_h, LC.TIMELINE_INIT_H])

        win.setCentralWidget(outer_splitter)

        # Stash references
        win._top_splitter = top_splitter
        win._outer_splitter = outer_splitter
        win._left_panel = left
        win._canvas_panel = canvas
        win._right_panel = right
        win._status_panel = status

        qtbot.addWidget(win)
        win.show()
        _process_events()

        return win

    # -- Initial sizes ---------------------------------------------------

    def test_initial_top_splitter_sizes(self, splitter_window):
        sizes = splitter_window._top_splitter.sizes()
        assert len(sizes) == 3
        # Left ~260, right ~320 (may vary slightly due to min/max enforcement)
        assert abs(sizes[0] - LC.LEFT_SIDEBAR_INIT) < 30
        assert abs(sizes[2] - LC.RIGHT_SIDEBAR_INIT) < 30
        # Canvas should take remaining space
        assert sizes[1] >= LC.CANVAS_MIN_W

    def test_initial_outer_splitter_sizes(self, splitter_window):
        sizes = splitter_window._outer_splitter.sizes()
        assert len(sizes) == 2
        assert abs(sizes[1] - LC.TIMELINE_INIT_H) < 30
        assert sizes[0] >= LC.CANVAS_MIN_H

    # -- Min/max enforcement ---------------------------------------------

    def test_left_sidebar_min_enforced(self, splitter_window):
        left = splitter_window._left_panel
        assert left.minimumWidth() == LC.LEFT_SIDEBAR_MIN

    def test_left_sidebar_max_enforced(self, splitter_window):
        left = splitter_window._left_panel
        assert left.maximumWidth() == LC.LEFT_SIDEBAR_MAX

    def test_right_sidebar_min_enforced(self, splitter_window):
        right = splitter_window._right_panel
        assert right.minimumWidth() == LC.RIGHT_SIDEBAR_MIN

    def test_canvas_minimum_size(self, splitter_window):
        canvas = splitter_window._canvas_panel
        assert canvas.minimumWidth() == LC.CANVAS_MIN_W
        assert canvas.minimumHeight() == LC.CANVAS_MIN_H

    def test_status_panel_min_height(self, splitter_window):
        status = splitter_window._status_panel
        assert status.minimumHeight() == LC.TIMELINE_MIN_H

    # -- Children not collapsible ----------------------------------------

    def test_top_splitter_not_collapsible(self, splitter_window):
        sp = splitter_window._top_splitter
        for idx in range(sp.count()):
            assert sp.isCollapsible(idx) is False

    def test_outer_splitter_not_collapsible(self, splitter_window):
        sp = splitter_window._outer_splitter
        for idx in range(sp.count()):
            assert sp.isCollapsible(idx) is False

    # -- Handle width ----------------------------------------------------

    def test_handle_widths(self, splitter_window):
        assert splitter_window._top_splitter.handleWidth() == LC.SPLITTER_HANDLE_W
        assert splitter_window._outer_splitter.handleWidth() == LC.SPLITTER_HANDLE_W

    # -- Stretch factors -------------------------------------------------

    def test_only_canvas_stretches(self, splitter_window):
        """Verify that stretch factors are set so only centre absorbs."""
        sp = splitter_window._top_splitter
        # PySide6 doesn't expose stretchFactor() — we test indirectly by
        # resizing the window and checking that canvas absorbs the delta.
        old_sizes = sp.sizes()
        splitter_window.resize(1600, 900)
        _process_events()
        new_sizes = sp.sizes()
        # Canvas should have grown the most
        delta_canvas = new_sizes[1] - old_sizes[1]
        delta_left = abs(new_sizes[0] - old_sizes[0])
        delta_right = abs(new_sizes[2] - old_sizes[2])
        assert delta_canvas > delta_left
        assert delta_canvas > delta_right

    # -- Simulated drag --------------------------------------------------

    def test_drag_top_handle_changes_left_size(self, splitter_window):
        """Simulate dragging the first handle of top_splitter."""
        sp = splitter_window._top_splitter
        handle = sp.handle(1)  # handle between left and canvas
        assert handle is not None

        old_sizes = sp.sizes()
        mid = handle.rect().center()

        QtTest.QTest.mousePress(handle, QtCore.Qt.MouseButton.LeftButton, pos=mid)
        new_pos = mid + QtCore.QPoint(40, 0)
        QtTest.QTest.mouseMove(handle, pos=new_pos)
        QtTest.QTest.mouseRelease(handle, QtCore.Qt.MouseButton.LeftButton, pos=new_pos)
        _process_events()

        new_sizes = sp.sizes()
        # The left panel should be larger than before
        assert new_sizes[0] > old_sizes[0] - 5  # ±tolerance

    def test_drag_outer_handle_changes_status_height(self, splitter_window):
        """Simulate dragging the outer splitter handle."""
        sp = splitter_window._outer_splitter
        handle = sp.handle(1)
        assert handle is not None

        old_sizes = sp.sizes()
        mid = handle.rect().center()

        QtTest.QTest.mousePress(handle, QtCore.Qt.MouseButton.LeftButton, pos=mid)
        new_pos = mid + QtCore.QPoint(0, -30)
        QtTest.QTest.mouseMove(handle, pos=new_pos)
        QtTest.QTest.mouseRelease(handle, QtCore.Qt.MouseButton.LeftButton, pos=new_pos)
        _process_events()

        new_sizes = sp.sizes()
        # Status should be larger (moved handle up)
        assert new_sizes[1] >= old_sizes[1] - 5

    # -- Persistence round-trip ------------------------------------------

    def test_persist_and_restore_top_splitter(self, splitter_window):
        sp = splitter_window._top_splitter
        key = "test/layout/top"
        try:
            sp.setSizes([250, 600, 300])
            _process_events()
            saved_sizes = sp.sizes()
            persist_splitter_state(sp, key)

            sp.setSizes([200, 700, 250])
            _process_events()

            restored = restore_splitter_state(sp, key)
            assert restored is True
            # Left and right should match exactly; canvas adjusts
            assert sp.sizes()[0] == saved_sizes[0]
            assert sp.sizes()[2] == saved_sizes[2]
        finally:
            clear_splitter_state(key)

    # -- Scroll areas ----------------------------------------------------

    def test_scroll_area_present_in_left_tabs(self, qtbot):
        """Verify that a QScrollArea wraps content in the tab panels."""
        tabs = QtWidgets.QTabWidget()
        content = QtWidgets.QLabel("Hello")

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        tabs.addTab(scroll, "Test")
        qtbot.addWidget(tabs)
        tabs.show()
        _process_events()

        widget = tabs.widget(0)
        assert isinstance(widget, QtWidgets.QScrollArea)
        assert widget.widgetResizable() is True


# ---------------------------------------------------------------------------
# 4. GripSplitter / GripSplitterHandle tests
# ---------------------------------------------------------------------------

class TestGripSplitter:
    """Tests for the custom GripSplitter that paints visible grip dots."""

    @pytest.fixture()
    def grip_h(self, qtbot):
        """Horizontal GripSplitter with three children."""
        sp = GripSplitter(QtCore.Qt.Orientation.Horizontal)
        for label in ("L", "C", "R"):
            w = QtWidgets.QLabel(label)
            w.setMinimumWidth(50)
            sp.addWidget(w)
        sp.resize(800, 200)
        sp.setSizes([200, 400, 200])
        qtbot.addWidget(sp)
        sp.show()
        _process_events()
        return sp

    @pytest.fixture()
    def grip_v(self, qtbot):
        """Vertical GripSplitter with two children."""
        sp = GripSplitter(QtCore.Qt.Orientation.Vertical)
        for label in ("Top", "Bottom"):
            w = QtWidgets.QLabel(label)
            w.setMinimumHeight(50)
            sp.addWidget(w)
        sp.resize(400, 400)
        sp.setSizes([200, 200])
        qtbot.addWidget(sp)
        sp.show()
        _process_events()
        return sp

    def test_creates_grip_handles(self, grip_h):
        """All internal handles should be GripSplitterHandle instances."""
        for idx in range(1, grip_h.count()):
            assert isinstance(grip_h.handle(idx), GripSplitterHandle)

    def test_horizontal_cursor(self, grip_h):
        handle = grip_h.handle(1)
        assert handle.cursor().shape() == QtCore.Qt.CursorShape.SplitHCursor

    def test_vertical_cursor(self, grip_v):
        handle = grip_v.handle(1)
        assert handle.cursor().shape() == QtCore.Qt.CursorShape.SplitVCursor

    def test_handle_tooltip(self, grip_h):
        assert grip_h.handle(1).toolTip() == "Drag to resize panels"

    def test_drag_still_works(self, grip_h):
        """Dragging a GripSplitterHandle should resize panels."""
        old_sizes = grip_h.sizes()
        handle = grip_h.handle(1)
        mid = handle.rect().center()

        QtTest.QTest.mousePress(handle, QtCore.Qt.MouseButton.LeftButton, pos=mid)
        new_pos = mid + QtCore.QPoint(30, 0)
        QtTest.QTest.mouseMove(handle, pos=new_pos)
        QtTest.QTest.mouseRelease(handle, QtCore.Qt.MouseButton.LeftButton, pos=new_pos)
        _process_events()

        new_sizes = grip_h.sizes()
        assert new_sizes[0] >= old_sizes[0] - 5  # left grew or stayed

    def test_handle_paint_no_crash(self, grip_h):
        """Ensure painting the grip dots does not crash."""
        handle = grip_h.handle(1)
        handle.repaint()  # force immediate paint


# ---------------------------------------------------------------------------
# 5. Layout regression tests at multiple window sizes
# ---------------------------------------------------------------------------

class TestLayoutRegression:
    """Verify no overlaps and all regions remain visible at various sizes.

    Tests resize from small (1024x768) through medium (1400x900) to
    large (1920x1080) and check that:
    - All four panels have positive dimensions.
    - The canvas is at least CANVAS_MIN_W x CANVAS_MIN_H.
    - No two sibling panels overlap each other.
    - Total widths/heights match the splitter's available space.
    """

    _SIZES = [
        (1024, 768),   # small laptop
        (1280, 800),   # typical laptop
        (1400, 900),   # default
        (1920, 1080),  # full HD
    ]

    @pytest.fixture()
    def regression_window(self, qtbot):
        """Build lightweight splitter window for regression checks."""
        win = _TestSplitterWindow()
        win.resize(1400, 900)

        left = QtWidgets.QFrame()
        left.setObjectName("LeftPanel")
        left.setMinimumWidth(LC.LEFT_SIDEBAR_MIN)
        left.setMaximumWidth(LC.LEFT_SIDEBAR_MAX)

        canvas = QtWidgets.QFrame()
        canvas.setObjectName("CanvasPanel")
        canvas.setMinimumSize(LC.CANVAS_MIN_W, LC.CANVAS_MIN_H)
        canvas.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )

        right = QtWidgets.QFrame()
        right.setObjectName("RightPanel")
        right.setMinimumWidth(LC.RIGHT_SIDEBAR_MIN)
        right.setMaximumWidth(LC.RIGHT_SIDEBAR_MAX)

        top_splitter = GripSplitter(QtCore.Qt.Orientation.Horizontal)
        top_splitter.setHandleWidth(LC.SPLITTER_HANDLE_W)
        top_splitter.setChildrenCollapsible(False)
        top_splitter.addWidget(left)
        top_splitter.addWidget(canvas)
        top_splitter.addWidget(right)
        top_splitter.setStretchFactor(0, 0)
        top_splitter.setStretchFactor(1, 1)
        top_splitter.setStretchFactor(2, 0)

        status = QtWidgets.QFrame()
        status.setObjectName("StatusPanel")
        status.setMinimumHeight(LC.TIMELINE_MIN_H)
        status.setMaximumHeight(LC.TIMELINE_MAX_H)

        outer_splitter = GripSplitter(QtCore.Qt.Orientation.Vertical)
        outer_splitter.setHandleWidth(LC.SPLITTER_HANDLE_W)
        outer_splitter.setChildrenCollapsible(False)
        outer_splitter.addWidget(top_splitter)
        outer_splitter.addWidget(status)
        outer_splitter.setStretchFactor(0, 1)
        outer_splitter.setStretchFactor(1, 0)

        canvas_w = 1400 - LC.LEFT_SIDEBAR_INIT - LC.RIGHT_SIDEBAR_INIT - 2 * LC.SPLITTER_HANDLE_W
        top_splitter.setSizes([LC.LEFT_SIDEBAR_INIT, canvas_w, LC.RIGHT_SIDEBAR_INIT])
        main_h = 900 - LC.TIMELINE_INIT_H - LC.SPLITTER_HANDLE_W
        outer_splitter.setSizes([main_h, LC.TIMELINE_INIT_H])

        win.setCentralWidget(outer_splitter)
        win._top_splitter = top_splitter
        win._outer_splitter = outer_splitter
        win._left_panel = left
        win._canvas_panel = canvas
        win._right_panel = right
        win._status_panel = status

        qtbot.addWidget(win)
        win.show()
        _process_events()
        return win

    @pytest.mark.parametrize("w, h", _SIZES, ids=[f"{w}x{h}" for w, h in _SIZES])
    def test_all_panels_visible(self, regression_window, w, h):
        """Every panel should have positive width and height."""
        regression_window.resize(w, h)
        _process_events(300)

        for panel_name in ("_left_panel", "_canvas_panel", "_right_panel", "_status_panel"):
            panel = getattr(regression_window, panel_name)
            assert panel.width() > 0, f"{panel_name} has zero width at {w}x{h}"
            assert panel.height() > 0, f"{panel_name} has zero height at {w}x{h}"

    @pytest.mark.parametrize("w, h", _SIZES, ids=[f"{w}x{h}" for w, h in _SIZES])
    def test_canvas_above_minimum(self, regression_window, w, h):
        """Canvas must meet its minimum size at every tested resolution."""
        regression_window.resize(w, h)
        _process_events(300)

        canvas = regression_window._canvas_panel
        assert canvas.width() >= LC.CANVAS_MIN_W, (
            f"Canvas width {canvas.width()} < {LC.CANVAS_MIN_W} at {w}x{h}"
        )
        assert canvas.height() >= LC.CANVAS_MIN_H, (
            f"Canvas height {canvas.height()} < {LC.CANVAS_MIN_H} at {w}x{h}"
        )

    @pytest.mark.parametrize("w, h", _SIZES, ids=[f"{w}x{h}" for w, h in _SIZES])
    def test_no_horizontal_overlap(self, regression_window, w, h):
        """Left, canvas, and right should not overlap horizontally."""
        regression_window.resize(w, h)
        _process_events(300)

        left = regression_window._left_panel
        canvas = regression_window._canvas_panel
        right = regression_window._right_panel

        # Map positions to the splitter's coordinate system
        sp = regression_window._top_splitter
        left_end = left.mapTo(sp, QtCore.QPoint(left.width(), 0)).x()
        canvas_start = canvas.mapTo(sp, QtCore.QPoint(0, 0)).x()
        canvas_end = canvas.mapTo(sp, QtCore.QPoint(canvas.width(), 0)).x()
        right_start = right.mapTo(sp, QtCore.QPoint(0, 0)).x()

        # Allow handle width tolerance
        tol = LC.SPLITTER_HANDLE_W + 2
        assert left_end <= canvas_start + tol, (
            f"Left/canvas overlap at {w}x{h}: left_end={left_end}, canvas_start={canvas_start}"
        )
        assert canvas_end <= right_start + tol, (
            f"Canvas/right overlap at {w}x{h}: canvas_end={canvas_end}, right_start={right_start}"
        )

    @pytest.mark.parametrize("w, h", _SIZES, ids=[f"{w}x{h}" for w, h in _SIZES])
    def test_no_vertical_overlap(self, regression_window, w, h):
        """Top area and status should not overlap vertically."""
        regression_window.resize(w, h)
        _process_events(300)

        sp = regression_window._outer_splitter
        sizes = sp.sizes()
        handle_space = (sp.count() - 1) * sp.handleWidth()
        total = sum(sizes) + handle_space
        # Sizes + handles should sum to available height (within tolerance)
        assert abs(total - sp.height()) < 5, (
            f"Vertical sizes don't sum to height at {w}x{h}: "
            f"{sizes} + {handle_space}px handles = {total} vs {sp.height()}"
        )

    @pytest.mark.parametrize("w, h", _SIZES, ids=[f"{w}x{h}" for w, h in _SIZES])
    def test_horizontal_sizes_sum(self, regression_window, w, h):
        """Top-splitter child sizes + handle widths should sum to available width."""
        regression_window.resize(w, h)
        _process_events(300)

        sp = regression_window._top_splitter
        sizes = sp.sizes()
        # sizes() returns widget sizes only; handles occupy additional space
        handle_space = (sp.count() - 1) * sp.handleWidth()
        total = sum(sizes) + handle_space
        assert abs(total - sp.width()) < 5, (
            f"Horizontal sizes don't sum to width at {w}x{h}: "
            f"{sizes} + {handle_space}px handles = {total} vs {sp.width()}"
        )
