"""PreferencesDialog accessibility, hand cursors and headless-safe Restore Defaults."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")
from PySide6 import QtCore, QtWidgets

from valis_workstation.ui.dialogs.preferences_dialog import PreferencesDialog

_CONTROLS = [
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


def test_every_control_is_named_and_described(dialog):
    names = set()
    for attr in _CONTROLS:
        w = getattr(dialog, attr)
        assert w.objectName(), attr
        assert w.accessibleName(), attr
        assert w.toolTip(), attr
        names.add(w.objectName())
    assert len(names) == len(_CONTROLS)


def test_clickable_controls_use_pointing_hand(dialog):
    for attr in ("_browse_cache_btn", "_persist_cache_check", "_high_contrast_check"):
        assert getattr(dialog, attr).cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
    box = dialog.findChild(QtWidgets.QDialogButtonBox)
    for std in (
        QtWidgets.QDialogButtonBox.StandardButton.Ok,
        QtWidgets.QDialogButtonBox.StandardButton.RestoreDefaults,
    ):
        assert box.button(std).cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor


def test_restore_defaults_does_not_block_headless(dialog, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("modal shown in headless run")

    monkeypatch.setattr(QtWidgets.QMessageBox, "question", boom)
    dialog._max_thumb_cache_spin.setValue(1234)
    dialog._high_contrast_check.setChecked(True)
    dialog._restore_defaults()
    assert dialog._max_thumb_cache_spin.value() == 500
    assert not dialog._high_contrast_check.isChecked()
