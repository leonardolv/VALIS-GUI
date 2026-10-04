"""QuickTutorialDialog's auto-advance poll timer must stop when dismissed."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtWidgets
from valis_workstation.ui.dialogs.quick_tutorial_dialog import QuickTutorialDialog


@pytest.mark.parametrize("finish", ["accept", "reject"])
def test_poll_timer_stops_when_dismissed(qtbot, finish):
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    dialog = QuickTutorialDialog(parent)
    qtbot.addWidget(dialog)
    assert dialog._poll_timer.isActive()
    getattr(dialog, finish)()
    assert not dialog._poll_timer.isActive()
