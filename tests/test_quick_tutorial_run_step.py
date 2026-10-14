"""The tutorial's Run action must only advance when a run actually started."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtWidgets
from valis_workstation.ui.dialogs.quick_tutorial_dialog import QuickTutorialDialog

RUN_STEP = 5


class _FakeWindow(QtWidgets.QWidget):
    """Stands in for MainWindow; ``_start_registration`` never pops a dialog."""

    def __init__(self, starts: bool) -> None:
        super().__init__()
        self._starts = starts
        self._worker = None
        self.calls = 0

    def _start_registration(self) -> None:
        self.calls += 1
        if self._starts:
            self._worker = object()


def _dialog(qtbot, starts: bool):
    win = _FakeWindow(starts)
    qtbot.addWidget(win)
    dialog = QuickTutorialDialog(win)  # type: ignore[arg-type]
    qtbot.addWidget(dialog)
    dialog._show_step(RUN_STEP)
    return win, dialog


def test_run_declined_stays_on_run_step(qtbot):
    win, dialog = _dialog(qtbot, starts=False)
    dialog._on_action_clicked()
    assert win.calls == 1
    assert dialog._current_step == RUN_STEP


def test_run_started_advances_to_wait_step(qtbot):
    win, dialog = _dialog(qtbot, starts=True)
    dialog._on_action_clicked()
    assert dialog._current_step == RUN_STEP + 1


def test_controls_have_accessible_names(qtbot):
    _, dialog = _dialog(qtbot, starts=False)
    for w in (
        dialog._prev_btn,
        dialog._next_btn,
        dialog._close_btn,
        dialog._action_btn,
        dialog._dont_show,
        dialog._body,
    ):
        assert w.accessibleName(), w
    for b in (dialog._prev_btn, dialog._next_btn, dialog._close_btn, dialog._action_btn):
        assert b.toolTip()
