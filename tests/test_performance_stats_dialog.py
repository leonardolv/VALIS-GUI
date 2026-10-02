"""Tests for PerformanceStatsDialog accessibility, tooltips, and headless cache clearance."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore
from valis_workstation.ui.dialogs.performance_stats_dialog import (
    PerformanceStatsDialog,
)


def test_performance_stats_dialog_accessibility_and_tooltips(qtbot):
    dialog = PerformanceStatsDialog()
    qtbot.addWidget(dialog)

    # Accessible names
    assert dialog._refresh_btn.accessibleName() == "Refresh Performance Statistics"
    assert dialog._clear_thumb_cache_btn.accessibleName() == "Clear Thumbnail Cache"
    assert dialog._close_btn.accessibleName() == "Close Dialog"
    assert dialog._thumb_cache_bar.accessibleName() == "Thumbnail Cache Usage"

    # Tooltips
    assert "refresh" in dialog._refresh_btn.toolTip().lower()
    assert "thumbnail" in dialog._clear_thumb_cache_btn.toolTip().lower()
    assert "close" in dialog._close_btn.toolTip().lower()

    # Cursors
    assert dialog._refresh_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
    assert dialog._clear_thumb_cache_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor
    assert dialog._close_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor


def test_performance_stats_dialog_refresh_action(qtbot):
    dialog = PerformanceStatsDialog()
    qtbot.addWidget(dialog)

    # Click refresh
    dialog._refresh_btn.click()
    assert dialog._update_timer.isActive()


def test_performance_stats_dialog_clear_cache_headless(qtbot):
    dialog = PerformanceStatsDialog()
    qtbot.addWidget(dialog)

    # Click clear thumbnail cache in headless mode without blocking
    dialog._clear_thumb_cache_btn.click()
    assert dialog._thumb_total_label.text() is not None
