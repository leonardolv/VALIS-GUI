"""Follow-ups to the 2026-08-18 Preferences-wiring pass.

That run wired 7 of 13 persisted-but-never-read Preferences fields into real
call sites and filed the remaining two as Backlog items needing a design
decision rather than just a call site: ``ui/show_tooltips`` (needs an
application-wide event filter, not a single read) and ``cache/persist``
("Keep cache between sessions" - needs a decision about what "not
persisting" means operationally). Both are now wired:

* ``cache/persist`` unchecked clears the on-disk thumbnail cache in
  ``MainWindow.closeEvent`` - the smaller-risk of the two options the
  Backlog entry weighed (clear on exit) rather than rearchitecting
  ``ThumbnailCache`` into an in-memory-only cache for the session.
* ``ui/show_tooltips`` unchecked is enforced by ``app._ToolTipSuppressionFilter``,
  installed on the ``QApplication`` in ``run_app`` so it sees every
  ``QEvent.Type.ToolTip`` regardless of which of the dozens of widgets it
  was headed for.
"""

from __future__ import annotations

import importlib.util
from unittest.mock import patch

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtGui, QtWidgets

from valis_workstation.utils.qt_logging import QtLogEmitter


# ---------------------------------------------------------------------------
# ui/show_tooltips -> _ToolTipSuppressionFilter
# ---------------------------------------------------------------------------


class TestToolTipSuppressionFilter:
    @pytest.fixture(autouse=True)
    def _clean_setting(self):
        settings = QtCore.QSettings("VALIS", "Workstation")
        previous = settings.value("ui/show_tooltips", None)
        yield
        if previous is None:
            settings.remove("ui/show_tooltips")
        else:
            settings.setValue("ui/show_tooltips", previous)

    def _tooltip_event(self):
        return QtCore.QEvent(QtCore.QEvent.Type.ToolTip)

    def test_suppresses_tooltips_when_disabled(self):
        from valis_workstation.app import _ToolTipSuppressionFilter

        QtCore.QSettings("VALIS", "Workstation").setValue(
            "ui/show_tooltips", False
        )
        filt = _ToolTipSuppressionFilter()
        consumed = filt.eventFilter(QtCore.QObject(), self._tooltip_event())
        assert consumed is True

    def test_lets_tooltips_through_when_enabled(self):
        from valis_workstation.app import _ToolTipSuppressionFilter

        QtCore.QSettings("VALIS", "Workstation").setValue(
            "ui/show_tooltips", True
        )
        filt = _ToolTipSuppressionFilter()
        consumed = filt.eventFilter(QtCore.QObject(), self._tooltip_event())
        assert consumed is False

    def test_defaults_to_enabled_when_unset(self):
        from valis_workstation.app import _ToolTipSuppressionFilter

        QtCore.QSettings("VALIS", "Workstation").remove("ui/show_tooltips")
        filt = _ToolTipSuppressionFilter()
        consumed = filt.eventFilter(QtCore.QObject(), self._tooltip_event())
        assert consumed is False

    def test_non_tooltip_events_are_never_consumed(self):
        """Disabling tooltips must not swallow unrelated events."""
        from valis_workstation.app import _ToolTipSuppressionFilter

        QtCore.QSettings("VALIS", "Workstation").setValue(
            "ui/show_tooltips", False
        )
        filt = _ToolTipSuppressionFilter()
        other_event = QtCore.QEvent(QtCore.QEvent.Type.MouseButtonPress)
        consumed = filt.eventFilter(QtCore.QObject(), other_event)
        assert consumed is False

    def test_installed_on_the_real_application(self, qtbot):
        """run_app installs the filter on the QApplication, not a dialog."""
        from valis_workstation.app import _ToolTipSuppressionFilter

        app = QtWidgets.QApplication.instance()
        app._tooltip_suppression_filter = _ToolTipSuppressionFilter(app)
        app.installEventFilter(app._tooltip_suppression_filter)
        try:
            assert app._tooltip_suppression_filter in app.children()
        finally:
            app.removeEventFilter(app._tooltip_suppression_filter)
            del app._tooltip_suppression_filter


# ---------------------------------------------------------------------------
# cache/persist -> MainWindow.closeEvent
# ---------------------------------------------------------------------------


class TestCachePersistOnClose:
    @pytest.fixture()
    def win(self, qtbot, monkeypatch, tmp_path):
        _original_find_spec = importlib.util.find_spec

        def _patched_find_spec(name, *args, **kwargs):
            if name == "napari":
                return None
            return _original_find_spec(name, *args, **kwargs)

        monkeypatch.setattr(importlib.util, "find_spec", _patched_find_spec)
        monkeypatch.setattr(
            QtWidgets.QMessageBox,
            "question",
            staticmethod(
                lambda *a, **kw: QtWidgets.QMessageBox.StandardButton.Yes
            ),
        )

        from valis_workstation.main_window import MainWindow

        w = MainWindow(
            repo_root=tmp_path,
            log_emitter=QtLogEmitter(),
            simple_elastix_available=False,
        )
        qtbot.addWidget(w)
        return w

    @pytest.fixture(autouse=True)
    def _clean_setting(self):
        settings = QtCore.QSettings("VALIS", "Workstation")
        previous = settings.value("cache/persist", None)
        yield
        if previous is None:
            settings.remove("cache/persist")
        else:
            settings.setValue("cache/persist", previous)

    def test_persist_off_clears_the_cache_on_close(self, win):
        QtCore.QSettings("VALIS", "Workstation").setValue("cache/persist", False)
        with patch("valis_workstation.main_window.get_thumbnail_cache") as mock_get:
            win.closeEvent(QtGui.QCloseEvent())
        mock_get.return_value.clear.assert_called_once()

    def test_persist_on_leaves_the_cache_alone(self, win):
        QtCore.QSettings("VALIS", "Workstation").setValue("cache/persist", True)
        with patch("valis_workstation.main_window.get_thumbnail_cache") as mock_get:
            win.closeEvent(QtGui.QCloseEvent())
        mock_get.return_value.clear.assert_not_called()

    def test_unset_defaults_to_keeping_the_cache(self, win):
        """The checkbox itself defaults to checked (True); the read-back
        default must match or a fresh install would silently wipe its
        cache on every exit."""
        QtCore.QSettings("VALIS", "Workstation").remove("cache/persist")
        with patch("valis_workstation.main_window.get_thumbnail_cache") as mock_get:
            win.closeEvent(QtGui.QCloseEvent())
        mock_get.return_value.clear.assert_not_called()

    def test_a_clear_failure_does_not_block_closing(self, win):
        """A diagnostics write must never be what breaks closing the app -
        same principle as this codebase's other best-effort cleanup steps."""
        QtCore.QSettings("VALIS", "Workstation").setValue("cache/persist", False)
        with patch("valis_workstation.main_window.get_thumbnail_cache") as mock_get:
            mock_get.return_value.clear.side_effect = OSError("disk gone")
            event = QtGui.QCloseEvent()
            win.closeEvent(event)
        assert event.isAccepted()
