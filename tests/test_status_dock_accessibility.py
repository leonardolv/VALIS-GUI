"""Unit tests for StatusDock accessibility metadata, object names, public properties, ergonomics helpers, and action triggers."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6 import QtCore, QtWidgets

from valis_workstation.ui.status_dock import StatusDock
from valis_workstation.utils.qt_logging import QtLogEmitter


@pytest.fixture
def dock(qtbot):
    emitter = QtLogEmitter()
    d = StatusDock(emitter)
    qtbot.addWidget(d)
    yield d
    d._timing_timer.stop()


class TestStatusDockAccessibilityAndErgonomics:
    def test_status_dock_metadata_and_object_names(self, dock) -> None:
        # 1. Dock accessibility metadata
        assert dock.objectName() == "StatusDock"
        assert dock.accessibleName() == "Pipeline Status and Log Dock"
        assert "Displays registration pipeline progress" in dock.accessibleDescription()

        # 2. Public properties, object names, and pointer cursor affordances
        assert dock.progress_bar.objectName() == "statusProgressBar"
        assert dock.progress_bar.accessibleName() == "Pipeline Progress"
        assert "percentage" in dock.progress_bar.accessibleDescription()

        assert dock.stage_label.objectName() == "statusStageLabel"
        assert dock.stage_label.accessibleName() == "Pipeline Stage"

        assert dock.timing_label.objectName() == "statusTimingLabel"
        assert dock.timing_label.accessibleName() == "Stage Timing and ETA"

        assert dock.filter_edit.objectName() == "statusLogFilterEdit"
        assert dock.filter_edit.accessibleName() == "Filter Log Lines"
        assert len(dock.filter_edit.accessibleDescription()) > 0

        assert dock.auto_scroll_checkbox.objectName() == "statusAutoScrollCheck"
        assert dock.auto_scroll_checkbox.accessibleName() == "Auto-scroll Log"
        assert dock.auto_scroll_checkbox.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

        assert dock.clear_button.objectName() == "statusClearLogBtn"
        assert dock.clear_button.accessibleName() == "Clear Log"
        assert dock.clear_button.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

        assert dock.copy_button.objectName() == "statusCopyLogBtn"
        assert dock.copy_button.accessibleName() == "Copy Log"
        assert dock.copy_button.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

        assert dock.cancel_button.objectName() == "statusCancelBtn"
        assert dock.cancel_button.accessibleName() == "Cancel Registration"
        assert dock.cancel_button.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

        assert dock.log_console.objectName() == "statusLogConsole"
        assert dock.log_console.accessibleName() == "Registration Log Console"
        assert len(dock.log_console.accessibleDescription()) > 0

    def test_status_dock_ergonomics_queries_and_setters(self, dock) -> None:
        # Initial state queries
        assert dock.progress_value() == 0
        assert dock.stage_text() == "Idle"
        assert "Elapsed: 00:00:00" in dock.timing_text()
        assert dock.log_line_count() == 0
        assert dock.log_lines() == []
        assert dock.log_text() == ""
        assert dock.console_text() == ""
        assert dock.filter_text() == ""
        assert dock.is_auto_scroll_enabled() is True
        assert dock.is_cancel_visible() is False

        # Setters and mutations
        dock.set_progress(45)
        assert dock.progress_value() == 45

        dock.set_stage("Rigid Registration")
        assert dock.stage_text() == "Rigid Registration"

        dock.set_auto_scroll_enabled(False)
        assert dock.is_auto_scroll_enabled() is False

        dock.show_cancel_button(True)
        assert dock.is_cancel_visible() is True

        dock.show_cancel_button(False)
        assert dock.is_cancel_visible() is False

    def test_status_dock_log_filtering_and_action_triggers(self, dock, tmp_path) -> None:
        # Append lines
        dock.append_log_line("Initialization complete")
        dock.append_log_line("Processing slide 001 - Liver")
        dock.append_log_line("Processing slide 002 - Kidney")
        dock.append_log_line("Finished successfully")

        assert dock.log_line_count() == 4
        assert len(dock.log_lines()) == 4
        assert "slide 001" in dock.log_text()

        # Filter lines
        dock.set_filter_text("Kidney")
        assert dock.filter_text() == "Kidney"
        assert "Kidney" in dock.console_text()
        assert "Liver" not in dock.console_text()

        # Reset filter
        dock.set_filter_text("")
        assert "Liver" in dock.console_text()
        assert "Kidney" in dock.console_text()

        # Copy log trigger
        dock.trigger_copy_log()

        # Save log as trigger with explicit path
        target = tmp_path / "registration_log.txt"
        assert dock._save_log_as(str(target)) is True
        assert target.exists()
        assert "Liver" in target.read_text(encoding="utf-8")

        # Headless save log without path
        assert dock._save_log_as(None) is True

        # Cancel trigger
        cancelled = []
        dock.connect_cancel(lambda: cancelled.append(True))
        dock.trigger_cancel()
        assert cancelled == [True]

        # Clear log trigger in headless environment
        dock.trigger_clear_log()
        assert dock.log_line_count() == 0
        assert dock.console_text() == ""
