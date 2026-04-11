from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtGui, QtWidgets

if TYPE_CHECKING:
    from valis_workstation.main_window import MainWindow


def build_actions(window: MainWindow) -> None:
    style = window.style()

    file_menu = window.menuBar().addMenu("File")

    open_action = QtGui.QAction("Open Slide Folder", window)
    open_action.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirIcon))
    open_action.triggered.connect(window._open_slide_folder)
    file_menu.addAction(open_action)

    # Recent folders submenu
    window._recent_menu = file_menu.addMenu("Recent Folders")
    window._recent_menu.setIcon(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView)
    )
    window._update_recent_folders_menu()

    file_menu.addSeparator()

    save_config_action = QtGui.QAction("Save Configuration...", window)
    save_config_action.setIcon(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton)
    )
    save_config_action.triggered.connect(window._save_configuration)
    file_menu.addAction(save_config_action)

    load_config_action = QtGui.QAction("Load Configuration...", window)
    load_config_action.setIcon(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogOpenButton)
    )
    load_config_action.triggered.connect(window._load_configuration)
    file_menu.addAction(load_config_action)

    file_menu.addSeparator()

    run_action = QtGui.QAction("Run Registration", window)
    run_action.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay))
    run_action.triggered.connect(window._start_registration)
    file_menu.addAction(run_action)

    resume_action = QtGui.QAction("Resume Last Registration", window)
    resume_action.setIcon(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_BrowserReload)
    )
    resume_action.triggered.connect(window._resume_last_registration)
    file_menu.addAction(resume_action)

    file_menu.addSeparator()

    preferences_action = QtGui.QAction("Preferences...", window)
    preferences_action.setIcon(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView)
    )
    preferences_action.setShortcut("Ctrl+,")
    preferences_action.triggered.connect(window._show_preferences)
    file_menu.addAction(preferences_action)

    view_menu = window.menuBar().addMenu("View")

    reset_layout_action = QtGui.QAction("Reset Layout", window)
    reset_layout_action.setShortcut("Ctrl+Shift+L")
    reset_layout_action.setToolTip("Reset all panels to their default sizes")
    reset_layout_action.triggered.connect(window.reset_layout)
    view_menu.addAction(reset_layout_action)

    toggle_left_action = QtGui.QAction("Toggle Left Sidebar", window)
    toggle_left_action.setShortcut("Ctrl+[")
    toggle_left_action.triggered.connect(window.toggle_left_sidebar)
    view_menu.addAction(toggle_left_action)

    toggle_right_action = QtGui.QAction("Toggle Right Sidebar", window)
    toggle_right_action.setShortcut("Ctrl+]")
    toggle_right_action.triggered.connect(window.toggle_right_sidebar)
    view_menu.addAction(toggle_right_action)

    expand_center_action = QtGui.QAction("Expand Center", window)
    expand_center_action.setShortcut("Ctrl+Shift+C")
    expand_center_action.triggered.connect(window.expand_center)
    view_menu.addAction(expand_center_action)

    fit_content_action = QtGui.QAction("Fit to Content", window)
    fit_content_action.triggered.connect(window.fit_to_content)
    view_menu.addAction(fit_content_action)

    tools_menu = window.menuBar().addMenu("Tools")

    blink_action = QtGui.QAction("Blink", window)
    blink_action.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_BrowserReload))
    blink_action.triggered.connect(window._blink)
    tools_menu.addAction(blink_action)

    plot_action = QtGui.QAction("Analysis Plot", window)
    plot_action.setIcon(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogInfoView)
    )
    plot_action.triggered.connect(window._show_analysis_plot)
    tools_menu.addAction(plot_action)

    quality_action = QtGui.QAction("Quality Report", window)
    quality_action.setIcon(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogContentsView)
    )
    quality_action.triggered.connect(window._show_quality_report)
    tools_menu.addAction(quality_action)

    warp_action = QtGui.QAction("Warp Annotations", window)
    warp_action.setIcon(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogListView)
    )
    warp_action.triggered.connect(window._warp_annotations)
    tools_menu.addAction(warp_action)

    tools_menu.addSeparator()

    save_options_action = QtGui.QAction("Save Options...", window)
    save_options_action.setIcon(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton)
    )
    save_options_action.triggered.connect(window._show_save_options)
    tools_menu.addAction(save_options_action)

    export_roi_action = QtGui.QAction("Export ROI Crop...", window)
    export_roi_action.setIcon(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogInfoView)
    )
    export_roi_action.triggered.connect(window._export_roi_crop)
    tools_menu.addAction(export_roi_action)

    merge_action = QtGui.QAction("Merge Slides...", window)
    merge_action.setIcon(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogListView)
    )
    merge_action.triggered.connect(window._merge_slides)
    tools_menu.addAction(merge_action)

    tools_menu.addSeparator()
    export_bundle_action = QtGui.QAction("Export Session Bundle...", window)
    export_bundle_action.triggered.connect(window._export_session_bundle)
    tools_menu.addAction(export_bundle_action)

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
    window._update_tools_enabled()

    help_menu = window.menuBar().addMenu("Help")

    user_manual_action = QtGui.QAction("Manual (HTML)", window)
    user_manual_action.setIcon(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView)
    )
    user_manual_action.triggered.connect(window._open_user_manual)
    help_menu.addAction(user_manual_action)

    tutorial_action = QtGui.QAction("Tutorial (HTML)", window)
    tutorial_action.setIcon(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogHelpButton)
    )
    tutorial_action.triggered.connect(window._open_tutorial)
    help_menu.addAction(tutorial_action)

    quick_start_action = QtGui.QAction("Quick Start Guide", window)
    quick_start_action.setIcon(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TitleBarMenuButton)
    )
    quick_start_action.triggered.connect(window._open_quick_start)
    help_menu.addAction(quick_start_action)

    help_menu.addSeparator()

    report_issue_action = QtGui.QAction("Report Issue", window)
    report_issue_action.setIcon(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxWarning)
    )
    report_issue_action.triggered.connect(window._report_issue)
    help_menu.addAction(report_issue_action)

    help_menu.addSeparator()

    perf_stats_action = QtGui.QAction("Performance Statistics", window)
    perf_stats_action.setShortcut("Ctrl+Shift+P")
    perf_stats_action.triggered.connect(window._show_performance_stats)
    help_menu.addAction(perf_stats_action)

    diagnostics_action = QtGui.QAction("Diagnostics", window)
    diagnostics_action.triggered.connect(window._show_diagnostics)
    help_menu.addAction(diagnostics_action)

    help_menu.addSeparator()

    about_action = QtGui.QAction("About VALIS Workstation", window)
    about_action.setIcon(
        style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxInformation)
    )
    about_action.triggered.connect(window._show_about)
    help_menu.addAction(about_action)


def setup_keyboard_shortcuts(window: MainWindow) -> None:
    """Setup keyboard shortcuts for common operations."""
    open_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+O"), window)
    open_shortcut.activated.connect(window._open_slide_folder)

    run_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+R"), window)
    run_shortcut.activated.connect(window._start_registration)

    blink_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+B"), window)
    blink_shortcut.activated.connect(window._blink)

    reset_layout_shortcut = QtGui.QShortcut(
        QtGui.QKeySequence("Ctrl+Shift+L"), window
    )
    reset_layout_shortcut.activated.connect(window.reset_layout)

    toggle_left_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+["), window)
    toggle_left_shortcut.activated.connect(window.toggle_left_sidebar)

    toggle_right_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+]"), window)
    toggle_right_shortcut.activated.connect(window.toggle_right_sidebar)

    expand_center_shortcut = QtGui.QShortcut(
        QtGui.QKeySequence("Ctrl+Shift+C"), window
    )
    expand_center_shortcut.activated.connect(window.expand_center)

    quit_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Q"), window)
    quit_shortcut.activated.connect(window.close)
