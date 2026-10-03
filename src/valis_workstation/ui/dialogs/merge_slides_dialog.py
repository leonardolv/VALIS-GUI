"""Dialog for merging multiple slides into a single multi-channel image."""

from __future__ import annotations

import json
import os
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
        self._table.setObjectName("channel_mapping_table")
        self._table.setAccessibleName("Channel Mapping Table")
        self._table.setAccessibleDescription(
            "Table configuring slide inclusion, channel naming, and color assignment for merge"
        )
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(
            ["Include", "Slide Name", "Channel Name", "Color"]
        )
        self._table.setRowCount(len(slide_names))

        # Populate table
        for i, name in enumerate(slide_names):
            # Include checkbox
            include_cb = QtWidgets.QCheckBox()
            include_cb.setObjectName(f"include_checkbox_{i}")
            include_cb.setAccessibleName(f"Include {name} in merged image")
            include_cb.setToolTip(f"Include {name} as a channel in merged image")
            include_cb.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
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
            color_combo.setObjectName(f"color_combo_{i}")
            color_combo.setAccessibleName(f"Channel color for {name}")
            color_combo.setToolTip(f"Select pseudo-color for {name} channel")
            color_combo.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
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
        self._duplicate_handling.setObjectName("duplicate_handling_combo")
        self._duplicate_handling.setAccessibleName("Overlap handling method")
        self._duplicate_handling.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
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
        self._output_name.setObjectName("output_name_edit")
        self._output_name.setAccessibleName("Merged output image name")
        self._output_name.setToolTip("Name for the merged output image")
        options_layout.addRow("Output name:", self._output_name)

        # Normalize intensities
        self._normalize = QtWidgets.QCheckBox()
        self._normalize.setObjectName("normalize_checkbox")
        self._normalize.setAccessibleName("Normalize intensities across channels")
        self._normalize.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._normalize.setChecked(True)
        self._normalize.setToolTip(
            "Normalize intensity ranges across channels.\n"
            "Recommended for better visualization."
        )
        options_layout.addRow("Normalize intensities:", self._normalize)

        layout.addWidget(options_group)

        # Dialog buttons
        self._button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

        # Add utility buttons
        self._select_all_btn = QtWidgets.QPushButton("Select All")
        self._select_all_btn.setObjectName("select_all_btn")
        self._select_all_btn.setAccessibleName("Select all slides")
        self._select_all_btn.setToolTip("Select all slides to be included in merge")
        self._select_all_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._select_all_btn.clicked.connect(self._select_all)
        self._button_box.addButton(self._select_all_btn, QtWidgets.QDialogButtonBox.ActionRole)

        self._select_none_btn = QtWidgets.QPushButton("Select None")
        self._select_none_btn.setObjectName("select_none_btn")
        self._select_none_btn.setAccessibleName("Deselect all slides")
        self._select_none_btn.setToolTip("Deselect all slides")
        self._select_none_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._select_none_btn.clicked.connect(self._select_none)
        self._button_box.addButton(self._select_none_btn, QtWidgets.QDialogButtonBox.ActionRole)

        self._export_config_btn = QtWidgets.QPushButton("Export config...")
        self._export_config_btn.setObjectName("export_config_btn")
        self._export_config_btn.setAccessibleName("Export channel configuration to JSON")
        self._export_config_btn.setToolTip("Export current channel configuration as a JSON file")
        self._export_config_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._export_config_btn.clicked.connect(self._export_config)
        self._button_box.addButton(self._export_config_btn, QtWidgets.QDialogButtonBox.ActionRole)

        self._ok_btn = self._button_box.button(QtWidgets.QDialogButtonBox.Ok)
        if self._ok_btn is not None:
            self._ok_btn.setObjectName("ok_btn")
            self._ok_btn.setAccessibleName("Merge slides and accept configuration")
            self._ok_btn.setToolTip("Confirm and proceed with slide merge")
            self._ok_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

        self._cancel_btn = self._button_box.button(QtWidgets.QDialogButtonBox.Cancel)
        if self._cancel_btn is not None:
            self._cancel_btn.setObjectName("cancel_btn")
            self._cancel_btn.setAccessibleName("Cancel slide merge")
            self._cancel_btn.setToolTip("Cancel slide merge and close dialog")
            self._cancel_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

        layout.addWidget(self._button_box)

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
            if not (os.environ.get("QT_QPA_PLATFORM") == "offscreen" or os.environ.get("PYTEST_CURRENT_TEST")):
                QtWidgets.QMessageBox.information(
                    self, "Exported", f"Config exported to {out_path}"
                )
        except Exception as exc:
            if not (os.environ.get("QT_QPA_PLATFORM") == "offscreen" or os.environ.get("PYTEST_CURRENT_TEST")):
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
