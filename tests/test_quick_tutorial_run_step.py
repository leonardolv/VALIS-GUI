"""The tutorial's Run action must only advance when a run actually started."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets
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
    assert dialog.objectName() == "quickTutorialDialog"
    assert dialog.accessibleName() == "Quick Tutorial Dialog"
    assert dialog.accessibleDescription() == "Interactive beginner tutorial for VALIS Workstation"
    assert " - " in dialog.windowTitle()
    assert "—" not in dialog.windowTitle()

    assert dialog._icon_label.objectName() == "tutorialIconLabel"
    assert dialog._icon_label.accessibleName() == "Tutorial step icon"

    assert dialog._title_label.objectName() == "tutorialTitleLabel"
    assert dialog._title_label.accessibleName() == "Tutorial step title"

    assert dialog._step_counter.objectName() == "tutorialStepCounter"
    assert dialog._step_counter.accessibleName() == "Tutorial step counter"

    assert dialog._body.objectName() == "tutorialBody"
    assert dialog._action_btn.objectName() == "tutorialActionBtn"
    assert dialog._dont_show.objectName() == "tutorialDontShowCheck"
    assert dialog._dont_show.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
    assert dialog._prev_btn.objectName() == "tutorialPrevBtn"
    assert dialog._next_btn.objectName() == "tutorialNextBtn"
    assert dialog._close_btn.objectName() == "tutorialCloseBtn"

    for i, bubble in enumerate(dialog._bubbles):
        assert bubble.objectName() == f"tutorialBubble_{i}"
        assert bubble.accessibleName() == f"Step {i + 1} indicator"
        assert f"Step {i + 1} of" in bubble.toolTip()

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


def test_finish_step_updates_close_button_accessibility(qtbot):
    from valis_workstation.ui.dialogs.quick_tutorial_dialog import _STEPS
    _, dialog = _dialog(qtbot, starts=False)
    dialog._show_step(len(_STEPS) - 1)
    assert dialog._close_btn.text() == "Finish"
    assert dialog._close_btn.accessibleName() == "Finish tutorial"
    assert "Finish" in dialog._close_btn.toolTip()


def test_quick_tutorial_dialog_query_and_navigation_helpers(qtbot):
    _, dialog = _dialog(qtbot, starts=False)
    assert dialog.total_steps == 13

    dialog.go_to_step(0)
    assert dialog.current_step == 0
    assert dialog.is_first_step() is True
    assert dialog.is_last_step() is False
    assert dialog.can_go_prev() is False
    assert dialog.can_go_next() is True
    assert "Welcome" in dialog.step_title

    dialog.next_step()
    assert dialog.current_step == 1
    assert dialog.can_go_prev() is True

    dialog.prev_step()
    assert dialog.current_step == 0

    dialog.go_to_step(dialog.total_steps - 1)
    assert dialog.current_step == dialog.total_steps - 1
    assert dialog.is_last_step() is True
    assert dialog.can_go_next() is False
    assert dialog.can_go_prev() is True
    assert "Ready" in dialog.step_title
