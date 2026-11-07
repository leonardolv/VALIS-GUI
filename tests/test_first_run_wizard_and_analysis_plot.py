from __future__ import annotations

import pandas as pd
from PySide6 import QtCore, QtWidgets

from valis_workstation.ui.dialogs.analysis_plot import AnalysisPlotDialog
from valis_workstation.ui.dialogs.first_run_wizard import FirstRunWizard
from valis_workstation.ui.dialogs.quick_tutorial_dialog import QuickTutorialDialog


def test_first_run_wizard_accessibility_and_affordances(qtbot):
    wizard = FirstRunWizard()
    qtbot.addWidget(wizard)

    assert wizard.objectName() == "first_run_wizard"
    assert wizard.accessibleName() == "VALIS Workstation Setup Wizard"
    assert "setup wizard" in wizard.accessibleDescription().lower()

    # Widget properties
    assert wizard.project_name_edit is wizard._project_name_edit
    assert wizard.output_profile_combo is wizard._output_profile_combo
    assert wizard.open_tutorial_check is wizard._open_tutorial_check
    assert wizard.welcome_page is wizard._welcome_page
    assert wizard.options_page is wizard._options_page
    assert wizard.finish_page is wizard._finish_page

    assert wizard.project_name_edit.accessibleName() == "Default project name"
    assert wizard.project_name_edit.placeholderText() != ""
    assert "default project name" in wizard.project_name_edit.toolTip().lower()

    assert wizard.output_profile_combo.accessibleName() == "Default output profile"
    assert "preset profile" in wizard.output_profile_combo.toolTip().lower()
    assert wizard.output_profile_combo.cursor().shape() == QtCore.Qt.PointingHandCursor

    assert wizard.selected_project_name() == "New Project"
    assert wizard.selected_output_profile() == "WSI Archive"
    assert wizard.has_valid_project_name() is True
    assert wizard.output_profiles() == ["WSI Archive", "Fast Review", "Publication"]

    wizard.set_project_name("Cohort_A")
    wizard.set_output_profile("Publication")
    assert wizard.selected_project_name() == "Cohort_A"
    assert wizard.selected_output_profile() == "Publication"
    assert wizard.has_valid_project_name() is True

    wizard.set_project_name("   ")
    assert wizard.has_valid_project_name() is False
    assert wizard.selected_project_name() == "New Project"

    assert wizard.open_tutorial_check.objectName() == "first_run_open_tutorial_check"
    assert wizard.open_tutorial_check.accessibleName() == "Open Quick Tutorial when finished"
    assert "tutorial" in wizard.open_tutorial_check.toolTip().lower()
    assert wizard.open_tutorial_check.cursor().shape() == QtCore.Qt.PointingHandCursor
    assert wizard.should_open_tutorial() is True
    wizard.set_open_tutorial(False)
    assert wizard.should_open_tutorial() is False


def test_analysis_plot_dialog_accessibility_and_empty_metrics(qtbot):
    dialog = AnalysisPlotDialog(None)
    qtbot.addWidget(dialog)

    assert dialog.objectName() == "AnalysisPlotDialog"
    assert dialog.accessibleName() == "Registration Analysis Dialog"
    assert "registration error analysis" in dialog.accessibleDescription().lower()

    # Widget properties
    assert dialog.canvas is dialog._canvas
    assert dialog.summary_label is dialog._summary_label
    assert dialog.button_box is dialog._button_box
    assert dialog.close_button is dialog._close_btn

    assert dialog.canvas.accessibleName() == "Registration error plot canvas"
    assert dialog.summary_label.accessibleName() == "Registration error summary statistics"
    assert dialog.close_button is not None
    assert dialog.close_button.accessibleName() == "Close registration analysis dialog"
    assert dialog.close_button.cursor().shape() == QtCore.Qt.PointingHandCursor

    # Ergonomic query helpers
    assert dialog.metric_column_name() is None
    assert dialog.has_metrics() is False
    assert "Metric: N/A" in dialog.summary_text()

    dialog.trigger_close()
    assert dialog.result() == QtWidgets.QDialog.DialogCode.Rejected


def test_analysis_plot_dialog_with_dataframe(qtbot):
    df = pd.DataFrame({"rigid_TRE": [1.0, 2.0, 3.0]})
    dialog = AnalysisPlotDialog(df)
    qtbot.addWidget(dialog)

    assert dialog.metric_column_name() == "rigid_TRE"
    assert dialog.has_metrics() is True
    assert "Metric: rigid_TRE" in dialog.summary_text()
    assert "Mean: 2.000" in dialog.summary_text()
    assert "Max: 3.000" in dialog.summary_text()


def test_quick_tutorial_dialog_properties_and_query_helpers(qtbot):
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    dialog = QuickTutorialDialog(parent)
    qtbot.addWidget(dialog)

    # Widget property accessors
    assert dialog.header is not None
    assert dialog.icon_label is not None
    assert dialog.title_label is not None
    assert dialog.step_counter is not None
    assert dialog.body_browser is not None
    assert dialog.action_button is not None
    assert dialog.dont_show_checkbox is not None
    assert dialog.prev_button is not None
    assert dialog.next_button is not None
    assert dialog.close_button is not None
    assert len(dialog.bubbles) == 13

    # Query helpers on initial step (Step 0)
    assert dialog.icon_text() == "👋"
    assert "Step 1 of 13" in dialog.step_counter_text()
    assert dialog.step_title == "Welcome to VALIS!"
    assert dialog.is_first_step() is True
    assert dialog.is_last_step() is False
    assert dialog.can_go_next() is True
    assert dialog.can_go_prev() is False
    assert dialog.bubble_count() == 13
    assert dialog.is_bubble_active(0) is True
    assert dialog.is_bubble_active(1) is False
    assert dialog.is_action_button_visible() is False
    assert dialog.close_button_text() == "Close"

    # Navigation and step 3 (index 2: Load Data with action button)
    dialog.go_to_step(2)
    assert dialog.current_step == 2
    assert dialog.is_bubble_active(2) is True
    assert dialog.is_action_button_visible() is True
    assert "Open Slide Folder" in dialog.action_button_text()
    assert dialog.can_go_prev() is True

    # Final step
    dialog.go_to_step(12)
    assert dialog.is_last_step() is True
    assert dialog.close_button_text() == "Finish"

    # Checkbox manipulation
    initial_checked = dialog.is_dont_show_checked()
    dialog.set_dont_show_checked(not initial_checked)
    assert dialog.is_dont_show_checked() == (not initial_checked)
    dialog.set_dont_show_checked(initial_checked)
