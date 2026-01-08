from __future__ import annotations

from PySide6 import QtWidgets


class WarpAnnotationsDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Warp Annotations")
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel(
            "Warp annotations from the reference slide to all registered slides."
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
