from __future__ import annotations

from PySide6 import QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from valis_workstation.services.error_metrics import summarize_error_dataframe


class AnalysisPlotDialog(QtWidgets.QDialog):
    def __init__(self, summary_df, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Registration Analysis")
        self.resize(720, 480)

        layout = QtWidgets.QVBoxLayout(self)
        self._canvas = FigureCanvasQTAgg(Figure(figsize=(6, 4)))
        layout.addWidget(self._canvas)

        self._summary_label = QtWidgets.QLabel()
        layout.addWidget(self._summary_label)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Close
        )
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._update_plot(summary_df)

    def _update_plot(self, summary_df) -> None:
        axes = self._canvas.figure.subplots()
        axes.clear()

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

        self._summary_label.setText(
            f"Metric: {metric_column or 'N/A'} | Mean: {summary['mean']:.3f} | Max: {summary['max']:.3f}"
        )
