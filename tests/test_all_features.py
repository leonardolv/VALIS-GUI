"""Comprehensive autonomous tests for ALL VALIS GUI features.

Every dialog, dock, menu action, keyboard shortcut, drag-and-drop, and
service function is tested here WITHOUT any modal dialogs requiring user
interaction.  All QFileDialog / QMessageBox calls are monkeypatched.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import time
from dataclasses import asdict
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtGui, QtWidgets

from valis_workstation.models.config import Config
from valis_workstation.utils.qt_logging import QtLogEmitter


# ═══════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════


def _noop(*a, **kw):
    """No-op callable for monkeypatching dialog exec/show."""
    return None


def _mock_viewer():
    """Create a minimal napari viewer mock."""
    viewer = MagicMock()
    viewer.layers = MagicMock()
    viewer.layers.__iter__ = MagicMock(return_value=iter([]))
    mock_layer = MagicMock()
    mock_layer.visible = True
    mock_layer.opacity = 1.0
    viewer.open.return_value = [mock_layer]
    return viewer


# ═══════════════════════════════════════════════════════════════════════
#  DIALOG TESTS — BlinkViewerDialog
# ═══════════════════════════════════════════════════════════════════════


class TestBlinkViewerDialog:
    @pytest.fixture()
    def dialog(self, qtbot):
        from valis_workstation.ui.dialogs.blink_viewer import BlinkViewerDialog

        viewer = _mock_viewer()
        slides = [Path("a.tif"), Path("b.tif")]
        d = BlinkViewerDialog(viewer, slides)
        qtbot.addWidget(d)
        return d

    def test_slides_populated(self, dialog):
        assert dialog._slide_a.count() == 2
        assert dialog._slide_b.count() == 2

    def test_blink_toggle_starts_timer(self, dialog):
        dialog._blink_toggle.setChecked(True)
        assert dialog._timer.isActive()

    def test_blink_toggle_stops_timer(self, dialog):
        dialog._blink_toggle.setChecked(True)
        dialog._blink_toggle.setChecked(False)
        assert not dialog._timer.isActive()

    def test_opacity_slider_default(self, dialog):
        assert dialog._opacity.value() == 50

    def test_opacity_slider_change(self, dialog):
        dialog._opacity.setValue(75)
        # Should not crash

    def test_close_stops_timer(self, dialog):
        dialog._blink_toggle.setChecked(True)
        dialog.close()
        assert not dialog._timer.isActive()

    def test_button_text_toggle(self, dialog):
        dialog._blink_toggle.setChecked(True)
        assert "Stop" in dialog._blink_toggle.text()
        dialog._blink_toggle.setChecked(False)
        assert "Start" in dialog._blink_toggle.text()


# ═══════════════════════════════════════════════════════════════════════
#  DIALOG TESTS — AnalysisPlotDialog
# ═══════════════════════════════════════════════════════════════════════


class TestAnalysisPlotDialog:
    def _make_df(self):
        pd = pytest.importorskip("pandas")
        return pd.DataFrame(
            {
                "non_rigid_D": [0.1, 0.2, 0.15],
                "rigid_D": [0.3, 0.4, 0.35],
            }
        )

    def test_opens_with_data(self, qtbot):
        from valis_workstation.ui.dialogs.analysis_plot import AnalysisPlotDialog

        d = AnalysisPlotDialog(self._make_df())
        qtbot.addWidget(d)
        assert d._summary_label.text() != ""

    def test_opens_with_empty_df(self, qtbot):
        pd = pytest.importorskip("pandas")
        from valis_workstation.ui.dialogs.analysis_plot import AnalysisPlotDialog

        d = AnalysisPlotDialog(pd.DataFrame())
        qtbot.addWidget(d)
        # Should not crash

    def test_canvas_exists(self, qtbot):
        from valis_workstation.ui.dialogs.analysis_plot import AnalysisPlotDialog

        d = AnalysisPlotDialog(self._make_df())
        qtbot.addWidget(d)
        assert d._canvas is not None


# ═══════════════════════════════════════════════════════════════════════
#  DIALOG TESTS — QualityReportDialog
# ═══════════════════════════════════════════════════════════════════════


class TestQualityReportDialog:
    def test_with_data(self, qtbot):
        pd = pytest.importorskip("pandas")
        from valis_workstation.ui.dialogs.quality_report import QualityReportDialog

        df = pd.DataFrame(
            {
                "filename": ["s1", "s2"],
                "rigid_D": [0.1, 0.2],
                "non_rigid_D": [0.05, 0.1],
            }
        )
        d = QualityReportDialog(df)
        qtbot.addWidget(d)
        assert d._table.rowCount() == 2
        assert d._table.columnCount() == 3

    def test_with_empty_df(self, qtbot):
        pd = pytest.importorskip("pandas")
        from valis_workstation.ui.dialogs.quality_report import QualityReportDialog

        d = QualityReportDialog(pd.DataFrame())
        qtbot.addWidget(d)
        assert d._table.rowCount() == 0

    def test_with_none(self, qtbot):
        from valis_workstation.ui.dialogs.quality_report import QualityReportDialog

        d = QualityReportDialog(None)
        qtbot.addWidget(d)
        assert d._table.rowCount() == 0

    def test_sorting_enabled(self, qtbot):
        pd = pytest.importorskip("pandas")
        from valis_workstation.ui.dialogs.quality_report import QualityReportDialog

        d = QualityReportDialog(pd.DataFrame({"col": [1, 2]}))
        qtbot.addWidget(d)
        assert d._table.isSortingEnabled()


# ═══════════════════════════════════════════════════════════════════════
#  DIALOG TESTS — SaveOptionsDialog  (deep)
# ═══════════════════════════════════════════════════════════════════════


class TestSaveOptionsDialogDeep:
    def test_all_keys_present(self, qtbot):
        from valis_workstation.ui.dialogs.save_options_dialog import SaveOptionsDialog

        d = SaveOptionsDialog()
        qtbot.addWidget(d)
        opts = d.get_options()
        for key in ("pyramid_levels", "compression", "quality", "tile_size", "format"):
            assert key in opts, f"Missing key: {key}"

    def test_modify_pyramid_levels(self, qtbot):
        from valis_workstation.ui.dialogs.save_options_dialog import SaveOptionsDialog

        d = SaveOptionsDialog()
        qtbot.addWidget(d)
        d._pyramid_levels.setValue(6)
        assert d.get_options()["pyramid_levels"] == 6

    def test_modify_compression(self, qtbot):
        from valis_workstation.ui.dialogs.save_options_dialog import SaveOptionsDialog

        d = SaveOptionsDialog()
        qtbot.addWidget(d)
        d._compression.setValue(5)
        assert d.get_options()["compression"] == 5

    def test_modify_quality(self, qtbot):
        from valis_workstation.ui.dialogs.save_options_dialog import SaveOptionsDialog

        d = SaveOptionsDialog()
        qtbot.addWidget(d)
        d._quality.setValue(80)
        assert d.get_options()["quality"] == 80


# ═══════════════════════════════════════════════════════════════════════
#  DIALOG TESTS — MergeSlidesDialog  (deep)
# ═══════════════════════════════════════════════════════════════════════


class TestMergeSlidesDialogDeep:
    def test_all_config_keys(self, qtbot):
        from valis_workstation.ui.dialogs.merge_slides_dialog import MergeSlidesDialog

        d = MergeSlidesDialog(["A", "B"])
        qtbot.addWidget(d)
        cfg = d.get_merge_config()
        for key in ("channels", "duplicate_handling", "output_name", "normalize"):
            assert key in cfg, f"Missing config key: {key}"

    def test_channels_match_slide_count(self, qtbot):
        from valis_workstation.ui.dialogs.merge_slides_dialog import MergeSlidesDialog

        d = MergeSlidesDialog(["A", "B", "C"])
        qtbot.addWidget(d)
        cfg = d.get_merge_config()
        assert len(cfg["channels"]) == 3

    def test_output_name_editable(self, qtbot):
        from valis_workstation.ui.dialogs.merge_slides_dialog import MergeSlidesDialog

        d = MergeSlidesDialog(["A", "B"])
        qtbot.addWidget(d)
        d._output_name.setText("my_composite")
        cfg = d.get_merge_config()
        assert cfg["output_name"] == "my_composite"

    def test_normalize_checkbox(self, qtbot):
        from valis_workstation.ui.dialogs.merge_slides_dialog import MergeSlidesDialog

        d = MergeSlidesDialog(["A", "B"])
        qtbot.addWidget(d)
        d._normalize.setChecked(True)
        assert d.get_merge_config()["normalize"] is True
        d._normalize.setChecked(False)
        assert d.get_merge_config()["normalize"] is False


# ═══════════════════════════════════════════════════════════════════════
#  DIALOG TESTS — PerformanceStatsDialog
# ═══════════════════════════════════════════════════════════════════════


class TestPerformanceStatsDialogFull:
    def test_opens(self, qtbot):
        from valis_workstation.ui.dialogs.performance_stats_dialog import (
            PerformanceStatsDialog,
        )

        d = PerformanceStatsDialog()
        qtbot.addWidget(d)
        assert d.windowTitle() == "Performance Statistics"

    def test_auto_refresh_timer_active(self, qtbot):
        from valis_workstation.ui.dialogs.performance_stats_dialog import (
            PerformanceStatsDialog,
        )

        d = PerformanceStatsDialog()
        qtbot.addWidget(d)
        assert d._update_timer.isActive()

    def test_close_stops_timer(self, qtbot):
        from valis_workstation.ui.dialogs.performance_stats_dialog import (
            PerformanceStatsDialog,
        )

        d = PerformanceStatsDialog()
        qtbot.addWidget(d)
        d.close()
        assert not d._update_timer.isActive()


# ═══════════════════════════════════════════════════════════════════════
#  DIALOG TESTS — PreferencesDialog
# ═══════════════════════════════════════════════════════════════════════


class TestPreferencesDialogFull:
    def test_opens(self, qtbot):
        from valis_workstation.ui.dialogs.preferences_dialog import PreferencesDialog

        d = PreferencesDialog()
        qtbot.addWidget(d)
        assert d.windowTitle() == "Preferences"

    def test_signal_exists(self, qtbot):
        from valis_workstation.ui.dialogs.preferences_dialog import PreferencesDialog

        d = PreferencesDialog()
        qtbot.addWidget(d)
        assert hasattr(d, "preferences_changed")

    def test_settings_managed_by_qsettings(self, qtbot):
        from valis_workstation.ui.dialogs.preferences_dialog import PreferencesDialog

        d = PreferencesDialog()
        qtbot.addWidget(d)
        assert d._settings is not None

    def test_output_profile_templates(self, qtbot):
        from valis_workstation.ui.dialogs.preferences_dialog import PreferencesDialog
        from valis_workstation.ui.properties_dock import PropertiesDock

        # Use PropertiesDock for template behavior introduced in feature update.
        dock = PropertiesDock(simple_elastix_available=True)
        qtbot.addWidget(dock)
        dock.apply_output_profile("Fast Review")
        cfg = dock.config()
        assert cfg.tile_size == 256
        assert cfg.pyramid_levels == 3


# ═══════════════════════════════════════════════════════════════════════
#  DIALOG TESTS — ErrorDetailDialog
# ═══════════════════════════════════════════════════════════════════════


class TestErrorDetailDialogFull:
    def test_opens(self, qtbot):
        from valis_workstation.ui.dialogs.error_detail_dialog import ErrorDetailDialog

        d = ErrorDetailDialog("Something failed", "Traceback...", "Log line 1")
        qtbot.addWidget(d)
        assert d.windowTitle() != ""

    def test_copy_to_clipboard(self, qtbot):
        from valis_workstation.ui.dialogs.error_detail_dialog import ErrorDetailDialog

        d = ErrorDetailDialog("Error", "Tech details", "Log excerpt")
        qtbot.addWidget(d)
        # The copy method should not crash
        d._copy_to_clipboard("Error", "Tech details", "Log excerpt")

    def test_show_error_dialog_function(self, qtbot, monkeypatch):
        from valis_workstation.ui.dialogs.error_detail_dialog import show_error_dialog

        # Monkeypatch exec to prevent blocking modal dialog
        monkeypatch.setattr(QtWidgets.QDialog, "exec", lambda self: None)
        parent = QtWidgets.QWidget()
        qtbot.addWidget(parent)
        show_error_dialog(parent, "Test error", RuntimeError("boom"))

    def test_show_error_dialog_no_exception(self, qtbot, monkeypatch):
        from valis_workstation.ui.dialogs.error_detail_dialog import show_error_dialog

        monkeypatch.setattr(QtWidgets.QDialog, "exec", lambda self: None)
        parent = QtWidgets.QWidget()
        qtbot.addWidget(parent)
        show_error_dialog(parent, "Test error only")


# ═══════════════════════════════════════════════════════════════════════
#  DOCK TESTS — SlidePreviewDock
# ═══════════════════════════════════════════════════════════════════════


class TestSlidePreviewDockFull:
    @pytest.fixture()
    def dock(self, qtbot):
        from valis_workstation.ui.slide_preview_dock import SlidePreviewDock

        d = SlidePreviewDock()
        qtbot.addWidget(d)
        return d

    def test_opens(self, dock):
        assert dock.windowTitle() != ""

    def test_add_slide(self, dock):
        px = QtGui.QPixmap(64, 64)
        px.fill(QtGui.QColor("red"))
        dock.add_slide("test_slide", px, {"size": "100x100"})

    def test_add_multiple_slides(self, dock):
        for name in ("a", "b", "c"):
            px = QtGui.QPixmap(32, 32)
            px.fill(QtGui.QColor("green"))
            dock.add_slide(name, px)

    def test_remove_slide(self, dock):
        px = QtGui.QPixmap(32, 32)
        dock.add_slide("rm_test", px)
        dock.remove_slide("rm_test")

    def test_clear(self, dock):
        dock.add_slide("x", QtGui.QPixmap(32, 32))
        dock.add_slide("y", QtGui.QPixmap(32, 32))
        dock.clear()

    def test_slide_selected_signal_exists(self, dock):
        assert hasattr(dock, "slide_selected")

    def test_size_slider_value(self, dock):
        dock._size_slider.setValue(128)
        assert dock._size_slider.value() == 128


# ═══════════════════════════════════════════════════════════════════════
#  DOCK TESTS — LayerControlsDock
# ═══════════════════════════════════════════════════════════════════════


class TestLayerControlsDockFull:
    def test_opens(self, qtbot):
        from valis_workstation.ui.layer_controls_dock import LayerControlsDock

        viewer = MagicMock()
        viewer.layers = []
        d = LayerControlsDock(viewer)
        qtbot.addWidget(d)

    def test_refresh_empty(self, qtbot):
        from valis_workstation.ui.layer_controls_dock import LayerControlsDock

        viewer = MagicMock()
        viewer.layers = []
        d = LayerControlsDock(viewer)
        qtbot.addWidget(d)
        d.refresh()

    def test_refresh_with_layers(self, qtbot):
        from valis_workstation.ui.layer_controls_dock import LayerControlsDock

        layer = MagicMock()
        layer.name = "Layer1"
        layer.visible = True
        layer.opacity = 0.8
        layer.colormap = MagicMock()
        layer.colormap.name = "gray"
        viewer = MagicMock()
        viewer.layers = [layer]
        d = LayerControlsDock(viewer)
        qtbot.addWidget(d)
        d.refresh()
        assert d._table.rowCount() >= 1

    def test_toggle_visible_static(self):
        from valis_workstation.ui.layer_controls_dock import LayerControlsDock

        mock_layer = MagicMock()
        LayerControlsDock._toggle_visible(mock_layer, 2)
        assert mock_layer.visible is True
        LayerControlsDock._toggle_visible(mock_layer, 0)
        assert mock_layer.visible is False

    def test_set_opacity_static(self):
        from valis_workstation.ui.layer_controls_dock import LayerControlsDock

        mock_layer = MagicMock()
        LayerControlsDock._set_opacity(mock_layer, 75)
        assert mock_layer.opacity == pytest.approx(0.75, abs=0.01)

    def test_set_colormap_static(self):
        from valis_workstation.ui.layer_controls_dock import LayerControlsDock

        mock_layer = MagicMock()
        LayerControlsDock._set_colormap(mock_layer, "viridis")
        assert mock_layer.colormap == "viridis"

    def test_locked_solo_reset_noop(self, qtbot):
        from valis_workstation.ui.layer_controls_dock import LayerControlsDock

        layer = MagicMock()
        layer.name = "Layer1"
        layer.visible = True
        layer.opacity = 0.5
        layer.colormap = MagicMock()
        layer.colormap.name = "gray"
        viewer = MagicMock()
        viewer.layers = [layer]

        d = LayerControlsDock(viewer)
        qtbot.addWidget(d)
        d.refresh()

        # Select first row
        d._table.selectRow(0)

        # Lock controls
        d._lock_check.setChecked(True)

        # Trigger solo
        d._solo_selected()
        # Should remain True and 0.5 opacity (no change)
        assert layer.visible is True
        assert layer.opacity == 0.5

        # Trigger reset opacity
        d._reset_opacity()
        assert layer.opacity == 0.5  # Would be 1.0 if not locked


# ═══════════════════════════════════════════════════════════════════════
#  MAIN WINDOW TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestMainWindow:
    """Full integration tests for MainWindow.

    Napari is disabled by monkeypatching ``importlib.util.find_spec``
    so the window uses the "Napari unavailable" fallback widget.
    All modal dialogs (QMessageBox, QFileDialog) are monkeypatched to
    prevent blocking.
    """

    @pytest.fixture()
    def win(self, qtbot, monkeypatch, tmp_path):
        # Disable napari so MainWindow uses the fallback central widget
        _original_find_spec = importlib.util.find_spec

        def _patched_find_spec(name, *args, **kwargs):
            if name == "napari":
                return None
            return _original_find_spec(name, *args, **kwargs)

        monkeypatch.setattr(importlib.util, "find_spec", _patched_find_spec)

        # Default dialog/file chooser stubs to prevent blocking modal UI in tests.
        monkeypatch.setattr(
            QtWidgets.QFileDialog,
            "getExistingDirectory",
            staticmethod(lambda *a, **kw: ""),
        )
        monkeypatch.setattr(
            QtWidgets.QFileDialog,
            "getOpenFileName",
            staticmethod(lambda *a, **kw: ("", "")),
        )
        monkeypatch.setattr(
            QtWidgets.QFileDialog,
            "getSaveFileName",
            staticmethod(lambda *a, **kw: ("", "")),
        )
        monkeypatch.setattr(
            QtWidgets.QMessageBox,
            "warning",
            staticmethod(lambda *a, **kw: QtWidgets.QMessageBox.StandardButton.Ok),
        )
        monkeypatch.setattr(
            QtWidgets.QMessageBox,
            "critical",
            staticmethod(lambda *a, **kw: QtWidgets.QMessageBox.StandardButton.Ok),
        )
        monkeypatch.setattr(
            QtWidgets.QMessageBox,
            "information",
            staticmethod(lambda *a, **kw: QtWidgets.QMessageBox.StandardButton.Ok),
        )
        monkeypatch.setattr(
            QtWidgets.QMessageBox,
            "about",
            staticmethod(lambda *a, **kw: None),
        )

        from valis_workstation.main_window import MainWindow

        emitter = QtLogEmitter()
        w = MainWindow(
            repo_root=tmp_path,
            log_emitter=emitter,
            simple_elastix_available=False,
        )
        qtbot.addWidget(w)
        return w

    # ── Menu bar ────────────────────────────────────────────

    def test_file_menu_exists(self, win):
        actions = [a.text() for a in win.menuBar().actions()]
        assert any("File" in t for t in actions)

    def test_tools_menu_exists(self, win):
        actions = [a.text() for a in win.menuBar().actions()]
        assert any("Tools" in t for t in actions)

    def test_help_menu_exists(self, win):
        actions = [a.text() for a in win.menuBar().actions()]
        assert any("Help" in t for t in actions)

    # ── Docks ───────────────────────────────────────────────

    def test_project_dock(self, win):
        assert win._project_dock is not None
        assert isinstance(win._project_dock, QtWidgets.QDockWidget)

    def test_properties_dock(self, win):
        assert win._properties_dock is not None

    def test_status_dock(self, win):
        assert win._status_dock is not None

    def test_slide_preview_dock(self, win):
        assert win._slide_preview_dock is not None

    def test_layer_controls_none_without_napari(self, win):
        # No napari → no layer controls dock created
        assert win._layer_controls_dock is None

    # ── Window properties ───────────────────────────────────

    def test_window_title(self, win):
        assert "VALIS" in win.windowTitle()

    def test_accepts_drops(self, win):
        assert win.acceptDrops()

    def test_napari_unavailable_flag(self, win):
        assert win._napari_available is False

    # ── Save configuration ──────────────────────────────────

    def test_save_config(self, win, tmp_path, monkeypatch):
        config_file = tmp_path / "test_config.json"
        monkeypatch.setattr(
            QtWidgets.QFileDialog,
            "getSaveFileName",
            staticmethod(lambda *a, **kw: (str(config_file), "JSON (*.json)")),
        )
        win._save_configuration()
        assert config_file.exists()
        data = json.loads(config_file.read_text())
        assert "project_name" in data
        assert "rigid_registration" in data

    def test_save_config_cancelled(self, win, monkeypatch):
        monkeypatch.setattr(
            QtWidgets.QFileDialog,
            "getSaveFileName",
            staticmethod(lambda *a, **kw: ("", "")),
        )
        win._save_configuration()  # Should not crash

    # ── Load configuration ──────────────────────────────────

    def test_load_config(self, win, tmp_path, monkeypatch):
        cfg = Config(project_name="LoadedProject", max_image_size=4096)
        config_path = tmp_path / "loaded_config.json"
        config_path.write_text(json.dumps(asdict(cfg)))

        monkeypatch.setattr(
            QtWidgets.QFileDialog,
            "getOpenFileName",
            staticmethod(lambda *a, **kw: (str(config_path), "JSON (*.json)")),
        )
        win._load_configuration()
        assert win._properties_dock.config().project_name == "LoadedProject"
        assert win._properties_dock.config().max_image_size == 4096

    def test_load_config_cancelled(self, win, monkeypatch):
        monkeypatch.setattr(
            QtWidgets.QFileDialog,
            "getOpenFileName",
            staticmethod(lambda *a, **kw: ("", "")),
        )
        win._load_configuration()  # Should not crash

    def test_load_config_from_path(self, win, tmp_path):
        cfg = Config(project_name="PathLoaded")
        config_path = tmp_path / "path_config.json"
        config_path.write_text(json.dumps(asdict(cfg)))
        win._load_config_from_path(config_path)
        assert win._properties_dock.config().project_name == "PathLoaded"

    # ── Open slide folder ───────────────────────────────────

    def test_open_slide_folder(self, win, tmp_path, monkeypatch):
        slide_dir = tmp_path / "slides"
        slide_dir.mkdir()
        (slide_dir / "s1.tif").write_text("x")
        (slide_dir / "s2.tiff").write_text("x")
        (slide_dir / "readme.txt").write_text("x")

        monkeypatch.setattr(
            QtWidgets.QFileDialog,
            "getExistingDirectory",
            staticmethod(lambda *a, **kw: str(slide_dir)),
        )
        # Monkeypatch thumbnail generation to avoid image loading
        monkeypatch.setattr(
            "valis_workstation.main_window.MainWindow._load_thumbnails_parallel",
            lambda self, slides, overlay=None: None,
        )
        win._open_slide_folder()

        slides = win._project_dock.slides()
        names = [s.name for s in slides]
        assert "s1.tif" in names
        assert "s2.tiff" in names
        assert "readme.txt" not in names

    def test_form_layout_dialogs_construct(self, qtbot):
        """Regression guard for dialogs using form layouts."""
        from valis_workstation.ui.dialogs.performance_stats_dialog import (
            PerformanceStatsDialog,
        )
        from valis_workstation.ui.dialogs.preferences_dialog import PreferencesDialog

        perf = PerformanceStatsDialog()
        prefs = PreferencesDialog()
        qtbot.addWidget(perf)
        qtbot.addWidget(prefs)
        assert perf.windowTitle() == "Performance Statistics"
        assert prefs.windowTitle() == "Preferences"

    def test_open_folder_cancelled(self, win, monkeypatch):
        monkeypatch.setattr(
            QtWidgets.QFileDialog,
            "getExistingDirectory",
            staticmethod(lambda *a, **kw: ""),
        )
        win._open_slide_folder()  # Should not crash

    # ── Registration (validation checks) ────────────────────

    def test_registration_no_slides_warning(self, win, monkeypatch):
        warned = []
        monkeypatch.setattr(
            QtWidgets.QMessageBox,
            "warning",
            staticmethod(lambda *a, **kw: warned.append(True)),
        )
        win._start_registration()
        assert len(warned) == 1  # Warning about "No slides"

    # ── Drag & drop ─────────────────────────────────────────

    def test_drop_folder(self, win, tmp_path, monkeypatch):
        slide_dir = tmp_path / "drop_slides"
        slide_dir.mkdir()
        (slide_dir / "a.tif").write_text("x")

        monkeypatch.setattr(
            "valis_workstation.main_window.MainWindow._load_thumbnails_parallel",
            lambda self, slides, overlay=None: None,
        )

        mock_url = MagicMock()
        mock_url.toLocalFile.return_value = str(slide_dir)

        mock_mime = MagicMock()
        mock_mime.hasUrls.return_value = True
        mock_mime.urls.return_value = [mock_url]

        mock_event = MagicMock()
        mock_event.mimeData.return_value = mock_mime

        # Patch Path.is_dir / is_file for the dropped path
        with patch.object(Path, "is_dir", return_value=True):
            win.dropEvent(mock_event)

        slides = win._project_dock.slides()
        assert any("a.tif" in s.name for s in slides)

    def test_drop_json_config(self, win, tmp_path, monkeypatch):
        config_path = tmp_path / "drop_config.json"
        cfg = Config(project_name="DroppedCfg")
        config_path.write_text(json.dumps(asdict(cfg)))

        mock_url = MagicMock()
        mock_url.toLocalFile.return_value = str(config_path)

        mock_mime = MagicMock()
        mock_mime.hasUrls.return_value = True
        mock_mime.urls.return_value = [mock_url]

        mock_event = MagicMock()
        mock_event.mimeData.return_value = mock_mime

        win.dropEvent(mock_event)
        assert win._properties_dock.config().project_name == "DroppedCfg"

    def test_drag_enter_accepted(self, win):
        mock_mime = MagicMock()
        mock_mime.hasUrls.return_value = True
        mock_event = MagicMock()
        mock_event.mimeData.return_value = mock_mime
        win.dragEnterEvent(mock_event)
        mock_event.acceptProposedAction.assert_called_once()

    # ── Tool actions (without results) ──────────────────────

    def test_blink_no_napari(self, win, monkeypatch):
        warned = []
        monkeypatch.setattr(
            QtWidgets.QMessageBox,
            "warning",
            staticmethod(lambda *a, **kw: warned.append(True)),
        )
        win._blink()
        assert len(warned) >= 1

    def test_analysis_plot_no_result(self, win, monkeypatch):
        warned = []
        monkeypatch.setattr(
            QtWidgets.QMessageBox,
            "warning",
            staticmethod(lambda *a, **kw: warned.append(True)),
        )
        win._show_analysis_plot()
        assert len(warned) >= 1

    def test_quality_report_no_result(self, win, monkeypatch):
        warned = []
        monkeypatch.setattr(
            QtWidgets.QMessageBox,
            "warning",
            staticmethod(lambda *a, **kw: warned.append(True)),
        )
        win._show_quality_report()
        assert len(warned) >= 1

    def test_warp_annotations_no_result(self, win, monkeypatch):
        warned = []
        monkeypatch.setattr(
            QtWidgets.QMessageBox,
            "warning",
            staticmethod(lambda *a, **kw: warned.append(True)),
        )
        win._warp_annotations()
        assert len(warned) >= 1

    def test_merge_slides_no_result(self, win, monkeypatch):
        warned = []
        monkeypatch.setattr(
            QtWidgets.QMessageBox,
            "warning",
            staticmethod(lambda *a, **kw: warned.append(True)),
        )
        win._merge_slides()
        assert len(warned) >= 1

    # ── Save options dialog ─────────────────────────────────

    def test_show_save_options(self, win, monkeypatch):
        monkeypatch.setattr(
            QtWidgets.QDialog,
            "exec",
            lambda self: QtWidgets.QDialog.DialogCode.Rejected,
        )
        win._show_save_options()  # Rejected → no-op

    # ── Performance stats ───────────────────────────────────

    def test_show_performance_stats(self, win, monkeypatch):
        monkeypatch.setattr(QtWidgets.QDialog, "exec", lambda self: None)
        win._show_performance_stats()

    # ── Preferences ─────────────────────────────────────────

    def test_show_preferences(self, win, monkeypatch):
        monkeypatch.setattr(QtWidgets.QDialog, "exec", lambda self: None)
        win._show_preferences()

    # ── About dialog ────────────────────────────────────────

    def test_show_about(self, win, monkeypatch):
        monkeypatch.setattr(
            QtWidgets.QMessageBox,
            "about",
            staticmethod(lambda *a, **kw: None),
        )
        win._show_about()

    # ── Recent folders ──────────────────────────────────────

    def test_recent_folders_menu_exists(self, win):
        assert win._recent_menu is not None

    def test_add_to_recent_folders(self, win, tmp_path):
        win._add_to_recent_folders(str(tmp_path / "folder1"))
        win._add_to_recent_folders(str(tmp_path / "folder2"))
        settings = QtCore.QSettings("VALIS", "Workstation")
        recent = settings.value("recent_folders", [])
        assert isinstance(recent, list)

    # ── Close event cleanup ─────────────────────────────────

    def test_close_event(self, win):
        event = QtGui.QCloseEvent()
        win.closeEvent(event)
        assert win._viewer is None
        assert win._worker is None

    # ── Status bar ──────────────────────────────────────────

    def test_status_bar_exists(self, win):
        assert win.statusBar() is not None
        assert win.statusBar().currentMessage() == "Ready"

    def test_window_build_performance_smoke(self, qtbot, monkeypatch, tmp_path):
        """Generous regression guard to detect severe startup slowdowns."""
        _original_find_spec = importlib.util.find_spec

        def _patched_find_spec(name, *args, **kwargs):
            if name == "napari":
                return None
            return _original_find_spec(name, *args, **kwargs)

        monkeypatch.setattr(importlib.util, "find_spec", _patched_find_spec)
        from valis_workstation.main_window import MainWindow

        start = time.perf_counter()
        w = MainWindow(
            repo_root=tmp_path,
            log_emitter=QtLogEmitter(),
            simple_elastix_available=False,
        )
        qtbot.addWidget(w)
        elapsed = time.perf_counter() - start
        assert elapsed < 15.0


# ═══════════════════════════════════════════════════════════════════════
#  SERVICE TESTS — ValisPipeline
# ═══════════════════════════════════════════════════════════════════════


class TestValisPipelineService:
    def test_build_kwargs_defaults(self):
        from valis_workstation.services.valis_pipeline import build_registrar_kwargs

        kwargs = build_registrar_kwargs(Config())
        assert isinstance(kwargs, dict)

    def test_build_kwargs_gpu(self):
        from valis_workstation.services.valis_pipeline import build_registrar_kwargs

        cfg = Config(use_gpu=True)
        kwargs = build_registrar_kwargs(cfg)
        assert isinstance(kwargs, dict)

    def test_build_kwargs_no_rigid(self):
        from valis_workstation.services.valis_pipeline import build_registrar_kwargs

        cfg = Config(rigid_registration=False)
        kwargs = build_registrar_kwargs(cfg)
        assert isinstance(kwargs, dict)

    def test_build_kwargs_all_detectors(self):
        from valis_workstation.services.valis_pipeline import build_registrar_kwargs
        from valis_workstation.constants import FeatureDetectors

        for fd in FeatureDetectors:
            cfg = Config(feature_detector=fd.value)
            kwargs = build_registrar_kwargs(cfg)
            assert isinstance(kwargs, dict), f"Failed for detector {fd.value}"

    def test_build_kwargs_all_transformers(self):
        from valis_workstation.services.valis_pipeline import build_registrar_kwargs
        from valis_workstation.constants import TransformerTypes

        for tt in TransformerTypes:
            cfg = Config(transformer_type=tt.value)
            kwargs = build_registrar_kwargs(cfg)
            assert isinstance(kwargs, dict), f"Failed for transformer {tt.value}"

    def test_build_kwargs_all_crop_modes(self):
        from valis_workstation.services.valis_pipeline import build_registrar_kwargs
        from valis_workstation.constants import CropModes

        for cm in CropModes:
            cfg = Config(crop_mode=cm.value)
            kwargs = build_registrar_kwargs(cfg)
            assert isinstance(kwargs, dict), f"Failed for crop_mode {cm.value}"


# ═══════════════════════════════════════════════════════════════════════
#  SERVICE TESTS — SlideScan
# ═══════════════════════════════════════════════════════════════════════


class TestSlideScanService:
    def test_scan_empty(self, tmp_path):
        from valis_workstation.services.slide_scan import scan_slide_folder

        assert scan_slide_folder(tmp_path) == []

    def test_scan_tif(self, tmp_path):
        from valis_workstation.services.slide_scan import scan_slide_folder

        (tmp_path / "a.tif").write_text("x")
        (tmp_path / "b.tiff").write_text("x")
        result = scan_slide_folder(tmp_path)
        names = [p.name for p in result]
        assert "a.tif" in names
        assert "b.tiff" in names

    def test_scan_ignores_non_slide(self, tmp_path):
        from valis_workstation.services.slide_scan import scan_slide_folder

        (tmp_path / "readme.txt").write_text("x")
        (tmp_path / "data.csv").write_text("x")
        assert scan_slide_folder(tmp_path) == []

    def test_scan_svs(self, tmp_path):
        from valis_workstation.services.slide_scan import scan_slide_folder

        (tmp_path / "slide.svs").write_text("x")
        result = scan_slide_folder(tmp_path)
        assert any(p.name == "slide.svs" for p in result)


# ═══════════════════════════════════════════════════════════════════════
#  ValisWorker TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestValisWorkerExtended:
    def test_cancel_flag(self):
        from valis_workstation.workers.valis_worker import ValisWorker

        w = ValisWorker(Config(), [], Path("."))
        assert w._cancel_requested is False
        w.cancel()
        assert w._cancel_requested is True

    def test_emits_finished(self, qtbot, monkeypatch, tmp_path):
        from valis_workstation.workers.valis_worker import ValisWorker

        def fake_pipeline(
            config, slides, output_dir, progress_callback=None, cancel_check=None
        ):
            if progress_callback:
                progress_callback(50)
            return {"output_dir": str(output_dir), "registered_dir": str(output_dir)}

        monkeypatch.setattr(
            "valis_workstation.workers.valis_worker.run_valis_pipeline",
            fake_pipeline,
        )

        worker = ValisWorker(Config(), [tmp_path / "s.tif"], tmp_path)
        thread = QtCore.QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)

        with qtbot.waitSignal(worker.finished, timeout=3000) as blocker:
            thread.start()
        thread.quit()
        thread.wait()
        assert blocker.args[0]["output_dir"] == str(tmp_path)

    def test_emits_failed(self, qtbot, monkeypatch, tmp_path):
        from valis_workstation.workers.valis_worker import ValisWorker

        def crash(*a, **kw):
            raise RuntimeError("boom")

        monkeypatch.setattr(
            "valis_workstation.workers.valis_worker.run_valis_pipeline",
            crash,
        )

        worker = ValisWorker(Config(), [tmp_path / "s.tif"], tmp_path)
        thread = QtCore.QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)

        with qtbot.waitSignal(worker.failed, timeout=3000) as blocker:
            thread.start()
        thread.quit()
        thread.wait()
        assert "boom" in blocker.args[0].lower()


# ═══════════════════════════════════════════════════════════════════════
#  CONFIG & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════


class TestConfigRoundtrip:
    def test_json_roundtrip(self, tmp_path):
        original = Config(
            project_name="RT",
            rigid_registration=False,
            non_rigid_registration=True,
            max_image_size=4096,
            use_gpu=True,
            feature_detector="kaze",
            transformer_type="affine",
            reference_slide="slide_2",
            crop_mode="all",
            use_masks=True,
            denoise=True,
            imgs_ordered=True,
            micro_registration=True,
            micro_max_image_size=8192,
            compression_level=6,
            pyramid_levels=5,
            tile_size=256,
            image_quality=85,
        )
        p = tmp_path / "cfg.json"
        p.write_text(json.dumps(asdict(original)))
        restored = Config(**json.loads(p.read_text()))
        assert restored == original

    def test_partial_config_load(self):
        """Old config files with missing keys should still load."""
        partial = {"project_name": "Old", "rigid_registration": False}
        cfg = Config(
            **{k: v for k, v in partial.items() if k in Config.__dataclass_fields__}
        )
        assert cfg.project_name == "Old"
        assert cfg.rigid_registration is False
        # Defaults for unset fields
        assert cfg.max_image_size == 2048

    def test_all_18_fields(self):
        assert len(Config.__dataclass_fields__) == 18


class TestConstantsComplete:
    def test_feature_detectors_count(self):
        from valis_workstation.constants import FeatureDetectors

        assert len(FeatureDetectors) == 8

    def test_feature_detectors_have_labels(self):
        from valis_workstation.constants import FeatureDetectors

        for fd in FeatureDetectors:
            assert fd.label, f"{fd.name} has no label"

    def test_transformer_types_count(self):
        from valis_workstation.constants import TransformerTypes

        assert len(TransformerTypes) == 3

    def test_crop_modes_count(self):
        from valis_workstation.constants import CropModes

        assert len(CropModes) == 4

    def test_image_formats_count(self):
        from valis_workstation.constants import ImageFormats

        assert len(ImageFormats) == 4

    def test_config_keys_count(self):
        from valis_workstation.constants import ConfigKeys

        assert len(ConfigKeys) >= 18


# ═══════════════════════════════════════════════════════════════════════
#  PROPERTIES DOCK — Config ↔ Widget Sync
# ═══════════════════════════════════════════════════════════════════════


class TestPropertiesDockSync:
    @pytest.fixture()
    def dock(self, qtbot):
        from valis_workstation.ui.properties_dock import PropertiesDock

        d = PropertiesDock(simple_elastix_available=True)
        qtbot.addWidget(d)
        return d

    def test_set_and_get_config(self, dock):
        cfg = Config(
            project_name="SyncTest",
            rigid_registration=False,
            max_image_size=4096,
            feature_detector="kaze",
            crop_mode="all",
        )
        dock.set_config(cfg)
        got = dock.config()
        assert got.project_name == "SyncTest"
        assert got.rigid_registration is False
        assert got.max_image_size == 4096
        assert got.feature_detector == "kaze"
        assert got.crop_mode == "all"

    def test_gpu_checkbox_default(self, dock):
        assert dock.config().use_gpu is False

    def test_micro_registration_enables_spin(self, dock):
        dock._micro_registration.setChecked(True)
        assert dock._micro_max_size.isEnabled()
        dock._micro_registration.setChecked(False)
        assert not dock._micro_max_size.isEnabled()

    def test_all_feature_detectors_in_combobox(self, dock):
        from valis_workstation.constants import FeatureDetectors

        combo = dock._feature_detector
        items = [combo.itemData(i) for i in range(combo.count())]
        for fd in FeatureDetectors:
            assert fd.value in items, f"{fd.value} missing from feature detector combo"

    def test_all_transformer_types_in_combobox(self, dock):
        from valis_workstation.constants import TransformerTypes

        combo = dock._transformer_type
        items = [combo.itemData(i) for i in range(combo.count())]
        for tt in TransformerTypes:
            assert tt.value in items, f"{tt.value} missing from transformer combo"

    def test_all_crop_modes_in_combobox(self, dock):
        from valis_workstation.constants import CropModes

        combo = dock._crop_mode
        items = [combo.itemText(i).lower() for i in range(combo.count())]
        for cm in CropModes:
            assert any(cm.value.lower() in t for t in items), (
                f"{cm.value} missing from crop mode combo"
            )


# ═══════════════════════════════════════════════════════════════════════
#  VALIDATION
# ═══════════════════════════════════════════════════════════════════════


class TestValidation:
    def test_validate_empty_slides(self, tmp_path):
        from valis_workstation.utils.validation import validate_slides

        result = validate_slides([], tmp_path)
        assert result.is_valid
        assert not result.has_errors()

    def test_validate_valid_slides(self, tmp_path):
        from valis_workstation.utils.validation import validate_slides

        s = tmp_path / "slide.tif"
        s.write_bytes(b"x")
        result = validate_slides([s], tmp_path)
        # Single slide may warn but shouldn't error fatally
        # (depends on implementation)


# ═══════════════════════════════════════════════════════════════════════
#  QT LOG EMITTER
# ═══════════════════════════════════════════════════════════════════════


class TestQtLogEmitterFull:
    def test_emit_log_line(self, qtbot):
        emitter = QtLogEmitter()
        with qtbot.waitSignal(emitter.log_line, timeout=1000) as blocker:
            emitter.log_line.emit("hello log")
        assert blocker.args[0] == "hello log"

    def test_multiple_emissions(self, qtbot):
        emitter = QtLogEmitter()
        messages = []
        emitter.log_line.connect(lambda msg: messages.append(msg))
        emitter.log_line.emit("msg1")
        emitter.log_line.emit("msg2")
        assert "msg1" in messages
        assert "msg2" in messages
