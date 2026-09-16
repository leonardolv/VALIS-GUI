"""Tests for the ``ui/high_contrast``/``ui/reduced_motion`` accessibility
settings.

Both keys existed in ``settings_keys.py`` with no UI entry point and no
reader anywhere in the app (Backlog: "`ui/high_contrast`/`ui/reduced_motion`
settings keys are fully dead"). This wires both to real behavior:

* ``ui/high_contrast`` - ``app.build_stylesheet``/``app.apply_theme`` append
  a high-contrast QSS overlay on top of the base dark theme, applied live
  from Preferences (no restart) the same way ``ui/show_tooltips`` already
  is.
* ``ui/reduced_motion`` - ``BlinkViewerDialog`` disables its "Blink" mode
  (an auto-toggling flash timer) when the setting is on, leaving the two
  static comparison modes (Side-by-side, Swipe) untouched.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _mock_viewer():
    viewer = MagicMock()
    viewer.layers = MagicMock()
    viewer.layers.__iter__ = MagicMock(return_value=iter([]))
    mock_layer = MagicMock()
    mock_layer.visible = True
    mock_layer.opacity = 1.0
    viewer.open.return_value = [mock_layer]
    return viewer


@pytest.fixture()
def _clean_settings():
    settings = QtCore.QSettings("VALIS", "Workstation")
    keys = ("ui/high_contrast", "ui/reduced_motion")
    previous = {key: settings.value(key, None) for key in keys}
    yield settings
    for key, value in previous.items():
        if value is None:
            settings.remove(key)
        else:
            settings.setValue(key, value)


# ---------------------------------------------------------------------------
# ui/high_contrast -> app.build_stylesheet / apply_theme
# ---------------------------------------------------------------------------


class TestHighContrastStylesheet:
    def _fake_repo(self, tmp_path, base_css="QWidget { color: white; }"):
        style_dir = tmp_path / "src" / "valis_workstation" / "styles"
        style_dir.mkdir(parents=True)
        (style_dir / "adobe_dark.qss").write_text(base_css, encoding="utf-8")
        (style_dir / "high_contrast_overlay.qss").write_text(
            "QWidget { background-color: #000000; }", encoding="utf-8"
        )
        return tmp_path

    def test_overlay_omitted_when_disabled(self, tmp_path, _clean_settings):
        from valis_workstation.app import build_stylesheet

        repo_root = self._fake_repo(tmp_path)
        _clean_settings.setValue("ui/high_contrast", False)
        css = build_stylesheet(repo_root, _clean_settings)
        assert "color: white" in css
        assert "#000000" not in css

    def test_overlay_appended_when_enabled(self, tmp_path, _clean_settings):
        from valis_workstation.app import build_stylesheet

        repo_root = self._fake_repo(tmp_path)
        _clean_settings.setValue("ui/high_contrast", True)
        css = build_stylesheet(repo_root, _clean_settings)
        assert "color: white" in css
        assert "#000000" in css
        # Base theme must come first so the overlay wins the cascade.
        assert css.index("color: white") < css.index("#000000")

    def test_defaults_to_disabled_when_unset(self, tmp_path, _clean_settings):
        from valis_workstation.app import build_stylesheet

        repo_root = self._fake_repo(tmp_path)
        _clean_settings.remove("ui/high_contrast")
        css = build_stylesheet(repo_root, _clean_settings)
        assert "#000000" not in css

    def test_missing_overlay_file_is_a_silent_no_op(self, tmp_path, _clean_settings):
        """Enabling high contrast when the overlay file doesn't exist (e.g.
        a stripped-down install) must not crash - fall back to the base
        theme alone, same shape as the base loader's own missing-file
        behavior."""
        from valis_workstation.app import build_stylesheet

        style_dir = tmp_path / "src" / "valis_workstation" / "styles"
        style_dir.mkdir(parents=True)
        (style_dir / "adobe_dark.qss").write_text(
            "QWidget { color: white; }", encoding="utf-8"
        )
        _clean_settings.setValue("ui/high_contrast", True)
        css = build_stylesheet(tmp_path, _clean_settings)
        assert css == "QWidget { color: white; }"

    def test_apply_theme_sets_the_composed_stylesheet(self, tmp_path, _clean_settings, qtbot):
        from valis_workstation.app import apply_theme

        repo_root = self._fake_repo(tmp_path)
        _clean_settings.setValue("ui/high_contrast", True)
        app = QtWidgets.QApplication.instance()
        original = app.styleSheet()
        try:
            apply_theme(app, repo_root)
            assert "#000000" in app.styleSheet()
        finally:
            app.setStyleSheet(original)


# ---------------------------------------------------------------------------
# ui/reduced_motion -> BlinkViewerDialog
# ---------------------------------------------------------------------------


class TestReducedMotionBlinkViewer:
    def _make_dialog(self, qtbot):
        from valis_workstation.ui.dialogs.blink_viewer import BlinkViewerDialog

        viewer = _mock_viewer()
        slides = [Path("a.tif"), Path("b.tif")]
        dialog = BlinkViewerDialog(viewer, slides)
        qtbot.addWidget(dialog)
        return dialog

    def test_blink_mode_disabled_in_combo(self, qtbot, _clean_settings):
        _clean_settings.setValue("ui/reduced_motion", True)
        dialog = self._make_dialog(qtbot)
        blink_index = dialog._mode.findText("Blink")
        item = dialog._mode.model().item(blink_index)
        assert item.isEnabled() is False

    def test_current_mode_moved_off_blink(self, qtbot, _clean_settings):
        _clean_settings.setValue("ui/reduced_motion", True)
        dialog = self._make_dialog(qtbot)
        assert dialog._mode.currentText() != "Blink"

    def test_start_blink_button_disabled(self, qtbot, _clean_settings):
        _clean_settings.setValue("ui/reduced_motion", True)
        dialog = self._make_dialog(qtbot)
        assert dialog._blink_toggle.isEnabled() is False

    def test_checking_the_disabled_button_does_not_start_the_timer(
        self, qtbot, _clean_settings
    ):
        """Defense in depth: even if something programmatically checks the
        button, the timer must not be started by a strobing mode the user
        asked to avoid."""
        _clean_settings.setValue("ui/reduced_motion", True)
        dialog = self._make_dialog(qtbot)
        dialog._blink_toggle.setChecked(True)
        assert not dialog._timer.isActive()

    def test_static_modes_are_unaffected(self, qtbot, _clean_settings):
        _clean_settings.setValue("ui/reduced_motion", True)
        dialog = self._make_dialog(qtbot)
        side_by_side_index = dialog._mode.findText("Side-by-side")
        swipe_index = dialog._mode.findText("Swipe")
        assert dialog._mode.model().item(side_by_side_index).isEnabled() is True
        assert dialog._mode.model().item(swipe_index).isEnabled() is True

    def test_blink_mode_available_and_functional_when_disabled(
        self, qtbot, _clean_settings
    ):
        """Unset/False is the existing, pre-change behavior - a full
        regression guard, not just "not reduced-motion-disabled"."""
        _clean_settings.setValue("ui/reduced_motion", False)
        dialog = self._make_dialog(qtbot)
        blink_index = dialog._mode.findText("Blink")
        assert dialog._mode.model().item(blink_index).isEnabled() is True
        assert dialog._mode.currentText() == "Blink"
        assert dialog._blink_toggle.isEnabled() is True
        dialog._blink_toggle.setChecked(True)
        assert dialog._timer.isActive()

    def test_defaults_to_enabled_when_unset(self, qtbot, _clean_settings):
        _clean_settings.remove("ui/reduced_motion")
        dialog = self._make_dialog(qtbot)
        assert dialog._blink_toggle.isEnabled() is True


# ---------------------------------------------------------------------------
# PreferencesDialog round trip
# ---------------------------------------------------------------------------


class TestPreferencesDialogAccessibilityFields:
    @pytest.fixture()
    def dialog(self, qtbot, _clean_settings):
        from valis_workstation.ui.dialogs.preferences_dialog import PreferencesDialog

        d = PreferencesDialog()
        qtbot.addWidget(d)
        return d

    def test_defaults_to_unchecked(self, dialog):
        assert dialog._high_contrast_check.isChecked() is False
        assert dialog._reduced_motion_check.isChecked() is False

    def test_loads_persisted_values(self, qtbot, _clean_settings):
        _clean_settings.setValue("ui/high_contrast", True)
        _clean_settings.setValue("ui/reduced_motion", True)
        from valis_workstation.ui.dialogs.preferences_dialog import PreferencesDialog

        d = PreferencesDialog()
        qtbot.addWidget(d)
        assert d._high_contrast_check.isChecked() is True
        assert d._reduced_motion_check.isChecked() is True

    def test_save_persists_both_fields(self, dialog, _clean_settings):
        dialog._high_contrast_check.setChecked(True)
        dialog._reduced_motion_check.setChecked(True)
        dialog._save_and_accept()
        assert _clean_settings.value("ui/high_contrast", False, type=bool) is True
        assert _clean_settings.value("ui/reduced_motion", False, type=bool) is True

    def test_restore_defaults_unchecks_both(self, dialog, monkeypatch):
        dialog._high_contrast_check.setChecked(True)
        dialog._reduced_motion_check.setChecked(True)
        monkeypatch.setattr(
            QtWidgets.QMessageBox,
            "question",
            staticmethod(
                lambda *a, **kw: QtWidgets.QMessageBox.StandardButton.Yes
            ),
        )
        dialog._restore_defaults()
        assert dialog._high_contrast_check.isChecked() is False
        assert dialog._reduced_motion_check.isChecked() is False

class TestPreferencesChangedReappliesThemeLive:
    """Saving Preferences must reapply the theme through the real
    MainWindow hook, not just persist the setting - otherwise
    high-contrast mode would need an app restart the way the old
    "Some preference changes require restarting" message implied every
    setting did."""

    @pytest.fixture()
    def win(self, qtbot, monkeypatch, tmp_path):
        import importlib.util

        _original_find_spec = importlib.util.find_spec

        def _patched_find_spec(name, *args, **kwargs):
            if name == "napari":
                return None
            return _original_find_spec(name, *args, **kwargs)

        monkeypatch.setattr(importlib.util, "find_spec", _patched_find_spec)

        from valis_workstation.main_window import MainWindow
        from valis_workstation.utils.qt_logging import QtLogEmitter

        w = MainWindow(
            repo_root=ROOT,
            log_emitter=QtLogEmitter(),
            simple_elastix_available=False,
        )
        qtbot.addWidget(w)
        return w

    def test_high_contrast_overlay_applied_without_restart(
        self, win, monkeypatch, _clean_settings
    ):
        monkeypatch.setattr(
            QtWidgets.QMessageBox, "information", staticmethod(lambda *a, **kw: None)
        )
        app = QtWidgets.QApplication.instance()
        original_stylesheet = app.styleSheet()
        _clean_settings.setValue("ui/high_contrast", True)
        try:
            win._on_preferences_changed()
            assert "High Contrast" in app.styleSheet()
        finally:
            app.setStyleSheet(original_stylesheet)

    def test_disabling_high_contrast_removes_the_overlay(
        self, win, monkeypatch, _clean_settings
    ):
        monkeypatch.setattr(
            QtWidgets.QMessageBox, "information", staticmethod(lambda *a, **kw: None)
        )
        app = QtWidgets.QApplication.instance()
        original_stylesheet = app.styleSheet()
        try:
            _clean_settings.setValue("ui/high_contrast", True)
            win._on_preferences_changed()
            _clean_settings.setValue("ui/high_contrast", False)
            win._on_preferences_changed()
            assert "High Contrast" not in app.styleSheet()
        finally:
            app.setStyleSheet(original_stylesheet)
