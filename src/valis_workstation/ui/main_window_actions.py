from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets
from valis_workstation.ui.icons import load_icon

if TYPE_CHECKING:
    from valis_workstation.main_window import MainWindow


logger = logging.getLogger(__name__)


def _configure_action(
    window: MainWindow,
    action: QtGui.QAction,
    *,
    status_tip: str,
    tool_tip: str | None = None,
) -> None:
    action.setStatusTip(status_tip)
    action.setToolTip(tool_tip or status_tip)
    action.hovered.connect(
        lambda a=action: window._status_bar.showMessage(a.statusTip(), 5000)
    )


def build_actions(window: MainWindow) -> None:
    quick_toolbar = window.addToolBar("Quick Actions")
    quick_toolbar.setObjectName("QuickActionsToolbar")
    quick_toolbar.setMovable(False)
    quick_toolbar.setFloatable(False)
    quick_toolbar.setIconSize(QtCore.QSize(16, 16))
    quick_toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

    file_menu = window.menuBar().addMenu("File")

    open_action = QtGui.QAction("Open Slide Folder", window)
    open_action.setIcon(
        load_icon("folder_open", window, QtWidgets.QStyle.StandardPixmap.SP_DirIcon)
    )
    open_action.setShortcut("Ctrl+O")
    _configure_action(
        window,
        open_action,
        status_tip="Open a slide folder (Ctrl+O)",
    )
    open_action.triggered.connect(window._open_slide_folder)
    file_menu.addAction(open_action)

    open_recent_action = QtGui.QAction("Open Most Recent Folder", window)
    open_recent_action.setShortcut("Ctrl+Shift+O")
    open_recent_action.setIcon(
        load_icon(
            "recent",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView,
        )
    )
    _configure_action(
        window,
        open_recent_action,
        status_tip="Open the most recent folder (Ctrl+Shift+O)",
    )
    open_recent_action.triggered.connect(window._open_most_recent_folder)
    file_menu.addAction(open_recent_action)

    # Recent folders submenu
    window._recent_menu = file_menu.addMenu("Recent Folders")
    window._recent_menu.setIcon(
        load_icon(
            "recent",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView,
        )
    )
    window._update_recent_folders_menu()

    file_menu.addSeparator()

    save_config_action = QtGui.QAction("Save Configuration...", window)
    save_config_action.setIcon(
        load_icon(
            "save",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton,
        )
    )
    _configure_action(
        window,
        save_config_action,
        status_tip="Save current registration settings to JSON",
    )
    save_config_action.triggered.connect(window._save_configuration)
    file_menu.addAction(save_config_action)

    load_config_action = QtGui.QAction("Load Configuration...", window)
    load_config_action.setIcon(
        load_icon(
            "open",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_DialogOpenButton,
        )
    )
    _configure_action(
        window,
        load_config_action,
        status_tip="Load registration settings from JSON",
    )
    load_config_action.triggered.connect(window._load_configuration)
    file_menu.addAction(load_config_action)

    file_menu.addSeparator()

    run_action = QtGui.QAction("Run Registration", window)
    run_action.setIcon(
        load_icon("play", window, QtWidgets.QStyle.StandardPixmap.SP_MediaPlay)
    )
    run_action.setShortcuts([QtGui.QKeySequence("Ctrl+R"), QtGui.QKeySequence("F5")])
    _configure_action(
        window,
        run_action,
        status_tip="Start registration (Ctrl+R, F5)",
    )
    run_action.triggered.connect(window._start_registration)
    file_menu.addAction(run_action)

    cancel_action = QtGui.QAction("Cancel Registration", window)
    cancel_action.setIcon(
        load_icon("cancel", window, QtWidgets.QStyle.StandardPixmap.SP_DialogCancelButton)
    )
    cancel_action.setShortcut("Esc")
    cancel_action.setEnabled(False)
    _configure_action(
        window,
        cancel_action,
        status_tip="Cancel active registration",
    )
    cancel_action.triggered.connect(window._request_cancellation)
    file_menu.addAction(cancel_action)

    resume_action = QtGui.QAction("Resume Last Registration", window)
    resume_action.setIcon(
        load_icon(
            "refresh", window, QtWidgets.QStyle.StandardPixmap.SP_BrowserReload
        )
    )
    _configure_action(
        window,
        resume_action,
        status_tip="Resume the last registration context",
    )
    resume_action.triggered.connect(window._resume_last_registration)
    file_menu.addAction(resume_action)

    file_menu.addSeparator()

    preferences_action = QtGui.QAction("Preferences...", window)
    preferences_action.setIcon(
        load_icon(
            "settings",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView,
        )
    )
    preferences_action.setShortcut("Ctrl+,")
    _configure_action(
        window,
        preferences_action,
        status_tip="Open application preferences (Ctrl+,)",
    )
    preferences_action.triggered.connect(window._show_preferences)
    file_menu.addAction(preferences_action)

    view_menu = window.menuBar().addMenu("View")

    reset_layout_action = QtGui.QAction("Reset Layout", window)
    reset_layout_action.setShortcut("Ctrl+Shift+L")
    reset_layout_action.setIcon(
        load_icon(
            "refresh", window, QtWidgets.QStyle.StandardPixmap.SP_BrowserReload
        )
    )
    _configure_action(
        window,
        reset_layout_action,
        status_tip="Reset all panels to their default sizes (Ctrl+Shift+L)",
    )
    reset_layout_action.triggered.connect(window.reset_layout)
    view_menu.addAction(reset_layout_action)

    toggle_left_action = QtGui.QAction("Toggle Left Sidebar", window)
    toggle_left_action.setIcon(
        load_icon(
            "sidebar_left",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_ArrowLeft,
        )
    )
    toggle_left_action.setShortcut("Ctrl+[")
    toggle_left_action.setCheckable(True)
    toggle_left_action.setChecked(True)
    _configure_action(
        window,
        toggle_left_action,
        status_tip="Show or hide the left sidebar (Ctrl+[)",
    )
    toggle_left_action.triggered.connect(window.toggle_left_sidebar)
    view_menu.addAction(toggle_left_action)

    toggle_right_action = QtGui.QAction("Toggle Right Sidebar", window)
    toggle_right_action.setIcon(
        load_icon(
            "sidebar_right",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_ArrowRight,
        )
    )
    toggle_right_action.setShortcut("Ctrl+]")
    toggle_right_action.setCheckable(True)
    toggle_right_action.setChecked(True)
    _configure_action(
        window,
        toggle_right_action,
        status_tip="Show or hide the right sidebar (Ctrl+])",
    )
    toggle_right_action.triggered.connect(window.toggle_right_sidebar)
    view_menu.addAction(toggle_right_action)

    focus_mode_action = QtGui.QAction("Toggle Focus Mode", window)
    focus_mode_action.setShortcut("Ctrl+Shift+\\")
    focus_mode_action.setCheckable(True)
    focus_mode_action.setIcon(
        load_icon(
            "expand_center", window, QtWidgets.QStyle.StandardPixmap.SP_ArrowForward
        )
    )
    _configure_action(
        window,
        focus_mode_action,
        status_tip="Collapse sidebars for focus mode (Ctrl+Shift+\\)",
    )
    focus_mode_action.toggled.connect(window.toggle_focus_mode)
    view_menu.addAction(focus_mode_action)

    fit_content_action = QtGui.QAction("Fit to Content", window)
    fit_content_action.setIcon(
        load_icon(
            "fit_content", window, QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon
        )
    )
    _configure_action(
        window,
        fit_content_action,
        status_tip="Fit timeline and reset viewer framing",
    )
    fit_content_action.triggered.connect(window.fit_to_content)
    view_menu.addAction(fit_content_action)

    # Quick toolbar actions (pro workflow: most-used commands one click away)
    quick_toolbar.addAction(open_action)
    quick_toolbar.addAction(run_action)
    quick_toolbar.addAction(cancel_action)
    quick_toolbar.addAction(open_recent_action)
    quick_toolbar.addAction(resume_action)
    quick_toolbar.addSeparator()
    quick_toolbar.addAction(reset_layout_action)
    quick_toolbar.addAction(focus_mode_action)
    quick_toolbar.addAction(fit_content_action)

    tools_menu = window.menuBar().addMenu("Tools")

    blink_action = QtGui.QAction("Blink", window)
    blink_action.setIcon(
        load_icon(
            "eye",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_BrowserReload,
        )
    )
    _configure_action(
        window,
        blink_action,
        status_tip="Open blink comparison viewer for registered slides",
    )
    blink_action.triggered.connect(window._blink)
    tools_menu.addAction(blink_action)

    plot_action = QtGui.QAction("Analysis Plot", window)
    plot_action.setIcon(
        load_icon(
            "chart",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_FileDialogInfoView,
        )
    )
    _configure_action(
        window,
        plot_action,
        status_tip="Open summary analysis plot",
    )
    plot_action.triggered.connect(window._show_analysis_plot)
    tools_menu.addAction(plot_action)

    quality_action = QtGui.QAction("Quality Report", window)
    quality_action.setIcon(
        load_icon(
            "report",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_FileDialogContentsView,
        )
    )
    _configure_action(
        window,
        quality_action,
        status_tip="Open tabular quality report",
    )
    quality_action.triggered.connect(window._show_quality_report)
    tools_menu.addAction(quality_action)

    warp_action = QtGui.QAction("Warp Annotations", window)
    warp_action.setIcon(
        load_icon(
            "warp",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_FileDialogListView,
        )
    )
    _configure_action(
        window,
        warp_action,
        status_tip="Warp annotation files into registered space",
    )
    warp_action.triggered.connect(window._warp_annotations)
    tools_menu.addAction(warp_action)

    tools_menu.addSeparator()

    save_options_action = QtGui.QAction("Save Options...", window)
    save_options_action.setIcon(
        load_icon(
            "save",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton,
        )
    )
    _configure_action(
        window,
        save_options_action,
        status_tip="Configure save/export options",
    )
    save_options_action.triggered.connect(window._show_save_options)
    tools_menu.addAction(save_options_action)

    export_roi_action = QtGui.QAction("Export ROI Crop...", window)
    export_roi_action.setIcon(
        load_icon(
            "roi",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_FileDialogInfoView,
        )
    )
    _configure_action(
        window,
        export_roi_action,
        status_tip="Export a region of interest from registered slides",
    )
    export_roi_action.triggered.connect(window._export_roi_crop)
    tools_menu.addAction(export_roi_action)

    merge_action = QtGui.QAction("Merge Slides...", window)
    merge_action.setIcon(
        load_icon(
            "merge",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_FileDialogListView,
        )
    )
    _configure_action(
        window,
        merge_action,
        status_tip="Merge registered slides into a multi-channel output",
    )
    merge_action.triggered.connect(window._merge_slides)
    tools_menu.addAction(merge_action)

    tools_menu.addSeparator()
    export_bundle_action = QtGui.QAction("Export Session Bundle...", window)
    export_bundle_action.setIcon(
        load_icon(
            "bundle",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_DirIcon,
        )
    )
    _configure_action(
        window,
        export_bundle_action,
        status_tip="Export config + diagnostics + logs as a session bundle",
    )
    export_bundle_action.triggered.connect(window._export_session_bundle)
    tools_menu.addAction(export_bundle_action)

    # Results toolbar (visible once a registration completes)
    results_toolbar = window.addToolBar("Results")
    results_toolbar.setObjectName("ResultsToolbar")
    results_toolbar.setMovable(False)
    results_toolbar.setFloatable(False)
    results_toolbar.setVisible(False)
    results_toolbar.addAction(blink_action)
    results_toolbar.addAction(plot_action)
    results_toolbar.addAction(quality_action)
    results_toolbar.addAction(warp_action)
    results_toolbar.addAction(export_roi_action)
    results_toolbar.addAction(merge_action)
    window._results_toolbar = results_toolbar

    quick_toolbar.addSeparator()
    quick_toolbar.addAction(blink_action)

    # Store result-dependent actions for contextual enable/disable
    window._result_actions: list[QtGui.QAction] = [
        blink_action,
        plot_action,
        quality_action,
        warp_action,
        save_options_action,
        export_roi_action,
        merge_action,
    ]
    window._registration_run_actions = [run_action, resume_action]
    window._cancel_registration_action = cancel_action

    window._toggle_left_action = toggle_left_action
    window._toggle_right_action = toggle_right_action
    window._focus_mode_action = focus_mode_action
    window._update_tools_enabled()

    help_menu = window.menuBar().addMenu("Help")

    quick_tutorial_action = QtGui.QAction("Quick Tutorial", window)
    quick_tutorial_action.setIcon(
        load_icon(
            "tutorial",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_DialogHelpButton,
        )
    )
    quick_tutorial_action.setShortcut("F1")
    _configure_action(
        window,
        quick_tutorial_action,
        status_tip="Open the in-app quick tutorial (F1)",
        tool_tip="Step-by-step guide to VALIS Workstation (F1)",
    )
    quick_tutorial_action.triggered.connect(window._show_quick_tutorial)
    help_menu.addAction(quick_tutorial_action)

    help_menu.addSeparator()

    user_manual_action = QtGui.QAction("Manual (HTML)", window)
    user_manual_action.setIcon(
        load_icon(
            "manual",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView,
        )
    )
    _configure_action(
        window,
        user_manual_action,
        status_tip="Open the local user manual",
    )
    user_manual_action.triggered.connect(window._open_user_manual)
    help_menu.addAction(user_manual_action)

    tutorial_action = QtGui.QAction("Tutorial (HTML)", window)
    tutorial_action.setIcon(
        load_icon(
            "tutorial",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_DialogHelpButton,
        )
    )
    _configure_action(
        window,
        tutorial_action,
        status_tip="Open the local tutorial",
    )
    tutorial_action.triggered.connect(window._open_tutorial)
    help_menu.addAction(tutorial_action)

    # Add Quick Tutorial to the quick toolbar
    quick_toolbar.addSeparator()
    quick_toolbar.addAction(quick_tutorial_action)

    quick_start_action = QtGui.QAction("Quick Start Guide", window)
    quick_start_action.setIcon(
        load_icon(
            "quick_start",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_TitleBarMenuButton,
        )
    )
    _configure_action(
        window,
        quick_start_action,
        status_tip="Open quick-start documentation",
    )
    quick_start_action.triggered.connect(window._open_quick_start)
    help_menu.addAction(quick_start_action)

    help_menu.addSeparator()

    report_issue_action = QtGui.QAction("Report Issue", window)
    report_issue_action.setIcon(
        load_icon(
            "issue",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_MessageBoxWarning,
        )
    )
    _configure_action(
        window,
        report_issue_action,
        status_tip="Open issue tracker",
    )
    report_issue_action.triggered.connect(window._report_issue)
    help_menu.addAction(report_issue_action)

    help_menu.addSeparator()

    perf_stats_action = QtGui.QAction("Performance Statistics", window)
    perf_stats_action.setIcon(
        load_icon(
            "speed",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon,
        )
    )
    perf_stats_action.setShortcut("Ctrl+Shift+P")
    _configure_action(
        window,
        perf_stats_action,
        status_tip="Open performance diagnostics (Ctrl+Shift+P)",
    )
    perf_stats_action.triggered.connect(window._show_performance_stats)
    help_menu.addAction(perf_stats_action)

    diagnostics_action = QtGui.QAction("Diagnostics", window)
    diagnostics_action.setIcon(
        load_icon(
            "diagnostics",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_FileDialogContentsView,
        )
    )
    _configure_action(
        window,
        diagnostics_action,
        status_tip="Open environment diagnostics",
    )
    diagnostics_action.triggered.connect(window._show_diagnostics)
    help_menu.addAction(diagnostics_action)

    help_menu.addSeparator()

    about_action = QtGui.QAction("About VALIS Workstation", window)
    about_action.setIcon(
        load_icon(
            "info",
            window,
            QtWidgets.QStyle.StandardPixmap.SP_MessageBoxInformation,
        )
    )
    _configure_action(
        window,
        about_action,
        status_tip="Show application version and credits",
    )
    about_action.triggered.connect(window._show_about)
    help_menu.addAction(about_action)


def setup_keyboard_shortcuts(window: MainWindow) -> None:
    """Keyboard shortcuts are registered directly on ``QAction`` instances."""
    logger.debug("QAction-based shortcuts configured")
