"""Animated splash / loading screen for VALIS Workstation.

Displays during application start-up while heavy subsystems (JVM, Napari,
Qt widgets) are initialised.  Also exposes a reusable *LoadingOverlay* that
can be parented to any widget to indicate long-running operations such as
slide scanning or thumbnail generation.
"""
from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

import valis_workstation as _pkg


# ── Colour palette (matches adobe_dark.qss) ─────────────────────
_BG     = QtGui.QColor("#1e1e1e")
_ACCENT = QtGui.QColor("#2d7aed")
_TRACK  = QtGui.QColor("#3a3a3a")


# ─────────────────────────────────────────────────────────────────
#  Spinner widget (reusable animated ring)
# ─────────────────────────────────────────────────────────────────
class _Spinner(QtWidgets.QWidget):
    """A small animated arc spinner."""

    def __init__(self, size: int = 48, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._size: int = size
        self._angle: int = 0
        self._timer = QtCore.QTimeLine(1000)
        self._timer.setFrameRange(0, 360)
        self._timer.setLoopCount(0)  # infinite
        self._timer.setEasingCurve(QtCore.QEasingCurve.Type.Linear)
        self._timer.frameChanged.connect(self._on_frame)
        self._timer.start()
        self.setFixedSize(size, size)

    def _on_frame(self, frame: int) -> None:
        self._angle = frame
        self.update()

    def paintEvent(self, _event: QtGui.QPaintEvent) -> None:  # noqa: N802
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        pen_w = max(3, self._size // 12)
        margin = pen_w + 1
        rect = QtCore.QRectF(margin, margin, self._size - 2 * margin, self._size - 2 * margin)

        # Track ring
        pen = QtGui.QPen(_TRACK, pen_w, QtCore.Qt.PenStyle.SolidLine)
        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawEllipse(rect)

        # Spinning arc
        pen.setColor(_ACCENT)
        p.setPen(pen)
        span = 90 * 16  # 90 degrees in 1/16th
        start = int(self._angle * 16)
        p.drawArc(rect, start, span)
        p.end()

    def stop(self) -> None:
        self._timer.stop()


# ─────────────────────────────────────────────────────────────────
#  SplashScreen – shown during application boot
# ─────────────────────────────────────────────────────────────────
class SplashScreen(QtWidgets.QWidget):
    """Frameless dark splash window with animated spinner and status text."""

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._finished: bool = False
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
            | QtCore.Qt.WindowType.SplashScreen
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(420, 320)

        # --- card background ---
        self._card = QtWidgets.QFrame(self)
        self._card.setStyleSheet(
            f"QFrame {{ background: {_BG.name()}; border-radius: 16px; }}"
        )
        self._card.setFixedSize(420, 320)

        layout = QtWidgets.QVBoxLayout(self._card)
        layout.setContentsMargins(32, 36, 32, 28)
        layout.setSpacing(12)

        # App title
        title = QtWidgets.QLabel("VALIS Workstation")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 22px; font-weight: 700; color: #e8e8e8; background: transparent;"
        )
        layout.addWidget(title)

        # Subtitle
        subtitle = QtWidgets.QLabel("Virtual Alignment of pathoLogy Image Series")
        subtitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 11px; color: #888888; background: transparent;")
        layout.addWidget(subtitle)

        layout.addSpacing(16)

        # Spinner (centred)
        spinner_row = QtWidgets.QHBoxLayout()
        spinner_row.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._spinner = _Spinner(52, self._card)
        spinner_row.addWidget(self._spinner)
        layout.addLayout(spinner_row)

        layout.addSpacing(8)

        # Status label
        self._status = QtWidgets.QLabel("Initializing…")
        self._status.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._status.setStyleSheet("font-size: 12px; color: #aaaaaa; background: transparent;")
        layout.addWidget(self._status)

        # Progress bar (thin, styled)
        self._progress = QtWidgets.QProgressBar()
        self._progress.setRange(0, 0)  # indeterminate by default
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(4)
        self._progress.setStyleSheet(
            "QProgressBar { background: #3a3a3a; border: none; border-radius: 2px; }"
            "QProgressBar::chunk { background: #2d7aed; border-radius: 2px; }"
        )
        layout.addWidget(self._progress)

        layout.addStretch()

        # Version label at bottom (read from package)
        ver = QtWidgets.QLabel(f"v{_pkg.__version__}")
        ver.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet("font-size: 10px; color: #555555; background: transparent;")
        layout.addWidget(ver)

        # Drop shadow
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 6)
        shadow.setColor(QtGui.QColor(0, 0, 0, 120))
        self._card.setGraphicsEffect(shadow)

        # Centre on screen
        self._center_on_screen()

    # ── public API ───────────────────────────────────────────────
    def set_status(self, text: str) -> None:
        self._status.setText(text)
        QtWidgets.QApplication.processEvents()

    def set_progress(self, value: int, maximum: int = 100) -> None:
        self._progress.setRange(0, maximum)
        self._progress.setValue(value)
        QtWidgets.QApplication.processEvents()

    def finish(self, main_window: QtWidgets.QWidget) -> None:
        """Fade out and close; then show the main window."""
        if self._finished:
            return
        self._finished = True
        self._spinner.stop()
        # Quick fade-out animation
        self._fade: QtCore.QPropertyAnimation = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self._fade.setDuration(350)
        self._fade.setStartValue(1.0)
        self._fade.setEndValue(0.0)
        self._fade.finished.connect(self.close)
        self._fade.finished.connect(main_window.show)
        self._fade.start()

    # ── internals ────────────────────────────────────────────────
    def _center_on_screen(self) -> None:
        screen = QtWidgets.QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + (geo.height() - self.height()) // 2
            self.move(x, y)

    def paintEvent(self, _event: QtGui.QPaintEvent) -> None:  # noqa: N802
        # Transparent background outside the card
        pass


# ─────────────────────────────────────────────────────────────────
#  LoadingOverlay – semi-transparent overlay for long tasks
# ─────────────────────────────────────────────────────────────────
class LoadingOverlay(QtWidgets.QWidget):
    """Translucent overlay with spinner + message, parented to any widget.

    Usage::

        overlay = LoadingOverlay(parent_widget, "Loading slides…")
        overlay.show()
        # ... when done:
        overlay.dismiss()
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget,
        message: str = "Please wait…",
    ):
        super().__init__(parent)
        self._dismissed: bool = False
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background: transparent;")

        # Fill entire parent
        self.setGeometry(parent.rect())

        # Central card
        card = QtWidgets.QFrame(self)
        card.setFixedSize(260, 140)
        card.setStyleSheet(
            "QFrame { background: rgba(30,30,30,230); border-radius: 12px; }"
        )

        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(12)
        card_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Spinner
        spinner_row = QtWidgets.QHBoxLayout()
        spinner_row.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._spinner = _Spinner(36, card)
        spinner_row.addWidget(self._spinner)
        card_layout.addLayout(spinner_row)

        # Message
        self._label = QtWidgets.QLabel(message)
        self._label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(
            "font-size: 12px; color: #cccccc; background: transparent;"
        )
        self._label.setWordWrap(True)
        card_layout.addWidget(self._label)

        # Centre the card inside the overlay
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(card)

        shadow = QtWidgets.QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 4)
        shadow.setColor(QtGui.QColor(0, 0, 0, 100))
        card.setGraphicsEffect(shadow)

    # ── public API ───────────────────────────────────────────────
    def set_message(self, text: str) -> None:
        self._label.setText(text)

    def dismiss(self) -> None:
        if self._dismissed:
            return
        self._dismissed = True
        self._spinner.stop()
        self._fade: QtCore.QPropertyAnimation = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self._fade.setDuration(200)
        self._fade.setStartValue(1.0)
        self._fade.setEndValue(0.0)
        self._fade.finished.connect(self._cleanup)
        self._fade.start()

    def _cleanup(self) -> None:
        self.hide()
        self.deleteLater()

    # ── event overrides ──────────────────────────────────────────
    def paintEvent(self, _event: QtGui.QPaintEvent) -> None:  # noqa: N802
        p = QtGui.QPainter(self)
        p.fillRect(self.rect(), QtGui.QColor(0, 0, 0, 100))
        p.end()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        # Keep overlay filling parent
        parent = self.parentWidget()
        if parent is not None:
            self.setGeometry(parent.rect())
