from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class QualityReportDialog(QtWidgets.QDialog):
    def __init__(self, summary_df, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Alignment Quality Report")
        self.resize(900, 500)
        self._summary_df = summary_df

        layout = QtWidgets.QVBoxLayout(self)
        self._table = QtWidgets.QTableWidget()
        self._table.setSortingEnabled(True)
        self._table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self._table)

        button_row = QtWidgets.QHBoxLayout()
        self._export_csv_btn = QtWidgets.QPushButton("Export CSV...")
        self._export_csv_btn.clicked.connect(self._export_csv)
        button_row.addWidget(self._export_csv_btn)
        button_row.addStretch()

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Close
        )
        button_box.rejected.connect(self.reject)
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
            if col_name in column_tooltips:
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
            header.append(self._table.horizontalHeaderItem(col).text())
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
                QtWidgets.QMessageBox.information(
                    self, "Export", f"Report exported to {out_path}"
                )
        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                self, "Export Error", f"Failed to export: {exc}"
            )
