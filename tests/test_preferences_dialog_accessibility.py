"""PreferencesDialog accessibility: accessible names, tooltips, hand cursors."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")
from PySide6 import QtCore, QtWidgets

from valis_workstation.ui.dialogs.preferences_dialog import PreferencesDialog

CONTROLS = [
    "_cache_dir_edit", "_browse_cache_btn", "_max_thumb_cache_spin",
    "_persist_cache_check", "_parallel_workers_spin", "_perf_monitoring_check",
    "_auto_refresh_spin", "_show_tooltips_check", "_show_statusbar_check",
    "_confirm_close_check", "_recent_files_spin", "_default_thumb_size_spin",
    "_high_contrast_check", "_reduced_motion_check",
]


@pytest.fixture
def dialog(qtbot):
    dlg = PreferencesDialog()
    qtbot.addWidget(dlg)
    return dlg


@pytest.mark.parametrize("attr", CONTROLS)
def test_control_has_accessible_name_and_tooltip(dialog, attr):
    widget = getattr(dialog, attr)
    assert widget.accessibleName()
    assert widget.toolTip()


def test_clickable_controls_use_hand_cursor(dialog):
    for attr in ("_browse_cache_btn", "_persist_cache_check", "_high_contrast_check"):
        assert getattr(dialog, attr).cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor


def test_dialog_buttons_have_hand_cursor(dialog):
    ok = dialog._button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
    assert ok.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor


def test_preferences_dialog_metadata_and_object_names(dialog):
    Std = QtWidgets.QDialogButtonBox.StandardButton

    assert dialog.objectName() == "preferencesDialog"
    assert dialog.accessibleName() == "Preferences Dialog"

    assert dialog.tabs.objectName() == "preferencesTabs"
    assert dialog.tabs.accessibleName() == "Preferences Categories"

    assert dialog._cache_dir_edit.objectName() == "prefCacheDirEdit"
    assert dialog._browse_cache_btn.objectName() == "prefBrowseCacheBtn"
    assert dialog._max_thumb_cache_spin.objectName() == "prefMaxThumbCacheSpin"
    assert dialog._persist_cache_check.objectName() == "prefPersistCacheCheck"
    assert dialog._parallel_workers_spin.objectName() == "prefParallelWorkersSpin"
    assert dialog._perf_monitoring_check.objectName() == "prefPerfMonitoringCheck"
    assert dialog._auto_refresh_spin.objectName() == "prefAutoRefreshSpin"
    assert dialog._show_tooltips_check.objectName() == "prefShowTooltipsCheck"
    assert dialog._show_statusbar_check.objectName() == "prefShowStatusbarCheck"
    assert dialog._confirm_close_check.objectName() == "prefConfirmCloseCheck"
    assert dialog._recent_files_spin.objectName() == "prefRecentFilesSpin"
    assert dialog._default_thumb_size_spin.objectName() == "prefDefaultThumbSizeSpin"
    assert dialog._high_contrast_check.objectName() == "prefHighContrastCheck"
    assert dialog._reduced_motion_check.objectName() == "prefReducedMotionCheck"

    assert dialog.button_box.objectName() == "prefButtonBox"
    assert dialog.button_box.button(Std.Ok).objectName() == "prefOkBtn"
    assert dialog.button_box.button(Std.Cancel).objectName() == "prefCancelBtn"
    assert dialog.button_box.button(Std.RestoreDefaults).objectName() == "prefRestoreBtn"
