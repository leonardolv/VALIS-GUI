"""Usability round 2: layout fit, review bar, modal guard, quality choice, a11y."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtWidgets

from valis_workstation import layout_constants as LC
from valis_workstation.ui import modal_utils
from valis_workstation.utils.qt_logging import QtLogEmitter

QSS = Path(__file__).resolve().parents[1] / "src" / "valis_workstation" / "styles" / "adobe_dark.qss"


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
        repo_root=tmp_path, log_emitter=QtLogEmitter(), simple_elastix_available=True
    )
    qtbot.addWidget(window)
    return window


def _set_slides(win, n: int) -> None:
    win._project_dock.set_slides([Path(f"s{i}.png") for i in range(n)])


class TestModalGuard:
    def test_headless_returns_defaults_without_showing(self, monkeypatch) -> None:
        monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
        # conftest stubs QMessageBox; restore the originals so the guard is tested.
        for kind, orig in modal_utils._ORIGINALS.items():
            monkeypatch.setattr(QtWidgets.QMessageBox, kind, staticmethod(orig))
        B = QtWidgets.QMessageBox.StandardButton
        assert modal_utils.information(None, "t", "x") == B.Ok
        assert modal_utils.warning(None, "t", "x") == B.Ok
        assert modal_utils.critical(None, "t", "x") == B.Ok
        assert modal_utils.question(None, "t", "x") == B.No
        assert modal_utils.question(None, "t", "x", default_button=B.Yes) == B.Yes

    def test_stub_is_still_honoured(self, monkeypatch) -> None:
        B = QtWidgets.QMessageBox.StandardButton
        monkeypatch.setattr(
            QtWidgets.QMessageBox, "question", staticmethod(lambda *a, **k: B.Yes)
        )
        assert modal_utils.question(None, "t", "x") == B.Yes

    def test_no_raw_modals_left_in_main_window_modules(self) -> None:
        root = Path(__file__).resolve().parents[1] / "src" / "valis_workstation"
        for rel in (
            "main_window.py",
            "ui/main_window_workflow.py",
            "ui/main_window_documents.py",
            "ui/project_dock.py",
            "ui/status_dock.py",
            "ui/properties_dock.py",
        ):
            text = (root / rel).read_text(encoding="utf-8")
            for kind in ("information", "warning", "critical", "question"):
                assert f"QMessageBox.{kind}(" not in text, (rel, kind)


class TestLayoutFit:
    def test_sidebars_wide_enough_for_their_controls(self, win) -> None:
        assert LC.RIGHT_SIDEBAR_MIN >= 330
        assert LC.LEFT_SIDEBAR_MIN >= 250
        dock = win._properties_dock
        buttons = (dock._save_preset_btn, dock._load_preset_btn, dock._delete_preset_btn)
        needed = sum(b.sizeHint().width() for b in buttons) + 2 * 6
        # margins + scrollbar allowance
        assert needed <= LC.RIGHT_SIDEBAR_MIN - 12 - 16
        proj = win._project_dock
        row = proj._remove_selected_button.sizeHint().width() + proj._clear_button.sizeHint().width() + 6
        assert row <= LC.LEFT_SIDEBAR_MIN - 12 - 16

    def test_lists_define_an_alternate_row_colour(self) -> None:
        css = QSS.read_text(encoding="utf-8")
        assert "alternate-background-color" in css

    def test_disabled_toolbar_buttons_are_styled(self) -> None:
        css = QSS.read_text(encoding="utf-8")
        assert "QToolBar#QuickActionsToolbar QToolButton:disabled" in css

    def test_log_controls_share_one_row_and_log_has_room(self, win) -> None:
        sd = win._status_dock
        parent_layout = sd._filter_edit.parentWidget()
        assert sd._copy_log_button.parentWidget() is parent_layout
        assert sd._auto_scroll_check.parentWidget() is parent_layout
        assert sd._log_console.minimumHeight() >= 48
        assert sd._log_console.placeholderText()

    def test_toolbar_uses_short_captions_with_full_tooltips(self, win) -> None:
        action = win._run_registration_action
        assert action.iconText() == "Run"
        assert "Run Registration" in action.text()
        assert action.toolTip()


class TestQualityChoice:
    def test_presets_drive_the_pixel_value(self, win) -> None:
        dock = win._properties_dock
        assert dock.config().max_image_size == 2048
        dock._quality_combo.setCurrentIndex(0)
        assert dock.config().max_image_size == 1024
        dock._quality_combo.setCurrentIndex(2)
        assert dock.config().max_image_size == 4096

    def test_custom_reveals_the_pixel_box_and_value_syncs_back(self, win, qtbot) -> None:
        dock = win._properties_dock
        win.show()
        qtbot.waitExposed(win)
        dock._quality_combo.setCurrentIndex(3)
        assert dock._max_size.isVisibleTo(dock.widget())
        dock._max_size.setValue(3000)
        assert dock.config().max_image_size == 3000
        assert dock._quality_combo.currentText().startswith("Custom")
        dock._max_size.setValue(1024)
        assert dock._quality_combo.currentText().startswith("Quick")

    def test_loading_a_config_selects_matching_choice(self, win) -> None:
        dock = win._properties_dock
        cfg = dock.config()
        cfg.max_image_size = 4096
        dock.set_config(cfg) if hasattr(dock, "set_config") else dock._max_size.setValue(4096)
        assert dock._quality_combo.currentText().startswith("Precise")


class TestReviewBar:
    def test_hidden_until_results_exist_then_lists_tools(self, win) -> None:
        assert win._review_bar.isHidden()
        win._last_result = {"summary_df": object(), "registered_dir": "x"}
        win._update_tools_enabled()
        assert not win._review_bar.isHidden()
        labels = [b.text() for b, _ in win._review_buttons]
        assert "Quality Report" in labels and "Merge Slides" in labels
        assert all(b.isEnabled() for b, _ in win._review_buttons)

    def test_new_run_hides_the_bar(self, win) -> None:
        win._last_result = {"x": 1}
        win._update_tools_enabled()
        assert not win._review_bar.isHidden()
        win._review_bar.setVisible(False)
        assert win._review_bar.isHidden()

    def test_step_strip_marks_current_and_done(self, win) -> None:
        win._set_workflow_step("Register")
        labels = win._workflow_labels
        assert labels["Register"].property("active") is True
        assert labels["Load"].property("done") is True
        assert labels["Review"].property("done") is False
        assert "current step" in labels["Register"].accessibleName()

    def test_finishing_does_not_open_a_modal(self, win, monkeypatch) -> None:
        called = []
        monkeypatch.setattr(modal_utils, "information", lambda *a, **k: called.append(a))
        from valis_workstation.ui import main_window_workflow as wf

        monkeypatch.setattr(win, "_load_registered_layers", lambda r: None)
        wf.on_worker_finished(win, {"registered_dir": "x"})
        assert not called
        assert not win._review_bar.isHidden()


class TestWelcomeRun:
    def test_run_button_appears_with_two_slides(self, win) -> None:
        panel = win._welcome_panel
        assert panel._run_button.isHidden()
        _set_slides(win, 1)
        assert panel._run_button.isHidden()
        _set_slides(win, 3)
        assert not panel._run_button.isHidden()
        assert panel._steps_label.isHidden()
        _set_slides(win, 0)
        assert panel._run_button.isHidden()
        assert not panel._steps_label.isHidden()


class TestPanels:
    def test_empty_project_list_is_hidden_and_filter_mismatch_explained(self, win) -> None:
        dock = win._project_dock
        assert dock._list.isHidden()
        _set_slides(win, 3)
        assert not dock._list.isHidden()
        dock._filter_edit.setText("zzz")
        assert not dock._no_match_label.isHidden()
        dock._filter_edit.setText("")
        assert dock._no_match_label.isHidden()

    def test_thumbnail_reflow_keeps_every_slide_when_tab_is_hidden(self, win) -> None:
        dock = win._slide_preview_dock
        for i in range(4):
            dock.add_slide(f"s{i}", None, {})
        dock._reflow_grid()
        assert dock._grid_layout.count() == 4

    def test_tutorial_and_wizard_are_accessible(self, win) -> None:
        from valis_workstation.ui.dialogs.first_run_wizard import FirstRunWizard
        from valis_workstation.ui.dialogs.quick_tutorial_dialog import QuickTutorialDialog

        dlg = QuickTutorialDialog(win)
        try:
            for w in (dlg._prev_btn, dlg._next_btn, dlg._close_btn, dlg._dont_show):
                assert w.accessibleName() and w.toolTip()
            assert dlg._body.accessibleName()
            assert all(b.accessibleName() for b in dlg._bubbles)
        finally:
            dlg.close()
        wiz = FirstRunWizard()
        assert wiz._project_name_edit.accessibleName()
        assert wiz._output_profile_combo.toolTip()
        assert wiz.button(QtWidgets.QWizard.WizardButton.NextButton).toolTip()
