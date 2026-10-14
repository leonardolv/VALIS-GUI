from __future__ import annotations

import pandas as pd
from PySide6 import QtCore, QtWidgets

from valis_workstation.ui.dialogs.analysis_plot import AnalysisPlotDialog
from valis_workstation.ui.dialogs.first_run_wizard import FirstRunWizard


def test_first_run_wizard_accessibility_and_affordances(qtbot):
    wizard = FirstRunWizard()
    qtbot.addWidget(wizard)

    assert wizard.objectName() == "first_run_wizard"
    assert wizard._project_name_edit.accessibleName() == "Default project name"
    assert wizard._project_name_edit.placeholderText() != ""
    assert "default project name" in wizard._project_name_edit.toolTip().lower()

    assert wizard._output_profile_combo.accessibleName() == "Default output profile"
    assert "preset profile" in wizard._output_profile_combo.toolTip().lower()
    assert wizard._output_profile_combo.cursor().shape() == QtCore.Qt.PointingHandCursor

    assert wizard.selected_project_name() == "New Project"
    assert wizard.selected_output_profile() == "WSI Archive"

    wizard._project_name_edit.setText("Cohort_A")
    wizard._output_profile_combo.setCurrentText("Publication")
    assert wizard.selected_project_name() == "Cohort_A"
    assert wizard.selected_output_profile() == "Publication"


def test_analysis_plot_dialog_accessibility_and_empty_metrics(qtbot):
    dialog = AnalysisPlotDialog(None)
    qtbot.addWidget(dialog)

    assert dialog.objectName() == "AnalysisPlotDialog"
    assert dialog._canvas.accessibleName() == "Registration error plot canvas"
    assert dialog._summary_label.accessibleName() == "Registration error summary statistics"
    assert dialog._close_btn is not None
    assert dialog._close_btn.accessibleName() == "Close registration analysis dialog"
    assert dialog._close_btn.cursor().shape() == QtCore.Qt.PointingHandCursor
    assert "Metric: N/A" in dialog._summary_label.text()


def test_analysis_plot_dialog_with_dataframe(qtbot):
    df = pd.DataFrame({"rigid_TRE": [1.0, 2.0, 3.0]})
    dialog = AnalysisPlotDialog(df)
    qtbot.addWidget(dialog)

    assert "Metric: rigid_TRE" in dialog._summary_label.text()
    assert "Mean: 2.000" in dialog._summary_label.text()
    assert "Max: 3.000" in dialog._summary_label.text()
