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
                "<b>Welcome to VALIS Workstation.</b><br><br>"
                "This app lines up a series of tissue slides (serial sections or "
                "different stains) so they overlay precisely. Working with it "
                "takes four steps:<br><br>"
                "<b>1. Load</b> a folder of slides (at least 2)<br>"
                "<b>2. Configure</b> settings (the defaults suit most sets)<br>"
                "<b>3. Register</b> by pressing Run Registration<br>"
                "<b>4. Review</b> the result with Blink and the Quality Report<br><br>"
                "The next page picks two defaults. You can change both later."
            )
        )
        layout.itemAt(0).widget().setWordWrap(True)
        return page

    def _build_options_page(self) -> QtWidgets.QWizardPage:
        page = QtWidgets.QWizardPage()
        page.setTitle("Default Settings")
        form = QtWidgets.QFormLayout(page)
        form.addRow("Default project name", self._project_name_edit)
        form.addRow("Default output profile", self._output_profile_combo)
        hint = QtWidgets.QLabel(
            "<b>Project name</b>: results are saved in a folder with this name.<br>"
            "<b>WSI Archive</b>: full-quality files for long-term storage (largest).<br>"
            "<b>Fast Review</b>: smaller files, quick to open and check.<br>"
            "<b>Publication</b>: high-quality images for figures and papers.<br><br>"
            "Not sure? Keep the defaults."
        )
        hint.setWordWrap(True)
        form.addRow(hint)
        return page

    def _build_finish_page(self) -> QtWidgets.QWizardPage:
        page = QtWidgets.QWizardPage()
        page.setTitle("Done")
        layout = QtWidgets.QVBoxLayout(page)
        layout.addWidget(
            QtWidgets.QLabel(
                "Setup is complete. Next: choose File > Open Slide Folder (Ctrl+O)\n"
                "to load your slides. You can change these settings any time\n"
                "in Properties, Preferences, or Presets."
            )
        )
        return page

    def selected_project_name(self) -> str:
        return self._project_name_edit.text().strip() or "New Project"

    def selected_output_profile(self) -> str:
        return self._output_profile_combo.currentText()
