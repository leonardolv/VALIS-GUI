"""Tests for PropertiesDock accessibility, object names, public properties, and ergonomics helpers."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets
from valis_workstation.constants import FeatureDetectors, ImageFormats, NonRigidMethods, TransformerTypes
from valis_workstation.ui.properties_dock import PropertiesDock


class TestPropertiesDockAccessibilityAndErgonomics:
    def test_properties_dock_accessibility_and_properties(self, qtbot) -> None:
        dock = PropertiesDock(simple_elastix_available=True)
        qtbot.addWidget(dock)

        # Dock metadata
        assert dock.objectName() == "PropertiesDock"
        assert dock.accessibleName() == "Registration Properties Dock"
        assert len(dock.accessibleDescription()) > 0

        # Child controls object names and cursor affordances
        assert dock.preset_combo.objectName() == "presetCombo"
        assert dock.preset_combo.accessibleName() == "Registration Preset Selector"

        assert dock.save_preset_btn.objectName() == "savePresetBtn"
        assert dock.save_preset_btn.accessibleName() == "Save Registration Preset"
        assert dock.save_preset_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

        assert dock.load_preset_btn.objectName() == "loadPresetBtn"
        assert dock.load_preset_btn.accessibleName() == "Load Registration Preset"
        assert dock.load_preset_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

        assert dock.delete_preset_btn.objectName() == "deletePresetBtn"
        assert dock.delete_preset_btn.accessibleName() == "Delete Registration Preset"
        assert dock.delete_preset_btn.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

        assert dock.project_name_edit.objectName() == "projectNameEdit"
        assert dock.project_name_edit.accessibleName() == "Project Name"

        assert dock.rigid_check.objectName() == "rigidCheck"
        assert dock.rigid_check.accessibleName() == "Rigid Registration Toggle"
        assert dock.rigid_check.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

        assert dock.non_rigid_check.objectName() == "nonRigidCheck"
        assert dock.non_rigid_check.accessibleName() == "Non-Rigid Registration Toggle"
        assert dock.non_rigid_check.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

        assert dock.working_resolution_spin.objectName() == "maxSizeSpin"
        assert dock.working_resolution_spin.accessibleName() == "Working Resolution"

        assert dock.use_gpu_check.objectName() == "useGpuCheck"
        assert dock.use_gpu_check.accessibleName() == "Use GPU Acceleration Toggle"
        assert dock.use_gpu_check.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

        assert dock.feature_detector_combo.objectName() == "featureDetectorCombo"
        assert dock.feature_detector_combo.accessibleName() == "Feature Detector Algorithm"

        assert dock.transformer_type_combo.objectName() == "transformerTypeCombo"
        assert dock.transformer_type_combo.accessibleName() == "Rigid Transformation Model"

        assert dock.reference_slide_combo.objectName() == "referenceSlideCombo"
        assert dock.reference_slide_combo.accessibleName() == "Reference Slide Selection"

        assert dock.crop_mode_combo.objectName() == "cropModeCombo"
        assert dock.crop_mode_combo.accessibleName() == "Output Crop Mode"

        assert dock.use_masks_check.objectName() == "useMasksCheck"
        assert dock.use_masks_check.accessibleName() == "Use Tissue Masks Toggle"
        assert dock.use_masks_check.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

        assert dock.denoise_check.objectName() == "denoiseCheck"
        assert dock.denoise_check.accessibleName() == "Denoise Images Toggle"
        assert dock.denoise_check.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

        assert dock.imgs_ordered_check.objectName() == "imgsOrderedCheck"
        assert dock.imgs_ordered_check.accessibleName() == "Slides Already In Order Toggle"
        assert dock.imgs_ordered_check.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

        assert dock.crop_for_rigid_check.objectName() == "cropForRigidCheck"
        assert dock.crop_for_rigid_check.accessibleName() == "Pre-Crop Tissue Toggle"
        assert dock.crop_for_rigid_check.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

        assert dock.non_rigid_method_combo.objectName() == "nonRigidMethodCombo"
        assert dock.non_rigid_method_combo.accessibleName() == "Non-Rigid Deformation Method"

        assert dock.use_color_features_check.objectName() == "useColorFeaturesCheck"
        assert dock.use_color_features_check.accessibleName() == "Use Color Features Toggle"
        assert dock.use_color_features_check.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

        assert dock.micro_registration_check.objectName() == "microRegistrationCheck"
        assert dock.micro_registration_check.accessibleName() == "Micro-Registration Pass Toggle"
        assert dock.micro_registration_check.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

        assert dock.micro_max_size_spin.objectName() == "microMaxSizeSpin"
        assert dock.micro_max_size_spin.accessibleName() == "Micro-Registration Max Pixel Dimension"

        assert dock.output_profile_combo.objectName() == "outputProfileCombo"
        assert dock.output_profile_combo.accessibleName() == "Output Profile Template"

        assert dock.format_combo.objectName() == "formatCombo"
        assert dock.format_combo.accessibleName() == "Output Image Format"

        assert dock.write_pyramid_check.objectName() == "writePyramidCheck"
        assert dock.write_pyramid_check.accessibleName() == "Write Multi-Resolution Pyramid Toggle"
        assert dock.write_pyramid_check.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

        assert dock.compression_level_spin.objectName() == "compressionLevelSpin"
        assert dock.compression_level_spin.accessibleName() == "Compression Level"

        assert dock.pyramid_levels_spin.objectName() == "pyramidLevelsSpin"
        assert dock.pyramid_levels_spin.accessibleName() == "Output Pyramid Levels"

        assert dock.tile_size_spin.objectName() == "tileSizeSpin"
        assert dock.tile_size_spin.accessibleName() == "Output Tile Size"

        assert dock.image_quality_spin.objectName() == "imageQualitySpin"
        assert dock.image_quality_spin.accessibleName() == "JPEG Image Quality"

    def test_properties_dock_ergonomics_getters_and_setters(self, qtbot) -> None:
        dock = PropertiesDock(simple_elastix_available=True)
        qtbot.addWidget(dock)

        # Project name
        assert dock.project_name() == "New Project"
        dock.set_project_name("Cohort_Experiment_01")
        assert dock.project_name() == "Cohort_Experiment_01"

        # Rigid & non-rigid
        assert dock.is_rigid_enabled() is True
        dock.set_rigid_enabled(False)
        assert dock.is_rigid_enabled() is False
        dock.set_rigid_enabled(True)

        assert dock.is_non_rigid_enabled() is True
        dock.set_non_rigid_enabled(False)
        assert dock.is_non_rigid_enabled() is False
        dock.set_non_rigid_enabled(True)

        # Working resolution
        assert dock.working_resolution() == 2048
        dock.set_working_resolution(4096)
        assert dock.working_resolution() == 4096

        # GPU acceleration
        initial_gpu = dock.is_gpu_enabled()
        dock.set_gpu_enabled(not initial_gpu)
        assert dock.is_gpu_enabled() == (not initial_gpu)
        dock.set_gpu_enabled(initial_gpu)

        # Feature detector
        assert dock.feature_detector() == FeatureDetectors.VGG
        dock.set_feature_detector(FeatureDetectors.ORB)
        assert dock.feature_detector() == FeatureDetectors.ORB

        # Transformer type
        assert dock.transformer_type() == TransformerTypes.SIMILARITY
        dock.set_transformer_type(TransformerTypes.AFFINE)
        assert dock.transformer_type() == TransformerTypes.AFFINE

        # Crop mode
        assert dock.crop_mode() == "reference"
        dock.set_crop_mode("all")
        assert dock.crop_mode() == "all"

        # Reference slide
        assert dock.reference_slide() == "Auto-detect"
        dock.update_reference_slide_list(["slide_01.svs", "slide_02.svs"])
        dock.set_reference_slide("slide_02.svs")
        assert dock.reference_slide() == "slide_02.svs"

        # Toggles
        assert dock.is_use_masks_enabled() is False
        dock.set_use_masks_enabled(True)
        assert dock.is_use_masks_enabled() is True

        assert dock.is_denoise_enabled() is False
        dock.set_denoise_enabled(True)
        assert dock.is_denoise_enabled() is True

        assert dock.is_imgs_ordered_enabled() is False
        dock.set_imgs_ordered_enabled(True)
        assert dock.is_imgs_ordered_enabled() is True

        assert dock.is_crop_for_rigid_enabled() is True
        dock.set_crop_for_rigid_enabled(False)
        assert dock.is_crop_for_rigid_enabled() is False

        assert dock.is_color_features_enabled() is False
        dock.set_color_features_enabled(True)
        assert dock.is_color_features_enabled() is True

        # Non-rigid method
        assert dock.non_rigid_method() == NonRigidMethods.OPTICAL_FLOW
        dock.set_non_rigid_method(NonRigidMethods.RAFT)
        assert dock.non_rigid_method() == NonRigidMethods.RAFT

        # Micro-registration
        assert dock.is_micro_registration_enabled() is False
        dock.set_micro_registration_enabled(True)
        assert dock.is_micro_registration_enabled() is True

        assert dock.micro_resolution() == 4096
        dock.set_micro_resolution(8192)
        assert dock.micro_resolution() == 8192

        # Output format & profile
        assert dock.output_format() == ImageFormats.OME_TIFF
        dock.set_output_format(ImageFormats.PNG)
        assert dock.output_format() == ImageFormats.PNG

        assert dock.output_profile() == "Custom"
        dock.set_output_profile("Fast Review")
        assert dock.output_profile() == "Fast Review"
        assert dock.compression_level() == 2
        assert dock.pyramid_levels() == 3
        assert dock.tile_size() == 256
        assert dock.image_quality() == 85

        dock.set_compression_level(5)
        assert dock.compression_level() == 5

        dock.set_pyramid_levels(6)
        assert dock.pyramid_levels() == 6

        dock.set_tile_size(1024)
        assert dock.tile_size() == 1024

        dock.set_image_quality(90)
        assert dock.image_quality() == 90

        assert dock.is_write_pyramid_enabled() is True
        dock.set_write_pyramid_enabled(False)
        assert dock.is_write_pyramid_enabled() is False

    def test_properties_dock_preset_helpers_and_triggers(self, qtbot) -> None:
        dock = PropertiesDock(simple_elastix_available=True)
        qtbot.addWidget(dock)

        preset_name = "Automated_Test_Preset"
        # Ensure clean initial state
        dock.delete_preset(preset_name)

        # Save preset programmatically
        dock.set_project_name("TestPresetProject")
        dock.set_working_resolution(1024)
        dock.save_preset(preset_name)

        assert preset_name in dock.preset_names()
        assert dock.selected_preset_name() == preset_name

        # Modify values and restore via load_preset
        dock.set_working_resolution(8192)
        assert dock.working_resolution() == 8192

        assert dock.load_preset(preset_name) is True
        assert dock.working_resolution() == 1024

        # Programmatic select_preset
        assert dock.select_preset(preset_name) is True
        assert dock.selected_preset_name() == preset_name
        assert dock.select_preset("NonExistentPreset") is False

        # Delete preset programmatically
        assert dock.delete_preset(preset_name) is True
        assert preset_name not in dock.preset_names()

        # Action triggers (headless safe)
        dock.trigger_save_preset()
        assert "Default Preset" in dock.preset_names()
        dock.trigger_load_preset()
        dock.trigger_delete_preset()
        assert "Default Preset" not in dock.preset_names()
