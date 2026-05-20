"""Dialog for merging multiple slides into a single multi-channel image."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

if TYPE_CHECKING:
    pass


class MergeSlidesDialog(QtWidgets.QDialog):
    """Dialog for configuring slide merge options.

    Allows users to merge multiple registered slides into a single multi-channel
    image, commonly used for multiplexed imaging workflows (CyCIF, CODEX, etc.).
    """

    def __init__(
        self, slide_names: list[str], parent: QtWidgets.QWidget | None = None
    ) -> None:
        """Initialize the merge slides dialog.

        Parameters
        ----------
        slide_names : list[str]
            List of available slide names to merge
        parent : QtWidgets.QWidget | None
            Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Merge Slides")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        self._slide_names = slide_names

        layout = QtWidgets.QVBoxLayout(self)

        # Info banner
        info = QtWidgets.QLabel(
            "Merge registered slides into a single multi-channel image.\n"
            "Each slide becomes a channel. Useful for CyCIF, CODEX, and other multiplexed imaging."
        )
        info.setWordWrap(True)
        info.setStyleSheet("background: #e8f4f8; padding: 8px; border-radius: 4px;")
        layout.addWidget(info)

        # Channel mapping table
        group = QtWidgets.QGroupBox("Channel Mapping")
        group_layout = QtWidgets.QVBoxLayout(group)

        self._table = QtWidgets.QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(
            ["Include", "Slide Name", "Channel Name", "Color"]
        )
        self._table.setRowCount(len(slide_names))

        # Populate table
        for i, name in enumerate(slide_names):
            # Include checkbox
            include_cb = QtWidgets.QCheckBox()
            include_cb.setChecked(True)
            self._table.setCellWidget(i, 0, include_cb)

            # Slide name (read-only)
            slide_item = QtWidgets.QTableWidgetItem(name)
            slide_item.setFlags(slide_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self._table.setItem(i, 1, slide_item)

            # Channel name (editable)
            channel_item = QtWidgets.QTableWidgetItem(f"Channel_{i + 1}")
            self._table.setItem(i, 2, channel_item)

            # Color selection
            color_combo = QtWidgets.QComboBox()
            color_combo.addItems(
                [
                    "Auto",
                    "Red",
                    "Green",
                    "Blue",
                    "Cyan",
                    "Magenta",
                    "Yellow",
                    "Gray",
                    "White",
                ]
            )
            self._table.setCellWidget(i, 3, color_combo)

        self._table.resizeColumnsToContents()
        group_layout.addWidget(self._table)
        layout.addWidget(group)

        # Options
        options_group = QtWidgets.QGroupBox("Merge Options")
        options_layout = QtWidgets.QFormLayout(options_group)

        # Duplicate handling
        self._duplicate_handling = QtWidgets.QComboBox()
        self._duplicate_handling.addItems(
            ["Average", "Maximum", "Minimum", "First", "Last"]
        )
        self._duplicate_handling.setCurrentText("Average")
        self._duplicate_handling.setToolTip(
            "How to handle overlapping pixels:\n"
            "• Average: Average overlapping values\n"
            "• Maximum: Take brightest value\n"
            "• Minimum: Take darkest value\n"
            "• First: Use first slide's value\n"
            "• Last: Use last slide's value"
        )
        options_layout.addRow("Overlap handling:", self._duplicate_handling)

        # Output name
        self._output_name = QtWidgets.QLineEdit("merged_image")
        self._output_name.setToolTip("Name for the merged output image")
        options_layout.addRow("Output name:", self._output_name)

        # Normalize intensities
        self._normalize = QtWidgets.QCheckBox()
        self._normalize.setChecked(True)
        self._normalize.setToolTip(
            "Normalize intensity ranges across channels.\n"
            "Recommended for better visualization."
        )
        options_layout.addRow("Normalize intensities:", self._normalize)

        layout.addWidget(options_group)

        # Dialog buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        # Add utility buttons
        select_all = QtWidgets.QPushButton("Select All")
        select_all.clicked.connect(self._select_all)
        buttons.addButton(select_all, QtWidgets.QDialogButtonBox.ActionRole)

        select_none = QtWidgets.QPushButton("Select None")
        select_none.clicked.connect(self._select_none)
        buttons.addButton(select_none, QtWidgets.QDialogButtonBox.ActionRole)

        export_config = QtWidgets.QPushButton("Export config...")
        export_config.clicked.connect(self._export_config)
        buttons.addButton(export_config, QtWidgets.QDialogButtonBox.ActionRole)

        layout.addWidget(buttons)

    def _select_all(self) -> None:
        """Select all slides for merging."""
        for i in range(self._table.rowCount()):
            cb = self._table.cellWidget(i, 0)
            if isinstance(cb, QtWidgets.QCheckBox):
                cb.setChecked(True)

    def _select_none(self) -> None:
        """Deselect all slides."""
        for i in range(self._table.rowCount()):
            cb = self._table.cellWidget(i, 0)
            if isinstance(cb, QtWidgets.QCheckBox):
                cb.setChecked(False)

    def _export_config(self) -> None:
        """Export channel config as JSON file."""
        config = self.get_merge_config()
        out_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Merge Config",
            "merge_config.json",
            "JSON Files (*.json)",
        )
        if not out_path:
            return
        try:
            with open(out_path, "w") as f:
                json.dump(config, f, indent=2)
            QtWidgets.QMessageBox.information(
                self, "Exported", f"Config exported to {out_path}"
            )
        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                self, "Export Error", f"Failed to export config: {exc}"
            )

    def get_merge_config(self) -> dict:
        """Get the merge configuration.

        Returns
        -------
        dict
            Configuration with channel mappings and merge options
        """
        channels = []
        for i in range(self._table.rowCount()):
            include_cb = self._table.cellWidget(i, 0)
            if (
                not isinstance(include_cb, QtWidgets.QCheckBox)
                or not include_cb.isChecked()
            ):
                continue

            slide_name = self._table.item(i, 1).text()
            channel_name = self._table.item(i, 2).text()
            color_combo = self._table.cellWidget(i, 3)
            color = (
                color_combo.currentText()
                if isinstance(color_combo, QtWidgets.QComboBox)
                else "Auto"
            )

            channels.append(
                {
                    "slide_name": slide_name,
                    "channel_name": channel_name,
                    "color": color,
                }
            )

        return {
            "channels": channels,
            "duplicate_handling": self._duplicate_handling.currentText().lower(),
            "output_name": self._output_name.text(),
            "normalize": self._normalize.isChecked(),
        }
