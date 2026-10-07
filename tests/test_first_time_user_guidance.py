"""First-time-user guidance: welcome page, next-step hint, Run availability."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtWidgets

from valis_workstation.utils.qt_logging import QtLogEmitter


@pytest.fixture()
def win(qtbot, tmp_path, monkeypatch):
    from valis_workstation.main_window import MainWindow

    original = importlib.util.find_spec
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda name, *a, **k: None if name == "napari" else original(name, *a, **k),
    )
    window = MainWindow(
        repo_root=tmp_path, log_emitter=QtLogEmitter(), simple_elastix_available=False
    )
    qtbot.addWidget(window)
    return window


def _set_slides(win, n: int) -> None:
    win._project_dock.set_slides([Path(f"s{i}.png") for i in range(n)])


class TestWelcomePanel:
    def test_welcome_replaces_error_style_message(self, win) -> None:
        panel = win._welcome_panel
        texts = " ".join(l.text() for l in panel.findChildren(QtWidgets.QLabel))
        assert "Welcome to VALIS Workstation" in texts
        assert "Not Available" not in texts
        # the optional-viewer notice is a footnote, not the headline
        assert panel.findChild(QtWidgets.QLabel, "WelcomeViewerNote") is not None

    def test_open_button_triggers_open_folder(self, win, monkeypatch) -> None:
        called = []
        monkeypatch.setattr(win, "_open_slide_folder", lambda: called.append(1))
        panel = win._welcome_panel
        panel.open_folder_requested.disconnect()
        panel.open_folder_requested.connect(win._open_slide_folder)
        panel._open_button.click()
        assert called

    def test_status_follows_slide_count(self, win) -> None:
        panel = win._welcome_panel
        assert panel._status_label.isHidden()
        _set_slides(win, 1)
        assert "at least one more" in panel._status_label.text()
        _set_slides(win, 3)
        assert "3 slides loaded" in panel._status_label.text()
        _set_slides(win, 0)
        assert panel._status_label.isHidden()


class TestWorkflowStrip:
    def test_steps_are_numbered_and_hint_updates(self, win) -> None:
        assert win._workflow_labels["Load"].text() == "1. Load"
        assert "Ctrl+O" in win._workflow_hint.text()
        win._set_workflow_step("Configure")
        assert "Run Registration" in win._workflow_hint.text()
        win._set_workflow_step("Review")
        assert "Blink" in win._workflow_hint.text()


class TestRunAvailability:
    def test_run_disabled_until_two_slides_with_reason(self, win) -> None:
        run = win._run_registration_action
        assert not run.isEnabled()
        assert "Ctrl+O" in run.toolTip()
        _set_slides(win, 1)
        assert not run.isEnabled()
        assert "only 1" in run.toolTip()
        _set_slides(win, 2)
        assert run.isEnabled()

    def test_running_disables_run_and_finishing_restores(self, win) -> None:
        _set_slides(win, 2)
        win._set_registration_running(True)
        assert not win._run_registration_action.isEnabled()
        win._set_registration_running(False)
        assert win._run_registration_action.isEnabled()


class TestProjectDockEmptyState:
    def test_empty_state_has_open_button(self, win, qtbot) -> None:
        dock = win._project_dock
        assert not dock._open_folder_button.isHidden()
        _set_slides(win, 2)
        assert dock._open_folder_button.isHidden()
        with qtbot.waitSignal(dock.open_folder_requested):
            _set_slides(win, 0)
            dock._open_folder_button.click()


class TestPlainLanguageLabels:
    def test_settings_use_plain_labels(self, win) -> None:
        form_labels = {
            l.text() for l in win._right_tabs.widget(0).findChildren(QtWidgets.QLabel)
        }
        assert "Align slides (rigid)" in form_labels
        assert "Fix tissue warping (non-rigid)" in form_labels
        assert "Working resolution" in form_labels
        assert "Max image size" not in form_labels


def test_wizard_explains_workflow(qtbot) -> None:
    from valis_workstation.ui.dialogs.first_run_wizard import FirstRunWizard

    wz = FirstRunWizard()
    qtbot.addWidget(wz)
    text = " ".join(l.text() for l in wz.page(0).findChildren(QtWidgets.QLabel))
    assert "Load" in text and "Review" in text
    opts = " ".join(l.text() for l in wz.page(1).findChildren(QtWidgets.QLabel))
    assert "Fast Review" in opts and "Publication" in opts
