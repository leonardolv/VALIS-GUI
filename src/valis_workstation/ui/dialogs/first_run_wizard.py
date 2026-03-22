from __future__ import annotations

from PySide6 import QtWidgets


class FirstRunWizard(QtWidgets.QWizard):
    """Simple first-run setup wizard."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("VALIS Workstation Setup")
        self.resize(640, 420)

        self.setWizardStyle(QtWidgets.QWizard.WizardStyle.ModernStyle)

        self._project_name_edit = QtWidgets.QLineEdit("New Project")
        self._output_profile_combo = QtWidgets.QComboBox()
        self._output_profile_combo.addItems(
            ["WSI Archive", "Fast Review", "Publication"]
        )

        self.addPage(self._build_welcome_page())
        self.addPage(self._build_options_page())
        self.addPage(self._build_finish_page())

    def _build_welcome_page(self) -> QtWidgets.QWizardPage:
        page = QtWidgets.QWizardPage()
        page.setTitle("Welcome")
        layout = QtWidgets.QVBoxLayout(page)
        layout.addWidget(
            QtWidgets.QLabel(
                "Welcome to VALIS Workstation.\n"
                "This wizard configures a few sensible defaults to get started quickly."
            )
        )
        return page

    def _build_options_page(self) -> QtWidgets.QWizardPage:
        page = QtWidgets.QWizardPage()
        page.setTitle("Default Settings")
        form = QtWidgets.QFormLayout(page)
        form.addRow("Default project name", self._project_name_edit)
        form.addRow("Default output profile", self._output_profile_combo)
        return page

    def _build_finish_page(self) -> QtWidgets.QWizardPage:
        page = QtWidgets.QWizardPage()
        page.setTitle("Done")
        layout = QtWidgets.QVBoxLayout(page)
        layout.addWidget(
            QtWidgets.QLabel(
                "Setup is complete. You can change these settings any time\n"
                "in Properties, Preferences, or Presets."
            )
        )
        return page

    def selected_project_name(self) -> str:
        return self._project_name_edit.text().strip() or "New Project"

    def selected_output_profile(self) -> str:
        return self._output_profile_combo.currentText()
