from __future__ import annotations

from PySide6 import QtWidgets


class QualityReportDialog(QtWidgets.QDialog):
    def __init__(self, summary_df, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Alignment Quality Report")
        self.resize(900, 500)

        layout = QtWidgets.QVBoxLayout(self)
        self._table = QtWidgets.QTableWidget()
        self._table.setSortingEnabled(True)
        layout.addWidget(self._table)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Close
        )
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._populate(summary_df)

    def _populate(self, summary_df) -> None:
        if summary_df is None or summary_df.empty:
            self._table.setRowCount(0)
            self._table.setColumnCount(0)
            return

        self._table.setColumnCount(len(summary_df.columns))
        self._table.setHorizontalHeaderLabels([str(c) for c in summary_df.columns])
        self._table.setRowCount(len(summary_df))

        for row_idx, (_, row) in enumerate(summary_df.iterrows()):
            for col_idx, value in enumerate(row.tolist()):
                item = QtWidgets.QTableWidgetItem(str(value))
                self._table.setItem(row_idx, col_idx, item)

        self._table.resizeColumnsToContents()
