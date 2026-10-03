from __future__ import annotations

import os
from PySide6 import QtCore, QtWidgets


class QualityReportDialog(QtWidgets.QDialog):
    def __init__(self, summary_df, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Alignment Quality Report")
        self.resize(900, 500)
        self._summary_df = summary_df

        layout = QtWidgets.QVBoxLayout(self)
        self._table = QtWidgets.QTableWidget()
        self._table.setObjectName("qualityReportTable")
        self._table.setAccessibleName("Alignment Quality Metrics Table")
        self._table.setAccessibleDescription(
            "Table displaying per-slide rigid and non-rigid alignment displacement metrics"
        )
        self._table.setSortingEnabled(True)
        self._table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self._table)

        button_row = QtWidgets.QHBoxLayout()
        self._copy_table_btn = QtWidgets.QPushButton("Copy Table")
        self._copy_table_btn.setObjectName("qualityReportCopyTableBtn")
        self._copy_table_btn.setAccessibleName("Copy Quality Report Table to Clipboard")
        self._copy_table_btn.setToolTip("Copy entire quality report table as tab-delimited text to clipboard")
        self._copy_table_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._copy_table_btn.clicked.connect(self._copy_table)
        button_row.addWidget(self._copy_table_btn)

        self._export_csv_btn = QtWidgets.QPushButton("Export CSV...")
        self._export_csv_btn.setObjectName("qualityReportExportCsvBtn")
        self._export_csv_btn.setAccessibleName("Export Quality Report to CSV")
        self._export_csv_btn.setToolTip("Export the alignment quality metrics table to a CSV file")
        self._export_csv_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._export_csv_btn.clicked.connect(self._export_csv)
        button_row.addWidget(self._export_csv_btn)
        button_row.addStretch()

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Close
        )
        button_box.rejected.connect(self.reject)
        self._close_btn = button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Close)
        if self._close_btn is not None:
            self._close_btn.setObjectName("qualityReportCloseBtn")
            self._close_btn.setAccessibleName("Close Quality Report Dialog")
            self._close_btn.setToolTip("Close the alignment quality report dialog")
            self._close_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        button_row.addWidget(button_box)
        layout.addLayout(button_row)

        self._populate(summary_df)

    def _populate(self, summary_df) -> None:
        if summary_df is None or summary_df.empty:
            self._table.setRowCount(0)
            self._table.setColumnCount(0)
            return

        self._table.setColumnCount(len(summary_df.columns))
        self._table.setHorizontalHeaderLabels([str(c) for c in summary_df.columns])
        self._table.setRowCount(len(summary_df))

        # Column header tooltips (E9)
        column_tooltips = {
            "mean_d_tform": "Mean displacement after rigid transform (μm)",
            "mean_d_non_rigid": "Mean displacement after non-rigid warping (μm)",
            "std_d_tform": "Standard deviation of rigid displacement",
            "std_d_non_rigid": "Standard deviation of non-rigid displacement",
        }

        for col_idx, col_name in enumerate(summary_df.columns):
            header_item = self._table.horizontalHeaderItem(col_idx)
            if header_item is not None and col_name in column_tooltips:
                header_item.setToolTip(column_tooltips[col_name])

        for row_idx, (_, row) in enumerate(summary_df.iterrows()):
            for col_idx, value in enumerate(row.tolist()):
                item = QtWidgets.QTableWidgetItem(str(value))
                self._table.setItem(row_idx, col_idx, item)

        self._table.resizeColumnsToContents()

    def _show_context_menu(self, pos: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(self._table)
        copy_row = menu.addAction("Copy Row")
        copy_table = menu.addAction("Copy Table")

        action = menu.exec(self._table.mapToGlobal(pos))
        if action == copy_row:
            self._copy_row()
        elif action == copy_table:
            self._copy_table()

    def _copy_row(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            return
        cells = []
        for col in range(self._table.columnCount()):
            item = self._table.item(row, col)
            cells.append(item.text() if item else "")
        text = "\t".join(cells)
        QtWidgets.QApplication.clipboard().setText(text)

    def _copy_table(self) -> None:
        rows = []
        # Header
        header = []
        for col in range(self._table.columnCount()):
            header_item = self._table.horizontalHeaderItem(col)
            header.append(header_item.text() if header_item else "")
        rows.append("\t".join(header))
        # Rows
        for row in range(self._table.rowCount()):
            cells = []
            for col in range(self._table.columnCount()):
                item = self._table.item(row, col)
                cells.append(item.text() if item else "")
            rows.append("\t".join(cells))
        text = "\n".join(rows)
        QtWidgets.QApplication.clipboard().setText(text)

        # Inline visual feedback
        self._copy_table_btn.setText("✓ Copied!")
        QtCore.QTimer.singleShot(1500, self, self._restore_copy_btn_text)

    def _restore_copy_btn_text(self) -> None:
        try:
            self._copy_table_btn.setText("Copy Table")
        except RuntimeError:
            pass

    def _export_csv(self) -> None:
        out_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Quality Report",
            "quality_report.csv",
            "CSV Files (*.csv)",
        )
        if not out_path:
            return
        try:
            if self._summary_df is not None:
                self._summary_df.to_csv(out_path, index=False)
                if not (os.environ.get("QT_QPA_PLATFORM") == "offscreen" or "PYTEST_CURRENT_TEST" in os.environ):
                    QtWidgets.QMessageBox.information(
                        self, "Export", f"Report exported to {out_path}"
                    )
        except Exception as exc:
            if not (os.environ.get("QT_QPA_PLATFORM") == "offscreen" or "PYTEST_CURRENT_TEST" in os.environ):
                QtWidgets.QMessageBox.critical(
                    self, "Export Error", f"Failed to export: {exc}"
                )
