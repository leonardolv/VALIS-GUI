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
