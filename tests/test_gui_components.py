"""Tests for Qt/GUI components that don't require napari."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets

from valis_workstation.models.config import Config
from valis_workstation.utils.qt_logging import QtLogEmitter, QtSignalHandler


# ---------- PropertiesDock ----------
class TestPropertiesDock:
    @pytest.fixture()
    def dock(self, qtbot):
        from valis_workstation.ui.properties_dock import PropertiesDock
        d = PropertiesDock(simple_elastix_available=True)
        qtbot.addWidget(d)
        return d

    def test_default_config(self, dock) -> None:
        c = dock.config()
        assert isinstance(c, Config)
        assert c.project_name == "New Project"
        assert c.rigid_registration is True
        assert c.non_rigid_registration is True

    def test_set_project_name(self, dock) -> None:
        dock._project_name.setText("MyProject")
        c = dock.config()
        assert c.project_name == "MyProject"

    def test_invalid_project_name_sanitised(self, dock) -> None:
        dock._project_name.setText('Bad<>Name')
        c = dock.config()
        assert "<" not in c.project_name
        assert ">" not in c.project_name

    def test_simple_elastix_unavailable_disables_non_rigid(self, qtbot) -> None:
        from valis_workstation.ui.properties_dock import PropertiesDock
        d = PropertiesDock(simple_elastix_available=False)
        qtbot.addWidget(d)
        assert not d._non_rigid.isEnabled()
        assert not d._non_rigid.isChecked()

    def test_advanced_settings_returned(self, dock) -> None:
        # Select by data key, not label text
        idx = dock._feature_detector.findData("kaze")
        dock._feature_detector.setCurrentIndex(idx)
        dock._crop_mode.setCurrentText("all")
        dock._use_masks.setChecked(True)
        c = dock.config()
        assert c.feature_detector == "kaze"
        assert c.crop_mode == "all"
        assert c.use_masks is True

    def test_reference_slide_auto(self, dock) -> None:
        c = dock.config()
        assert c.reference_slide is None

    def test_update_reference_slide_list(self, dock) -> None:
        dock.update_reference_slide_list(["Slide_A", "Slide_B"])
        assert dock._reference_slide.count() == 3  # Auto-detect + 2

    def test_micro_registration_toggle(self, dock) -> None:
        dock._micro_registration.setChecked(True)
        assert dock._micro_max_size.isEnabled()
        dock._micro_registration.setChecked(False)
        assert not dock._micro_max_size.isEnabled()

    def test_form_layout_visible(self, dock) -> None:
        """The basic settings form must be added to the layout (regression test)."""
        # Find the QFormLayout in the dock's widget
        container = dock.widget()
        layout = container.layout()
        found_form = False
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.layout() and isinstance(item.layout(), QtWidgets.QFormLayout):
                found_form = True
                break
        assert found_form, "QFormLayout not found in Properties dock layout"


# ---------- ProjectDock ----------
class TestProjectDock:
    @pytest.fixture()
    def dock(self, qtbot):
        from valis_workstation.ui.project_dock import ProjectDock
        d = ProjectDock()
        qtbot.addWidget(d)
        return d

    def test_initial_empty(self, dock) -> None:
        assert dock.slides() == []

    def test_set_slides(self, dock, tmp_path: Path) -> None:
        f1 = tmp_path / "a.tif"
        f2 = tmp_path / "b.tif"
        f1.write_text("a")
        f2.write_text("b")
        dock.set_slides([f1, f2])
        assert len(dock.slides()) == 2


# ---------- StatusDock ----------
class TestStatusDock:
    @pytest.fixture()
    def dock(self, qtbot):
        from valis_workstation.ui.status_dock import StatusDock
        emitter = QtLogEmitter()
        d = StatusDock(emitter)
        qtbot.addWidget(d)
        return d

    def test_set_progress(self, dock) -> None:
        dock.set_progress(50)
        # Should not crash

    def test_show_cancel_button(self, dock) -> None:
        dock.show_cancel_button(True)
        dock.show_cancel_button(False)


# ---------- QtLogEmitter ----------
class TestQtLogEmitter:
    def test_emit_signal(self, qtbot) -> None:
        emitter = QtLogEmitter()
        with qtbot.waitSignal(emitter.log_line, timeout=1000) as blocker:
            emitter.log_line.emit("test message")
        assert blocker.args[0] == "test message"


# ---------- WarpAnnotationsDialog ----------
class TestWarpAnnotationsDialog:
    def test_no_duplicate_init(self) -> None:
        """Regression test: WarpAnnotationsDialog must not have a bare __init__(parent)."""
        from valis_workstation.ui.dialogs.warp_annotations import WarpAnnotationsDialog
        import inspect
        sig = inspect.signature(WarpAnnotationsDialog.__init__)
        params = list(sig.parameters.keys())
        assert "registrar" in params, \
            "WarpAnnotationsDialog.__init__ should require 'registrar' parameter"


# ---------- LayerControlsDock visibility toggle ----------
class TestLayerToggle:
    def test_toggle_visible_checked_value(self) -> None:
        """Regression: _toggle_visible must compare with .value for Qt6 int emission."""
        from valis_workstation.ui.layer_controls_dock import LayerControlsDock

        mock_layer = MagicMock()
        # Qt6 stateChanged emits the int value of CheckState.Checked (== 2)
        LayerControlsDock._toggle_visible(mock_layer, 2)
        assert mock_layer.visible is True

        LayerControlsDock._toggle_visible(mock_layer, 0)
        assert mock_layer.visible is False


# ---------- SaveOptionsDialog ----------
class TestSaveOptionsDialog:
    def test_dialog_opens(self, qtbot) -> None:
        from valis_workstation.ui.dialogs.save_options_dialog import SaveOptionsDialog
        d = SaveOptionsDialog()
        qtbot.addWidget(d)
        opts = d.get_options()
        assert isinstance(opts, dict)
        assert "format" in opts or "pyramid_levels" in opts or "compression" in opts


# ---------- MergeSlidesDialog ----------
class TestMergeSlidesDialog:
    def test_dialog_opens(self, qtbot) -> None:
        from valis_workstation.ui.dialogs.merge_slides_dialog import MergeSlidesDialog
        slides = ["Slide_A", "Slide_B", "Slide_C"]
        d = MergeSlidesDialog(slides)
        qtbot.addWidget(d)
        config = d.get_merge_config()
        assert isinstance(config, dict)


# ---------- Config save/load roundtrip ----------
class TestConfigSaveLoad:
    def test_full_config_roundtrip(self, tmp_path: Path) -> None:
        """All Config fields must survive a save/load cycle."""
        from dataclasses import asdict
        original = Config(
            project_name="TestProject",
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
        config_path = tmp_path / "config.json"
        d = asdict(original)
        config_path.write_text(json.dumps(d, indent=2))

        loaded = json.loads(config_path.read_text())
        restored = Config(**loaded)
        assert restored == original
