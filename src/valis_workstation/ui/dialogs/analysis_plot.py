from __future__ import annotations

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
except ImportError:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6 import QtCore, QtWidgets

from valis_workstation.services.error_metrics import summarize_error_dataframe


class AnalysisPlotDialog(QtWidgets.QDialog):
    def __init__(self, summary_df, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("AnalysisPlotDialog")
        self.setWindowTitle("Registration Analysis")
        self.resize(720, 480)

        layout = QtWidgets.QVBoxLayout(self)
        self._canvas = FigureCanvasQTAgg(Figure(figsize=(6, 4)))
        self._canvas.setObjectName("analysis_plot_canvas")
        self._canvas.setAccessibleName("Registration error plot canvas")
        layout.addWidget(self._canvas)

        self._summary_label = QtWidgets.QLabel()
        self._summary_label.setObjectName("analysis_plot_summary_label")
        self._summary_label.setAccessibleName("Registration error summary statistics")
        layout.addWidget(self._summary_label)

        self._button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Close
        )
        self._button_box.setObjectName("analysis_plot_button_box")
        self._close_btn = self._button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Close)
        if self._close_btn is not None:
            self._close_btn.setObjectName("analysis_plot_close_button")
            self._close_btn.setAccessibleName("Close registration analysis dialog")
            self._close_btn.setToolTip("Close the analysis dialog")
            self._close_btn.setCursor(QtCore.Qt.PointingHandCursor)

        self._button_box.rejected.connect(self.reject)
        layout.addWidget(self._button_box)

        self._update_plot(summary_df)

    def _update_plot(self, summary_df) -> None:
        axes = self._canvas.figure.subplots()
        axes.clear()

        if summary_df is None:
            summary = {"metric_column": None, "values": [], "mean": 0.0, "max": 0.0}
        else:
            summary = summarize_error_dataframe(summary_df)

        metric_column = summary.get("metric_column")
        values = summary.get("values", [])

        if metric_column and values:
            axes.plot(values, marker="o")
            axes.set_title(f"{metric_column} per pair")
            axes.set_xlabel("Pair index")
            axes.set_ylabel(metric_column)
        else:
            axes.text(0.5, 0.5, "No metrics available", ha="center", va="center")

        self._canvas.figure.tight_layout()
        self._canvas.draw()

        mean_val = summary.get("mean", 0.0) or 0.0
        max_val = summary.get("max", 0.0) or 0.0
        self._summary_label.setText(
            f"Metric: {metric_column or 'N/A'} | Mean: {mean_val:.3f} | Max: {max_val:.3f}"
        )

