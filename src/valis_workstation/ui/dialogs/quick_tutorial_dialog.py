"""In-app Quick Tutorial dialog.

A 13-step non-modal wizard designed for beginners that walks through the
VALIS Workstation workflow with embedded action buttons and auto-advancing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from PySide6 import QtCore, QtGui, QtWidgets

if TYPE_CHECKING:
    from valis_workstation.main_window import MainWindow

logger = logging.getLogger(__name__)

_SETTINGS_KEY_SKIP_TUTORIAL = "skip_quick_tutorial"


# ── Step data ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _TutorialStep:
    icon: str
    title: str
    body: str  # Rich-text HTML
    action_id: str | None = None
    action_label: str | None = None


_STEPS: list[_TutorialStep] = [
    # 1 — Welcome
    _TutorialStep(
        icon="👋",
        title="Welcome to VALIS!",
        body=(
            "<p>Welcome to <b>VALIS Workstation</b>.</p>"
            "<p>We are going to learn how to align tissue slides in 13 easy steps.</p>"
            "<p>You can keep this window open and use the app at the same time.</p>"
        ),
    ),
    # 2 — The Basics
    _TutorialStep(
        icon="🔬",
        title="What is Registration?",
        body=(
            "<p>A <b>slide</b> is a piece of tissue on a glass slide.</p>"
            "<p><b>Registration</b> is the process of aligning these slides so they match up perfectly, like stacking pancakes.</p>"
            "<p>This lets you compare different stains on the exact same cells.</p>"
        ),
    ),
    # 3 — Load Data
    _TutorialStep(
        icon="📂",
        title="Load Your Slides",
        body=(
            "<p>First, we need to load images.</p>"
            "<p>Put all your slide images for a single case into one folder.</p>"
            "<p>Click the button below to open a folder. (Or you can drag and drop a folder into the main window).</p>"
        ),
        action_id="load_slides",
        action_label="📂 Open Slide Folder",
    ),
    # 4 — What is Rigid?
    _TutorialStep(
        icon="📐",
        title="Rigid vs. Non-Rigid",
        body=(
            "<p>Before we run, let's understand two settings:</p>"
            "<ul>"
            "<li><b>Rigid:</b> We just move and rotate the image without changing its shape.</li>"
            "<li><b>Non-Rigid:</b> We squish and stretch the image to fix torn or folded tissue.</li>"
            "</ul>"
            "<p>Usually, we want <b>both</b> turned on.</p>"
        ),
    ),
    # 5 — Configure Settings
    _TutorialStep(
        icon="⚙️",
        title="Configure Settings",
        body=(
            "<p>Look at the <b>Properties</b> panel on the right.</p>"
            "<p>For beginners, the default settings are perfect.</p>"
            "<ul>"
            "<li>Give your project a name.</li>"
            "<li>Make sure <b>Rigid</b> and <b>Non-rigid</b> are checked.</li>"
            "</ul>"
            "<p>You can ignore the Advanced settings for now.</p>"
        ),
    ),
    # 6 — Run
    _TutorialStep(
        icon="▶️",
        title="Run Registration",
        body=(
            "<p>We are ready to align the slides!</p>"
            "<p>Click the button below to start. A confirmation window will appear.</p>"
        ),
        action_id="run_registration",
        action_label="▶️ Run Registration",
    ),
    # 7 — Wait
    _TutorialStep(
        icon="⏳",
        title="Wait & Watch",
        body=(
            "<p>Registration takes some time depending on the size of the images.</p>"
            "<p>Look at the <b>Status</b> panel at the bottom of the screen. It shows the progress bar and logs.</p>"
            "<p>If you made a mistake, you can click Cancel.</p>"
        ),
    ),
    # 8 — View Results
    _TutorialStep(
        icon="👀",
        title="View Results",
        body=(
            "<p>When finished, the aligned images will load in the center screen.</p>"
            "<p>Look at the <b>Layers</b> panel on the right. You can click the eye icon 👁️ to hide or show different slides.</p>"
            "<p>You can zoom in with your mouse wheel and drag to pan.</p>"
        ),
    ),
    # 9 — Find Errors
    _TutorialStep(
        icon="🔍",
        title="Check the Quality",
        body=(
            "<p>How do we know if it worked well?</p>"
            "<p>Go to the <b>Tools</b> menu at the top:</p>"
            "<ul>"
            "<li><b>Blink:</b> Rapidly switches between two slides so you can see if they move.</li>"
            "<li><b>Quality Report:</b> A table showing numerical errors to find bad pairs.</li>"
            "</ul>"
        ),
    ),
    # 10 — Troubleshooting
    _TutorialStep(
        icon="🔧",
        title="What if it fails?",
        body=(
            "<p>Sometimes slides don't align perfectly.</p>"
            "<ul>"
            "<li>Try changing the <b>Feature detector</b> in the Advanced settings (e.g., from VGG to BRISK).</li>"
            "<li>If it's too slow, reduce the <b>Max image size</b> to 1024.</li>"
            "<li>If a slide is upside down, VALIS usually fixes it automatically!</li>"
            "</ul>"
        ),
    ),
    # 11 — Post-Processing
    _TutorialStep(
        icon="✂️",
        title="Post-Processing",
        body=(
            "<p>Now that they are aligned, you can do more from the <b>Tools</b> menu:</p>"
            "<ul>"
            "<li><b>Export ROI Crop:</b> Cut out a small matching square from all slides.</li>"
            "<li><b>Merge Slides:</b> Combine them into one multi-colored image (like for multiplexing).</li>"
            "</ul>"
        ),
    ),
    # 12 — Output Files
    _TutorialStep(
        icon="💾",
        title="Where are my files?",
        body=(
            "<p>VALIS already saved your aligned slides!</p>"
            "<p>Check the <code>output/YourProjectName</code> folder on your computer.</p>"
            "<ul>"
            "<li><b>OME-TIFF files:</b> These are the huge, aligned image files.</li>"
            "<li><b>summary.csv:</b> A spreadsheet of the error metrics.</li>"
            "</ul>"
        ),
    ),
    # 13 — Done
    _TutorialStep(
        icon="🎉",
        title="You're Ready!",
        body=(
            "<p>You've completed the tutorial!</p>"
            "<p>If you need more details, check out the full <b>Manual</b> in the Help menu.</p>"
            "<p style='color:#7dd3fc; margin-top:12px;'>Happy registering! 🔬</p>"
        ),
    ),
]


# ── Dialog ───────────────────────────────────────────────────────────


class QuickTutorialDialog(QtWidgets.QDialog):
    """Multi-step in-app tutorial wizard (Non-Modal)."""

    def __init__(self, parent: MainWindow) -> None:
        super().__init__(parent)
        self.setWindowTitle("Quick Tutorial — VALIS Workstation")
        self.setMinimumSize(660, 560)
        self.resize(720, 600)
        # Non-modal so users can interact with the app
        self.setModal(False)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, False)

        self._parent_window = parent
        self._current_step = 0

        # ── Main layout ──────────────────────────────────────────────
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header bar
        self._header = QtWidgets.QFrame()
        self._header.setObjectName("TutorialHeader")
        self._header.setStyleSheet(
            "#TutorialHeader {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
            "    stop:0 #0c4a6e, stop:0.5 #0e7490, stop:1 #0891b2);"
            "  padding: 18px 24px;"
            "}"
        )
        header_layout = QtWidgets.QHBoxLayout(self._header)
        header_layout.setContentsMargins(24, 18, 24, 18)

        self._icon_label = QtWidgets.QLabel()
        self._icon_label.setStyleSheet("font-size: 42px;")
        header_layout.addWidget(self._icon_label)

        header_text_layout = QtWidgets.QVBoxLayout()
        header_text_layout.setSpacing(4)

        self._title_label = QtWidgets.QLabel()
        self._title_label.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #f0f9ff;"
        )
        header_text_layout.addWidget(self._title_label)

        self._step_counter = QtWidgets.QLabel()
        self._step_counter.setStyleSheet("font-size: 13px; color: #bae6fd;")
        header_text_layout.addWidget(self._step_counter)

        header_layout.addLayout(header_text_layout, 1)
        outer.addWidget(self._header)

        # Body (scrollable)
        body_container = QtWidgets.QFrame()
        body_container.setStyleSheet("background: #0f172a;")
        body_layout = QtWidgets.QVBoxLayout(body_container)
        body_layout.setContentsMargins(32, 24, 32, 24)
        body_layout.setSpacing(16)

        self._body = QtWidgets.QTextBrowser()
        self._body.setOpenExternalLinks(True)
        self._body.setStyleSheet(
            "QTextBrowser {"
            "  background: transparent;"
            "  color: #e2e8f0;"
            "  border: none;"
            "  font-size: 15px;"
            "  line-height: 1.8;"
            "  selection-background-color: #0284c7;"
            "}"
            "QTextBrowser a { color: #38bdf8; }"
        )
        body_layout.addWidget(self._body, 1)

        # Embedded Action Button
        self._action_btn = QtWidgets.QPushButton()
        self._action_btn.setVisible(False)
        self._action_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._action_btn.setStyleSheet(
            "QPushButton {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
            "    stop:0 #059669, stop:1 #10b981);"
            "  color: #ffffff; border: none; border-radius: 8px;"
            "  padding: 12px 24px; font-size: 16px; font-weight: bold;"
            "  margin-top: 10px;"
            "}"
            "QPushButton:hover {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
            "    stop:0 #047857, stop:1 #059669);"
            "}"
        )
        self._action_btn.clicked.connect(self._on_action_clicked)
        body_layout.addWidget(self._action_btn, 0, QtCore.Qt.AlignmentFlag.AlignHCenter)
        
        outer.addWidget(body_container, 1)

        # ── Bubbles Progress Indicator ──────────────────────────────
        self._bubbles_container = QtWidgets.QFrame()
        self._bubbles_container.setStyleSheet("background: #0f172a;")
        bubbles_layout = QtWidgets.QHBoxLayout(self._bubbles_container)
        bubbles_layout.setContentsMargins(16, 0, 16, 16)
        bubbles_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        bubbles_layout.setSpacing(8)
        
        self._bubbles: list[QtWidgets.QLabel] = []
        for i in range(len(_STEPS)):
            lbl = QtWidgets.QLabel()
            lbl.setFixedSize(10, 10)
            self._set_bubble_state(lbl, False)
            bubbles_layout.addWidget(lbl)
            self._bubbles.append(lbl)
            
        outer.addWidget(self._bubbles_container)

        # ── Footer ──────────────────────────────────────────────────
        footer = QtWidgets.QFrame()
        footer.setStyleSheet(
            "background: #1e293b; border-top: 1px solid #334155;"
        )
        footer_layout = QtWidgets.QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 14, 20, 14)

        self._dont_show = QtWidgets.QCheckBox("Don't show on startup")
        self._dont_show.setStyleSheet(
            "QCheckBox { color: #64748b; font-size: 12px; }"
            "QCheckBox::indicator { width: 16px; height: 16px; }"
        )
        settings = QtCore.QSettings("VALIS", "Workstation")
        self._dont_show.setChecked(
            settings.value(_SETTINGS_KEY_SKIP_TUTORIAL, False, type=bool)
        )
        self._dont_show.toggled.connect(self._on_dont_show_toggled)
        footer_layout.addWidget(self._dont_show)

        footer_layout.addStretch(1)

        btn_style = (
            "QPushButton {"
            "  padding: 8px 24px;"
            "  border-radius: 6px;"
            "  font-weight: 600;"
            "  font-size: 13px;"
            "}"
        )

        self._prev_btn = QtWidgets.QPushButton("← Previous")
        self._prev_btn.setStyleSheet(
            btn_style
            + "QPushButton {"
            "  background: #334155; color: #e2e8f0; border: 1px solid #475569;"
            "}"
            "QPushButton:hover { background: #475569; }"
            "QPushButton:disabled { color: #475569; background: #1e293b; "
            "border-color: #334155; }"
        )
        self._prev_btn.clicked.connect(self._go_prev)
        footer_layout.addWidget(self._prev_btn)

        self._next_btn = QtWidgets.QPushButton("Next →")
        self._next_btn.setStyleSheet(
            btn_style
            + "QPushButton {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
            "    stop:0 #0284c7, stop:1 #0ea5e9);"
            "  color: #ffffff; border: none;"
            "}"
            "QPushButton:hover {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
            "    stop:0 #0369a1, stop:1 #0284c7);"
            "}"
        )
        self._next_btn.clicked.connect(self._go_next)
        footer_layout.addWidget(self._next_btn)

        self._close_btn = QtWidgets.QPushButton("Close")
        self._close_btn.setStyleSheet(
            btn_style
            + "QPushButton {"
            "  background: #334155; color: #e2e8f0; border: 1px solid #475569;"
            "}"
            "QPushButton:hover { background: #475569; }"
        )
        self._close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(self._close_btn)

        outer.addWidget(footer)

        # Auto-advance timer
        self._poll_timer = QtCore.QTimer(self)
        self._poll_timer.timeout.connect(self._check_auto_advance)
        self._poll_timer.start(1000)

        # Initial context detection
        self._detect_initial_context()

    # ── Context & Auto-Advance ───────────────────────────────────────
    
    def _slides_loaded(self) -> bool:
        if not hasattr(self._parent_window, "_project_dock"):
            return False
        return len(self._parent_window._project_dock.slides()) > 0
        
    def _registration_done(self) -> bool:
        if not hasattr(self._parent_window, "_last_result"):
            return False
        return self._parent_window._last_result is not None

    def _detect_initial_context(self) -> None:
        if self._registration_done():
            # Jump to View Results
            self._show_step(7)
        elif self._slides_loaded():
            # Jump to Settings
            self._show_step(4)
        else:
            self._show_step(0)
            
    def _check_auto_advance(self) -> None:
        """Poll the parent window state and auto-advance if an action completes."""
        if self._current_step == 2:  # Load Data
            if self._slides_loaded():
                logger.info("Tutorial: Detected slides loaded, advancing.")
                self._go_next()
        elif self._current_step == 5:  # Run Registration
            # We don't advance immediately to wait, but if registration is done, jump
            if self._registration_done():
                logger.info("Tutorial: Detected registration complete, jumping to View Results.")
                self._show_step(7)

    # ── Navigation ───────────────────────────────────────────────────

    def _set_bubble_state(self, lbl: QtWidgets.QLabel, active: bool) -> None:
        if active:
            lbl.setStyleSheet("background: #0ea5e9; border-radius: 5px;")
        else:
            lbl.setStyleSheet("background: #334155; border-radius: 5px;")

    def _show_step(self, index: int) -> None:
        index = max(0, min(index, len(_STEPS) - 1))
        self._current_step = index
        step = _STEPS[index]

        self._icon_label.setText(step.icon)
        self._title_label.setText(step.title)
        self._step_counter.setText(f"Step {index + 1} of {len(_STEPS)}")
        self._body.setHtml(step.body)
        
        # Update bubbles
        for i, b in enumerate(self._bubbles):
            self._set_bubble_state(b, i == index)
            
        # Embedded Action Button
        if step.action_label and step.action_id:
            self._action_btn.setText(step.action_label)
            self._action_btn.setProperty("action_id", step.action_id)
            self._action_btn.setVisible(True)
        else:
            self._action_btn.setVisible(False)

        self._prev_btn.setEnabled(index > 0)

        is_last = index == len(_STEPS) - 1
        self._next_btn.setVisible(not is_last)
        self._close_btn.setVisible(True)
        if is_last:
            self._close_btn.setText("Finish")
        else:
            self._close_btn.setText("Close")
            
    def _on_action_clicked(self) -> None:
        action_id = self._action_btn.property("action_id")
        if action_id == "load_slides":
            if hasattr(self._parent_window, "_open_slide_folder"):
                self._parent_window._open_slide_folder()
        elif action_id == "run_registration":
            if hasattr(self._parent_window, "_start_registration"):
                self._parent_window._start_registration()
                self._go_next() # Advance to Wait step manually

    def _go_next(self) -> None:
        if self._current_step < len(_STEPS) - 1:
            self._show_step(self._current_step + 1)

    def _go_prev(self) -> None:
        if self._current_step > 0:
            self._show_step(self._current_step - 1)

    def _on_dont_show_toggled(self, checked: bool) -> None:
        settings = QtCore.QSettings("VALIS", "Workstation")
        settings.setValue(_SETTINGS_KEY_SKIP_TUTORIAL, checked)
        logger.debug("Quick tutorial 'don't show' set to %s", checked)

    # ── Class helpers ────────────────────────────────────────────────

    @staticmethod
    def should_show_on_startup() -> bool:
        """Return ``True`` unless the user opted out via the checkbox."""
        settings = QtCore.QSettings("VALIS", "Workstation")
        return not settings.value(
            _SETTINGS_KEY_SKIP_TUTORIAL, False, type=bool
        )

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Allow arrow keys for navigation."""
        if event.key() == QtCore.Qt.Key.Key_Right:
            self._go_next()
        elif event.key() == QtCore.Qt.Key.Key_Left:
            self._go_prev()
        else:
            super().keyPressEvent(event)
