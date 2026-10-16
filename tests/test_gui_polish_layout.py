"""Headless regression tests for the 2026-10 layout/contrast polish pass."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6 import QtCore, QtWidgets

ROOT = Path(__file__).resolve().parents[1]


def test_stylesheet_has_no_unresolved_placeholder_and_arrow_files_exist():
    from valis_workstation.utils.accessibility import base_stylesheet

    css = base_stylesheet(ROOT)
    assert "@STYLES_DIR@" not in css
    assert "arrow_down.svg" in css and "check.svg" in css
    styles = ROOT / "src" / "valis_workstation" / "styles"
    for name in ("arrow_up.svg", "arrow_down.svg", "check.svg"):
        assert (styles / name).is_file()


def test_status_dock_filter_and_log_buttons_share_one_row(qtbot):
    from valis_workstation.ui.status_dock import StatusDock
    from valis_workstation.utils.qt_logging import QtLogEmitter

    dock = StatusDock(QtLogEmitter())
    qtbot.addWidget(dock)
    dock.resize(600, 220)
    dock.show()
    qtbot.wait(20)
    f, c = dock._filter_edit.geometry(), dock._copy_log_button.geometry()
    assert abs(f.center().y() - c.center().y()) < 12
    assert not f.intersects(c)
    assert dock._log_console.height() > 40


def test_welcome_panel_scrolls_instead_of_clipping(qtbot):
    from valis_workstation.ui.welcome_panel import WelcomePanel

    panel = WelcomePanel()
    qtbot.addWidget(panel)
    scroll = panel.findChild(QtWidgets.QScrollArea, "WelcomeScroll")
    assert scroll is not None and scroll.widgetResizable()


def test_slide_preview_controls_are_two_rows(qtbot):
    from valis_workstation.ui.slide_preview_dock import SlidePreviewDock

    dock = SlidePreviewDock()
    qtbot.addWidget(dock)
    dock.resize(240, 500)
    dock.show()
    qtbot.wait(20)
    assert dock._grid_view.text() == "" and dock._grid_view.accessibleName()
    assert dock._grid_view.geometry().right() <= dock.width()
    assert dock._list_view.geometry().right() <= dock.width()


def test_toolbar_goes_icon_only_when_labels_do_not_fit(qtbot, tmp_path):
    from valis_workstation.main_window import MainWindow
    from valis_workstation.utils.qt_logging import QtLogEmitter

    w = MainWindow(
        repo_root=tmp_path, log_emitter=QtLogEmitter(), simple_elastix_available=False
    )
    qtbot.addWidget(w)
    w.resize(1000, 700)
    w.show()
    qtbot.wait(50)
    tb = w.findChild(QtWidgets.QToolBar, "QuickActionsToolbar")
    assert tb.toolButtonStyle() == QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly
    w.resize(2200, 800)
    qtbot.wait(50)
    assert tb.toolButtonStyle() == QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon


def test_dialog_info_text_is_not_dark_on_light():
    for rel in ("merge_slides_dialog.py",):
        src = (ROOT / "src/valis_workstation/ui/dialogs" / rel).read_text()
        assert "#e8f4f8" not in src
    for rel in ("save_options_dialog.py", "preferences_dialog.py"):
        src = (ROOT / "src/valis_workstation/ui/dialogs" / rel).read_text()
        assert "color: gray" not in src and "color: #888;" not in src


def test_strenum_compat_str_is_value():
    from valis_workstation.compat import StrEnum

    class E(StrEnum):
        A = "a-value"

    assert str(E.A) == "a-value" and E.A == "a-value"
