"""StatusDock timing label must stop updating once a run completes."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import time

import pytest
from PySide6 import QtWidgets

from valis_workstation.ui.status_dock import StatusDock
from valis_workstation.utils.qt_logging import QtLogEmitter


@pytest.fixture(scope="module")
def qapp():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def dock(qapp):
    d = StatusDock(QtLogEmitter())
    yield d
    d._timing_timer.stop()


def test_complete_label_survives_timer_tick(dock):
    dock.set_stage("Starting")
    dock._run_started_at = time.time() - 90
    dock.set_progress(50)
    dock._update_timing()
    assert "01:30" in dock._timing_label.text()
    dock.set_progress(100)
    dock._update_timing()
    assert dock._timing_label.text() == "Elapsed: complete | ETA: 00:00:00"


def test_reset_clears_label_and_ticks_are_noop(dock):
    dock.set_stage("Starting")
    dock.set_progress(40)
    dock.reset_progress()
    dock._update_timing()
    assert dock._timing_label.text() == "Elapsed: 00:00:00 | ETA: --:--:--"
