"""``ui/high_contrast``/``ui/reduced_motion`` were fully dead settings keys.

A 2026-09-08 audit found both declared in ``settings_keys.py`` with zero
readers/writers anywhere in the app and no checkbox for either in
``PreferencesDialog`` — unlike every other Preferences field this repo has
fixed before (``ui/show_tooltips``, ``cache/persist``, the performance
trackers), these two had no UI entry point at all to even discover them
from. Wired up as a small, real accessibility feature rather than deleted:

* ``ui/high_contrast`` composes a genuinely higher-contrast QSS variant
  (``styles/high_contrast_overrides.qss``) after the base theme —
  ``utils/accessibility.py::compose_stylesheet``/``apply_theme`` — applied
  at startup (``app.run_app``) and re-applied immediately from
  ``MainWindow._on_preferences_changed`` when it changes, no restart
  required, the same "re-read fresh on every call" approach
  ``app._ToolTipSuppressionFilter`` and ``performance._monitoring_enabled``
  already use for their own settings.
* ``ui/reduced_motion`` shortens the two ``QPropertyAnimation`` fade-outs
  that exist in the app today (``SplashScreen.finish``,
  ``LoadingOverlay.dismiss``, both ``ui/splash_screen.py``) via
  ``utils/accessibility.py::reduced_motion_duration_ms`` — a shared helper
  any future animated transition should also consult, rather than
  reinventing its own on/off check.

Both default off (``False``), matching every boolean checkbox in this
dialog's "unset -> unchecked" convention.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_accessibility_settings():
    """Leaves ``ui/high_contrast``/``ui/reduced_motion`` as they were found.

    Mirrors ``test_preferences_wiring_followups.py``'s ``_clean_setting``
    fixture, just for both keys at once since every test in this file
    touches at least one of them.
    """
    settings = QtCore.QSettings("VALIS", "Workstation")
    previous = {
        key: settings.value(key, None) for key in ("ui/high_contrast", "ui/reduced_motion")
    }
    yield
    for key, value in previous.items():
        if value is None:
            settings.remove(key)
        else:
            settings.setValue(key, value)


# ---------------------------------------------------------------------------
# utils.accessibility — reading the settings back
# ---------------------------------------------------------------------------


class TestHighContrastEnabled:
    def test_defaults_to_off_when_unset(self):
        from valis_workstation.utils.accessibility import high_contrast_enabled

        QtCore.QSettings("VALIS", "Workstation").remove("ui/high_contrast")
        assert high_contrast_enabled() is False

    def test_true_when_set(self):
        from valis_workstation.utils.accessibility import high_contrast_enabled

        QtCore.QSettings("VALIS", "Workstation").setValue("ui/high_contrast", True)
        assert high_contrast_enabled() is True

    def test_false_when_explicitly_off(self):
        from valis_workstation.utils.accessibility import high_contrast_enabled

        QtCore.QSettings("VALIS", "Workstation").setValue("ui/high_contrast", False)
        assert high_contrast_enabled() is False


class TestShouldReduceMotion:
    def test_defaults_to_off_when_unset(self):
        from valis_workstation.utils.accessibility import should_reduce_motion

        QtCore.QSettings("VALIS", "Workstation").remove("ui/reduced_motion")
        assert should_reduce_motion() is False

    def test_true_when_set(self):
        from valis_workstation.utils.accessibility import should_reduce_motion

        QtCore.QSettings("VALIS", "Workstation").setValue("ui/reduced_motion", True)
        assert should_reduce_motion() is True


class TestReducedMotionDurationMs:
    def test_returns_normal_duration_when_off(self):
        from valis_workstation.utils.accessibility import reduced_motion_duration_ms

        QtCore.QSettings("VALIS", "Workstation").setValue("ui/reduced_motion", False)
        assert reduced_motion_duration_ms(350) == 350

    def test_collapses_to_near_zero_when_on(self):
        from valis_workstation.utils.accessibility import (
            REDUCED_MOTION_DURATION_MS,
            reduced_motion_duration_ms,
        )

        QtCore.QSettings("VALIS", "Workstation").setValue("ui/reduced_motion", True)
        assert reduced_motion_duration_ms(350) == REDUCED_MOTION_DURATION_MS
        assert reduced_motion_duration_ms(350) < 350

    def test_stays_a_positive_duration_not_literal_zero(self):
        """A real (if tiny) duration keeps ``finished`` firing asynchronously
        rather than every call site needing its own zero-duration special
        case — see the constant's own docstring."""
        from valis_workstation.utils.accessibility import REDUCED_MOTION_DURATION_MS

        assert REDUCED_MOTION_DURATION_MS > 0


# ---------------------------------------------------------------------------
# utils.accessibility — the high-contrast stylesheet
# ---------------------------------------------------------------------------


class TestComposeStylesheet:
    def test_returns_base_unchanged_when_off(self):
        from valis_workstation.utils.accessibility import compose_stylesheet

        QtCore.QSettings("VALIS", "Workstation").setValue("ui/high_contrast", False)
        assert compose_stylesheet("QWidget { color: red; }") == "QWidget { color: red; }"

    def test_appends_real_overrides_when_on(self):
        from valis_workstation.utils.accessibility import compose_stylesheet

        QtCore.QSettings("VALIS", "Workstation").setValue("ui/high_contrast", True)
        composed = compose_stylesheet("QWidget { color: red; }")
        assert "QWidget { color: red; }" in composed
        # The override file's own distinguishing content: pure-black/white
        # base colours and the thick bright focus outline.
        assert "#000000" in composed
        assert "3px solid #ffdd00" in composed

    def test_the_override_file_actually_exists_on_disk(self):
        """Guards against the override QSS being renamed/moved without
        updating the path ``compose_stylesheet`` reads from."""
        from valis_workstation.utils.accessibility import _HIGH_CONTRAST_QSS

        assert _HIGH_CONTRAST_QSS.exists()
        assert _HIGH_CONTRAST_QSS.name == "high_contrast_overrides.qss"

    def test_missing_override_file_falls_back_to_base_unchanged(self, tmp_path):
        """A high-contrast toggle must never leave the app with no
        stylesheet at all just because the overrides file went missing."""
        from valis_workstation.utils import accessibility

        QtCore.QSettings("VALIS", "Workstation").setValue("ui/high_contrast", True)
        missing = tmp_path / "does_not_exist.qss"
        with patch.object(accessibility, "_HIGH_CONTRAST_QSS", missing):
            result = accessibility.compose_stylesheet("QWidget { color: red; }")
        assert result == "QWidget { color: red; }"

    def test_empty_base_with_overrides_on_returns_just_the_overrides(self):
        from valis_workstation.utils.accessibility import compose_stylesheet

        QtCore.QSettings("VALIS", "Workstation").setValue("ui/high_contrast", True)
        result = compose_stylesheet("")
        assert "#ffdd00" in result


class TestApplyTheme:
    def test_sets_the_composed_stylesheet_on_the_given_app(self, qtbot):
        from valis_workstation.utils.accessibility import apply_theme

        QtCore.QSettings("VALIS", "Workstation").setValue("ui/high_contrast", False)
        app = QtWidgets.QApplication.instance()
        try:
            apply_theme("QWidget { color: red; }", app)
            assert "QWidget { color: red; }" in app.styleSheet()
        finally:
            app.setStyleSheet("")

    def test_high_contrast_overrides_land_in_the_applied_stylesheet(self, qtbot):
        from valis_workstation.utils.accessibility import apply_theme

        QtCore.QSettings("VALIS", "Workstation").setValue("ui/high_contrast", True)
        app = QtWidgets.QApplication.instance()
        try:
            apply_theme("QWidget { color: red; }", app)
            assert "3px solid #ffdd00" in app.styleSheet()
        finally:
            app.setStyleSheet("")

    def test_no_running_application_is_a_silent_no_op(self):
        from valis_workstation.utils.accessibility import apply_theme

        with patch(
            "PySide6.QtWidgets.QApplication.instance", return_value=None
        ):
            apply_theme("QWidget { color: red; }")  # must not raise


# ---------------------------------------------------------------------------
# PreferencesDialog — the two new checkboxes
# ---------------------------------------------------------------------------


class TestPreferencesDialogAccessibilityCheckboxes:
    def test_checkboxes_exist_and_default_unchecked(self, qtbot):
        from valis_workstation.ui.dialogs.preferences_dialog import PreferencesDialog

        QtCore.QSettings("VALIS", "Workstation").remove("ui/high_contrast")
        QtCore.QSettings("VALIS", "Workstation").remove("ui/reduced_motion")

        d = PreferencesDialog()
        qtbot.addWidget(d)
        assert isinstance(d._high_contrast_check, QtWidgets.QCheckBox)
        assert isinstance(d._reduced_motion_check, QtWidgets.QCheckBox)
        assert d._high_contrast_check.isChecked() is False
        assert d._reduced_motion_check.isChecked() is False

    def test_dialog_loads_a_previously_saved_on_state(self, qtbot):
        """Opening the dialog reflects whatever was last persisted, not just
        the construction-time default — the "reopen and see the right
        state" half of the round trip."""
        from valis_workstation.ui.dialogs.preferences_dialog import PreferencesDialog

        settings = QtCore.QSettings("VALIS", "Workstation")
        settings.setValue("ui/high_contrast", True)
        settings.setValue("ui/reduced_motion", True)

        d = PreferencesDialog()
        qtbot.addWidget(d)
        assert d._high_contrast_check.isChecked() is True
        assert d._reduced_motion_check.isChecked() is True

    def test_toggling_on_and_saving_persists_the_value(self, qtbot):
        from valis_workstation.ui.dialogs.preferences_dialog import PreferencesDialog

        QtCore.QSettings("VALIS", "Workstation").remove("ui/high_contrast")
        QtCore.QSettings("VALIS", "Workstation").remove("ui/reduced_motion")

        d = PreferencesDialog()
        qtbot.addWidget(d)
        d._high_contrast_check.setChecked(True)
        d._reduced_motion_check.setChecked(True)
        d._save_and_accept()

        settings = QtCore.QSettings("VALIS", "Workstation")
        assert settings.value("ui/high_contrast", False, type=bool) is True
        assert settings.value("ui/reduced_motion", False, type=bool) is True

    def test_toggling_off_and_saving_persists_the_value(self, qtbot):
        from valis_workstation.ui.dialogs.preferences_dialog import PreferencesDialog

        settings = QtCore.QSettings("VALIS", "Workstation")
        settings.setValue("ui/high_contrast", True)
        settings.setValue("ui/reduced_motion", True)

        d = PreferencesDialog()
        qtbot.addWidget(d)
        d._high_contrast_check.setChecked(False)
        d._reduced_motion_check.setChecked(False)
        d._save_and_accept()

        settings = QtCore.QSettings("VALIS", "Workstation")
        assert settings.value("ui/high_contrast", True, type=bool) is False
        assert settings.value("ui/reduced_motion", True, type=bool) is False

    def test_full_round_trip_save_then_reopen(self, qtbot):
        """toggle -> persisted value changes -> a *freshly opened* dialog
        reflects it, the exact round trip the task asked for."""
        from valis_workstation.ui.dialogs.preferences_dialog import PreferencesDialog

        QtCore.QSettings("VALIS", "Workstation").remove("ui/high_contrast")
        QtCore.QSettings("VALIS", "Workstation").remove("ui/reduced_motion")

        first = PreferencesDialog()
        qtbot.addWidget(first)
        first._high_contrast_check.setChecked(True)
        first._reduced_motion_check.setChecked(False)
        first._save_and_accept()

        second = PreferencesDialog()
        qtbot.addWidget(second)
        assert second._high_contrast_check.isChecked() is True
        assert second._reduced_motion_check.isChecked() is False

    def test_restore_defaults_unchecks_both(self, qtbot, monkeypatch):
        from valis_workstation.ui.dialogs.preferences_dialog import PreferencesDialog

        monkeypatch.setattr(
            QtWidgets.QMessageBox,
            "question",
            staticmethod(lambda *a, **kw: QtWidgets.QMessageBox.StandardButton.Yes),
        )

        d = PreferencesDialog()
        qtbot.addWidget(d)
        d._high_contrast_check.setChecked(True)
        d._reduced_motion_check.setChecked(True)
        d._restore_defaults()
        assert d._high_contrast_check.isChecked() is False
        assert d._reduced_motion_check.isChecked() is False


# ---------------------------------------------------------------------------
# MainWindow — high contrast re-applies without a restart
# ---------------------------------------------------------------------------


class TestMainWindowReappliesThemeOnPreferencesChanged:
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
            repo_root=tmp_path,
            log_emitter=QtLogEmitter(),
            simple_elastix_available=False,
        )
        qtbot.addWidget(w)
        return w

    def test_on_preferences_changed_reapplies_the_theme(self, win, monkeypatch):
        monkeypatch.setattr(
            QtWidgets.QMessageBox, "information", staticmethod(lambda *a, **kw: None)
        )
        with patch("valis_workstation.main_window.apply_theme") as mock_apply:
            win._on_preferences_changed()
        mock_apply.assert_called_once()

    def test_on_preferences_changed_uses_the_windows_own_repo_root(
        self, win, monkeypatch, tmp_path
    ):
        monkeypatch.setattr(
            QtWidgets.QMessageBox, "information", staticmethod(lambda *a, **kw: None)
        )
        with patch(
            "valis_workstation.main_window.base_stylesheet", return_value="X"
        ) as mock_base, patch("valis_workstation.main_window.apply_theme") as mock_apply:
            win._on_preferences_changed()
        mock_base.assert_called_once_with(tmp_path)
        mock_apply.assert_called_once_with("X")


# ---------------------------------------------------------------------------
# app.py — _load_stylesheet still behaves the same, now via accessibility
# ---------------------------------------------------------------------------


class TestAppStylesheetLoadingIsUnchanged:
    def test_load_stylesheet_still_reads_the_base_theme(self, tmp_path):
        from valis_workstation.app import _load_stylesheet

        style_dir = tmp_path / "src" / "valis_workstation" / "styles"
        style_dir.mkdir(parents=True)
        (style_dir / "adobe_dark.qss").write_text(
            "QWidget { color: red; }", encoding="utf-8"
        )
        assert "QWidget" in _load_stylesheet(tmp_path)

    def test_load_stylesheet_matches_accessibility_base_stylesheet(self, tmp_path):
        from valis_workstation.app import _load_stylesheet
        from valis_workstation.utils.accessibility import base_stylesheet

        style_dir = tmp_path / "src" / "valis_workstation" / "styles"
        style_dir.mkdir(parents=True)
        (style_dir / "adobe_dark.qss").write_text("QWidget {}", encoding="utf-8")
        assert _load_stylesheet(tmp_path) == base_stylesheet(tmp_path)


# ---------------------------------------------------------------------------
# splash_screen — the two real QPropertyAnimation fades honour reduced motion
# ---------------------------------------------------------------------------


class TestSplashScreenReducedMotion:
    def test_finish_uses_normal_duration_when_off(self, qtbot):
        from valis_workstation.ui.splash_screen import SplashScreen

        QtCore.QSettings("VALIS", "Workstation").setValue("ui/reduced_motion", False)
        splash = SplashScreen()
        qtbot.addWidget(splash)
        dummy = QtWidgets.QWidget()
        qtbot.addWidget(dummy)
        splash.finish(dummy)
        assert splash._fade.duration() == 350

    def test_finish_shortens_duration_when_on(self, qtbot):
        from valis_workstation.ui.splash_screen import SplashScreen
        from valis_workstation.utils.accessibility import REDUCED_MOTION_DURATION_MS

        QtCore.QSettings("VALIS", "Workstation").setValue("ui/reduced_motion", True)
        splash = SplashScreen()
        qtbot.addWidget(splash)
        dummy = QtWidgets.QWidget()
        qtbot.addWidget(dummy)
        splash.finish(dummy)
        assert splash._fade.duration() == REDUCED_MOTION_DURATION_MS

    def test_loading_overlay_dismiss_uses_normal_duration_when_off(self, qtbot):
        from valis_workstation.ui.splash_screen import LoadingOverlay

        QtCore.QSettings("VALIS", "Workstation").setValue("ui/reduced_motion", False)
        parent = QtWidgets.QWidget()
        qtbot.addWidget(parent)
        overlay = LoadingOverlay(parent)
        qtbot.addWidget(overlay)
        overlay.dismiss()
        assert overlay._fade.duration() == 200

    def test_loading_overlay_dismiss_shortens_duration_when_on(self, qtbot):
        from valis_workstation.ui.splash_screen import LoadingOverlay
        from valis_workstation.utils.accessibility import REDUCED_MOTION_DURATION_MS

        QtCore.QSettings("VALIS", "Workstation").setValue("ui/reduced_motion", True)
        parent = QtWidgets.QWidget()
        qtbot.addWidget(parent)
        overlay = LoadingOverlay(parent)
        qtbot.addWidget(overlay)
        overlay.dismiss()
        assert overlay._fade.duration() == REDUCED_MOTION_DURATION_MS
