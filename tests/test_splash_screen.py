"""Tests for SplashScreen, LoadingOverlay, and _Spinner widgets.

Covers instantiation, status/progress updates, dismiss/finish guards,
version label, window flags, geometry, and paint robustness.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from PySide6 import QtCore, QtWidgets

from valis_workstation.ui.splash_screen import SplashScreen, LoadingOverlay, _Spinner
import valis_workstation as _pkg


# ---------------------------------------------------------------------------
# _Spinner
# ---------------------------------------------------------------------------


class TestSpinner:
    """Tests for the animated arc spinner."""

    @pytest.fixture()
    def spinner(self, qtbot):
        w = _Spinner(48)
        qtbot.addWidget(w)
        return w

    def test_default_size(self, spinner):
        assert spinner.width() == 48
        assert spinner.height() == 48

    def test_custom_size(self, qtbot):
        w = _Spinner(64)
        qtbot.addWidget(w)
        assert w.width() == 64
        assert w.height() == 64

    def test_timer_runs_on_create(self, spinner):
        assert spinner._timer.state() == QtCore.QTimeLine.State.Running

    def test_stop_halts_timer(self, spinner):
        spinner.stop()
        assert spinner._timer.state() != QtCore.QTimeLine.State.Running

    def test_paint_no_crash(self, spinner):
        spinner.repaint()  # should not raise

    def test_angle_updates_on_frame(self, spinner):
        spinner._on_frame(90)
        assert spinner._angle == 90

    def test_angle_wraps(self, spinner):
        spinner._on_frame(360)
        assert spinner._angle == 360


# ---------------------------------------------------------------------------
# SplashScreen
# ---------------------------------------------------------------------------


class TestSplashScreen:
    """Tests for the startup splash screen."""

    @pytest.fixture()
    def splash(self, qtbot):
        w = SplashScreen()
        qtbot.addWidget(w)
        return w

    # Window properties
    def test_window_flags(self, splash):
        flags = splash.windowFlags()
        assert flags & QtCore.Qt.WindowType.FramelessWindowHint
        assert flags & QtCore.Qt.WindowType.WindowStaysOnTopHint

    def test_fixed_size(self, splash):
        assert splash.width() == 420
        assert splash.height() == 320

    def test_translucent_background(self, splash):
        assert splash.testAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

    # Status / progress
    def test_initial_status_text(self, splash):
        assert splash._status.text() == "Initializing\u2026"

    def test_set_status_updates_label(self, splash):
        splash.set_status("Loading JVM\u2026")
        assert splash._status.text() == "Loading JVM\u2026"

    def test_set_progress_range_and_value(self, splash):
        splash.set_progress(42, 100)
        assert splash._progress.value() == 42
        assert splash._progress.maximum() == 100

    def test_initial_progress_indeterminate(self, splash):
        assert splash._progress.minimum() == 0
        assert splash._progress.maximum() == 0  # indeterminate

    # Version label
    def test_version_label_matches_package(self, splash):
        # Find any child QLabel whose text starts with "v"
        labels = splash.findChildren(QtWidgets.QLabel)
        version_labels = [l for l in labels if l.text().startswith("v")]
        assert len(version_labels) == 1
        assert version_labels[0].text() == f"v{_pkg.__version__}"

    # Finish / guard
    def test_finish_stops_spinner(self, splash, qtbot):
        dummy = QtWidgets.QWidget()
        qtbot.addWidget(dummy)
        splash.finish(dummy)
        assert splash._spinner._timer.state() != QtCore.QTimeLine.State.Running

    def test_finish_double_call_safe(self, splash, qtbot):
        dummy = QtWidgets.QWidget()
        qtbot.addWidget(dummy)
        splash.finish(dummy)
        splash.finish(dummy)  # second call should be a no-op

    def test_finish_sets_finished_flag(self, splash, qtbot):
        dummy = QtWidgets.QWidget()
        qtbot.addWidget(dummy)
        assert splash._finished is False
        splash.finish(dummy)
        assert splash._finished is True

    # Paint
    def test_paint_event_no_crash(self, splash):
        splash.repaint()

    # Drop shadow
    def test_card_has_drop_shadow(self, splash):
        from PySide6.QtWidgets import QGraphicsDropShadowEffect

        effect = splash._card.graphicsEffect()
        assert isinstance(effect, QGraphicsDropShadowEffect)

    # Centre
    def test_center_on_screen(self, splash):
        screen = QtWidgets.QApplication.primaryScreen()
        if screen is None:
            pytest.skip("No screen available")
        geo = screen.availableGeometry()
        pos = splash.pos()
        assert geo.x() <= pos.x() <= geo.x() + geo.width()
        assert geo.y() <= pos.y() <= geo.y() + geo.height()


# ---------------------------------------------------------------------------
# LoadingOverlay
# ---------------------------------------------------------------------------


class TestLoadingOverlay:
    """Tests for the reusable loading overlay."""

    @pytest.fixture()
    def parent_widget(self, qtbot):
        w = QtWidgets.QWidget()
        w.resize(800, 600)
        qtbot.addWidget(w)
        return w

    @pytest.fixture()
    def overlay(self, qtbot, parent_widget):
        o = LoadingOverlay(parent_widget)
        # addWidget not needed — overlay is child of parent_widget
        return o

    # Geometry
    def test_fills_parent_geometry(self, overlay, parent_widget):
        assert overlay.geometry() == parent_widget.rect()

    def test_resize_follows_parent(self, overlay, parent_widget):
        parent_widget.resize(1024, 768)
        overlay.resizeEvent(None)  # synthetic trigger
        assert overlay.geometry().width() == 1024

    # Message
    def test_default_message(self, overlay):
        assert overlay._label.text() == "Please wait\u2026"

    def test_custom_message(self, qtbot, parent_widget):
        o = LoadingOverlay(parent_widget, "Loading slides\u2026")
        assert o._label.text() == "Loading slides\u2026"

    def test_set_message(self, overlay):
        overlay.set_message("Almost done\u2026")
        assert overlay._label.text() == "Almost done\u2026"

    # Dismiss / guard
    def test_dismiss_stops_spinner(self, overlay):
        overlay.dismiss()
        assert overlay._spinner._timer.state() != QtCore.QTimeLine.State.Running

    def test_dismiss_double_call_safe(self, overlay):
        overlay.dismiss()
        overlay.dismiss()  # should not raise

    def test_dismiss_sets_dismissed_flag(self, overlay):
        assert overlay._dismissed is False
        overlay.dismiss()
        assert overlay._dismissed is True

    # Cleanup
    def test_cleanup_hides_widget(self, overlay):
        overlay.show()
        overlay._cleanup()
        assert not overlay.isVisible()

    # Mouse events
    def test_mouse_events_not_transparent(self, overlay):
        assert not overlay.testAttribute(
            QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )

    # Paint
    def test_paint_draws_background(self, overlay):
        overlay.repaint()  # should not crash

    # Drop shadow on card
    def test_card_has_drop_shadow(self, overlay):
        from PySide6.QtWidgets import QGraphicsDropShadowEffect

        cards = overlay.findChildren(QtWidgets.QFrame)
        shadowed = [
            c
            for c in cards
            if isinstance(c.graphicsEffect(), QGraphicsDropShadowEffect)
        ]
        assert len(shadowed) >= 1
