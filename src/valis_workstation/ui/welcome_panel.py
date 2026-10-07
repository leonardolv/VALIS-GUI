from __future__ import annotations

from PySide6 import QtCore, QtWidgets

WELCOME_STEPS: list[tuple[str, str]] = [
    ("Load", "Open a folder that contains the slide images you want to align (at least 2). "
             "You can also drag a folder into this window."),
    ("Configure", "Check the settings on the right. The defaults suit most slide sets, "
                  "so you can usually leave them as they are."),
    ("Register", "Press Run Registration (Ctrl+R). VALIS aligns the slides; "
                 "progress is shown at the bottom."),
    ("Review", "Inspect the result with Blink, the Quality Report and other Tools, "
               "then export or merge the aligned slides."),
]


class WelcomePanel(QtWidgets.QWidget):
    """Getting-started page shown in the centre until slides are loaded.

    ``viewer_note`` is an optional, deliberately low-key footnote (for example
    that the napari viewer is not installed) so that a missing optional
    component never reads as the main message of the first screen.
    """

    open_folder_requested = QtCore.Signal()

    def __init__(self, viewer_note: str = "", parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("WelcomePanel")
        outer = QtWidgets.QVBoxLayout(self)
        outer.addStretch(1)

        card = QtWidgets.QWidget()
        card.setMaximumWidth(560)
        layout = QtWidgets.QVBoxLayout(card)
        layout.setSpacing(10)

        title = QtWidgets.QLabel("<h2>Welcome to VALIS Workstation</h2>")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        intro = QtWidgets.QLabel(
            "Line up a series of tissue slides (for example serial sections or "
            "different stains of the same sample) so they overlay precisely."
        )
        intro.setWordWrap(True)
        intro.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(intro)

        self._status_label = QtWidgets.QLabel("")
        self._status_label.setObjectName("WelcomeStatus")
        self._status_label.setWordWrap(True)
        self._status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._status_label.setVisible(False)
        layout.addWidget(self._status_label)

        self._open_button = QtWidgets.QPushButton("Open Slide Folder…  (Ctrl+O)")
        self._open_button.setObjectName("WelcomeOpenButton")
        self._open_button.setProperty("primary", True)
        self._open_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._open_button.setToolTip("Choose a folder containing your slide images")
        self._open_button.setAccessibleName("Open slide folder")
        self._open_button.clicked.connect(self.open_folder_requested.emit)
        layout.addWidget(self._open_button)

        steps = "".join(
            f"<p><b>{i}. {name}</b> &mdash; {text}</p>"
            for i, (name, text) in enumerate(WELCOME_STEPS, start=1)
        )
        self._intro = intro
        self._steps_label = QtWidgets.QLabel(steps)
        self._steps_label.setWordWrap(True)
        layout.addWidget(self._steps_label)

        if viewer_note:
            note = QtWidgets.QLabel(viewer_note)
            note.setWordWrap(True)
            note.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            note.setStyleSheet("color: #888;")
            note.setObjectName("WelcomeViewerNote")
            layout.addWidget(note)

        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        row.addWidget(card)
        row.addStretch(1)
        outer.addLayout(row)
        outer.addStretch(1)

    def set_slide_count(self, count: int) -> None:
        """Reflect how many slides are loaded so the page never goes stale."""
        if count <= 0:
            self._status_label.setVisible(False)
            self._intro.setVisible(True)
            self._open_button.setText("Open Slide Folder…  (Ctrl+O)")
            return
        if count == 1:
            text = (
                "<b>1 slide loaded.</b> Registration aligns slides to each other, "
                "so add at least one more: open a folder with 2 or more slides."
            )
        else:
            text = (
                f"<b>{count} slides loaded.</b> Next: check the settings on the right, "
                "then press Run Registration (Ctrl+R)."
            )
        self._status_label.setText(text)
        self._status_label.setVisible(True)
        self._intro.setVisible(False)
        self._open_button.setText("Open a Different Folder…")
