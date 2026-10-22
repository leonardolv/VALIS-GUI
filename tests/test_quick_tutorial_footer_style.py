"""The tutorial footer's "Don't show" checkbox must be visible and legible."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtWidgets
from valis_workstation.ui.dialogs.quick_tutorial_dialog import QuickTutorialDialog


def _luminance(hex_color: str) -> float:
    rgb = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _contrast(a: str, b: str) -> float:
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


@pytest.fixture
def dialog(qtbot):
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    dlg = QuickTutorialDialog(parent)  # type: ignore[arg-type]
    qtbot.addWidget(dlg)
    return dlg


def test_footer_border_is_scoped_to_the_footer(dialog):
    footer = dialog.findChild(QtWidgets.QFrame, "tutorialFooter")
    assert footer is not None
    # An unscoped rule would also draw border-top on every child widget.
    assert footer.styleSheet().lstrip().startswith("QFrame#tutorialFooter")


def test_checkbox_indicator_is_drawn_and_label_readable(dialog):
    style = dialog._dont_show.styleSheet()
    assert "QCheckBox::indicator" in style and "border: 1px solid" in style
    assert "QCheckBox::indicator:checked" in style
    assert _contrast("#94a3b8", "#1e293b") >= 4.5
