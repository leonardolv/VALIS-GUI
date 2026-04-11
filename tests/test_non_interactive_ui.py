from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtWidgets


def test_modal_message_boxes_are_non_blocking() -> None:
    result = QtWidgets.QMessageBox.question(None, "Title", "Body")
    assert result == QtWidgets.QMessageBox.StandardButton.No


def test_file_dialogs_return_empty_defaults() -> None:
    open_result = QtWidgets.QFileDialog.getOpenFileName(None, "Pick file")
    save_result = QtWidgets.QFileDialog.getSaveFileName(None, "Save file")
    dir_result = QtWidgets.QFileDialog.getExistingDirectory(None, "Pick folder")

    assert open_result == ("", "")
    assert save_result == ("", "")
    assert dir_result == ""


def test_warning_message_box_returns_ok() -> None:
    result = QtWidgets.QMessageBox.warning(None, "Title", "Body")
    assert result == QtWidgets.QMessageBox.StandardButton.Ok
