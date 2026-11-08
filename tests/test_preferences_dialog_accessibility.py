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


def test_preferences_dialog_properties_and_ergonomics(dialog):
    # Verify child property accessors
    assert dialog.cache_dir_edit is dialog._cache_dir_edit
    assert dialog.browse_cache_button is dialog._browse_cache_btn
    assert dialog.max_thumb_cache_spin is dialog._max_thumb_cache_spin
    assert dialog.persist_cache_check is dialog._persist_cache_check
    assert dialog.parallel_workers_spin is dialog._parallel_workers_spin
    assert dialog.perf_monitoring_check is dialog._perf_monitoring_check
    assert dialog.auto_refresh_spin is dialog._auto_refresh_spin
    assert dialog.show_tooltips_check is dialog._show_tooltips_check
    assert dialog.show_statusbar_check is dialog._show_statusbar_check
    assert dialog.confirm_close_check is dialog._confirm_close_check
    assert dialog.recent_files_spin is dialog._recent_files_spin
    assert dialog.default_thumb_size_spin is dialog._default_thumb_size_spin
    assert dialog.high_contrast_check is dialog._high_contrast_check
    assert dialog.reduced_motion_check is dialog._reduced_motion_check
    assert dialog.ok_button is not None
    assert dialog.cancel_button is not None
    assert dialog.restore_defaults_button is not None

    # Verify query and setter helpers
    dialog.set_cache_directory("/tmp/custom_cache")
    assert dialog.cache_directory() == "/tmp/custom_cache"

    dialog.set_max_thumbnail_cache_mb(800)
    assert dialog.max_thumbnail_cache_mb() == 800

    dialog.set_cache_persisted(False)
    assert dialog.is_cache_persisted() is False
    dialog.set_cache_persisted(True)
    assert dialog.is_cache_persisted() is True

    dialog.set_parallel_workers(8)
    assert dialog.parallel_workers() == 8

    dialog.set_perf_monitoring_enabled(False)
    assert dialog.is_perf_monitoring_enabled() is False
    dialog.set_perf_monitoring_enabled(True)
    assert dialog.is_perf_monitoring_enabled() is True

    dialog.set_auto_refresh_seconds(5)
    assert dialog.auto_refresh_seconds() == 5

    dialog.set_show_tooltips_enabled(False)
    assert dialog.is_show_tooltips_enabled() is False
    dialog.set_show_tooltips_enabled(True)
    assert dialog.is_show_tooltips_enabled() is True

    dialog.set_show_statusbar_enabled(False)
    assert dialog.is_show_statusbar_enabled() is False
    dialog.set_show_statusbar_enabled(True)
    assert dialog.is_show_statusbar_enabled() is True

    dialog.set_confirm_close_enabled(True)
    assert dialog.is_confirm_close_enabled() is True
    dialog.set_confirm_close_enabled(False)
    assert dialog.is_confirm_close_enabled() is False

    dialog.set_recent_files_count(15)
    assert dialog.recent_files_count() == 15

    dialog.set_default_thumbnail_size(256)
    assert dialog.default_thumbnail_size() == 256

    dialog.set_high_contrast_enabled(True)
    assert dialog.is_high_contrast_enabled() is True
    dialog.set_high_contrast_enabled(False)
    assert dialog.is_high_contrast_enabled() is False

    dialog.set_reduced_motion_enabled(True)
    assert dialog.is_reduced_motion_enabled() is True
    dialog.set_reduced_motion_enabled(False)
    assert dialog.is_reduced_motion_enabled() is False

    # Category switching
    assert dialog.current_category() == "Cache"
    assert dialog.set_category("Performance") is True
    assert dialog.current_category() == "Performance"
    assert dialog.set_category("User Interface") is True
    assert dialog.current_category() == "User Interface"
    assert dialog.set_category("Nonexistent") is False

    # Headless restore defaults trigger
    dialog.trigger_restore_defaults()
    assert dialog.max_thumbnail_cache_mb() == 500
    assert dialog.parallel_workers() == 4

    # Trigger accept & reject
    dialog.trigger_reject()
    dialog.trigger_accept()
