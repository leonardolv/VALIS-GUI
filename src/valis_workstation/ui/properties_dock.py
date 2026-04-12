from __future__ import annotations

import dataclasses
import json
import logging
import re

from PySide6 import QtCore, QtWidgets

from valis_workstation.constants import CropModes, FeatureDetectors, TransformerTypes
from valis_workstation.layout_constants import GRID_SPACING
from valis_workstation.models.config import Config
from valis_workstation.ui.icons import load_icon

logger = logging.getLogger(__name__)

SIMPLE_ELASTIX_BANNER = (
    "SimpleElastix not found. Only Rigid Registration is available. "
    "Please install SimpleElastix for full functionality."
)


class PropertiesDock(QtWidgets.QDockWidget):
    def __init__(
        self, simple_elastix_available: bool, parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__("Properties", parent)
        self.setObjectName("PropertiesDock")
        self._simple_elastix_available = simple_elastix_available

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(
            GRID_SPACING, GRID_SPACING, GRID_SPACING, GRID_SPACING
        )
        layout.setSpacing(GRID_SPACING)

        self._banner = QtWidgets.QLabel()
        self._banner.setWordWrap(True)
        self._banner.setStyleSheet("color: #ffcc66; font-weight: bold;")
        layout.addWidget(self._banner)

        # ── Presets ──────────────────────────────────────────────────
        presets_header = QtWidgets.QLabel("Presets")
        presets_header.setProperty("role", "sidebar-header")
        layout.addWidget(presets_header)

        preset_row = QtWidgets.QHBoxLayout()
        preset_row.setSpacing(GRID_SPACING)
        preset_row.addWidget(QtWidgets.QLabel("Preset"))
        self._preset_combo = QtWidgets.QComboBox()
        self._preset_combo.setToolTip("Load a saved registration preset")
        preset_row.addWidget(self._preset_combo, 1)

        self._save_preset_btn = QtWidgets.QPushButton("Save")
        self._save_preset_btn.setIcon(
            load_icon("save", self, QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton)
        )
        self._save_preset_btn.setProperty("panelAction", True)
        self._save_preset_btn.clicked.connect(self._save_current_preset)
        preset_row.addWidget(self._save_preset_btn)

        self._load_preset_btn = QtWidgets.QPushButton("Load")
        self._load_preset_btn.setIcon(
            load_icon("open", self, QtWidgets.QStyle.StandardPixmap.SP_DialogOpenButton)
        )
        self._load_preset_btn.setProperty("panelAction", True)
        self._load_preset_btn.clicked.connect(self._load_selected_preset)
        preset_row.addWidget(self._load_preset_btn)

        self._delete_preset_btn = QtWidgets.QPushButton("Delete")
        self._delete_preset_btn.setIcon(
            load_icon("trash", self, QtWidgets.QStyle.StandardPixmap.SP_TrashIcon)
        )
        self._delete_preset_btn.setProperty("panelAction", True)
        self._delete_preset_btn.clicked.connect(self._delete_selected_preset)
        preset_row.addWidget(self._delete_preset_btn)
        layout.addLayout(preset_row)

        # ── Basic settings ──────────────────────────────────────────
        registration_header = QtWidgets.QLabel("Registration")
        registration_header.setProperty("role", "sidebar-header")
        layout.addWidget(registration_header)

        form = QtWidgets.QFormLayout()
        form.setHorizontalSpacing(GRID_SPACING)
        form.setVerticalSpacing(max(4, GRID_SPACING - 1))
        form.setFieldGrowthPolicy(
            QtWidgets.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )

        self._project_name = QtWidgets.QLineEdit("New Project")
        self._project_name.setToolTip(
            "Name for the registration project.\n"
            "Results will be saved in output/<project_name>/"
        )
        self._project_name.textChanged.connect(self._validate_project_name)

        self._rigid = QtWidgets.QCheckBox()
        self._rigid.setChecked(True)
        self._rigid.setToolTip(
            "Perform rigid (affine) registration to align slides.\n"
            "Recommended for all workflows."
        )

        self._non_rigid = QtWidgets.QCheckBox()
        self._non_rigid.setChecked(True)
        self._non_rigid.setToolTip(
            "Perform non-rigid (elastic) registration to correct tissue deformation.\n"
            "More accurate but slower than rigid only."
        )

        self._max_size = QtWidgets.QSpinBox()
        self._max_size.setRange(256, 16384)
        self._max_size.setValue(2048)
        self._max_size.setSuffix(" px")
        self._max_size.setToolTip(
            "Maximum image dimension (pixels) for processing.\n"
            "Larger = better accuracy but slower and more memory.\n"
            "Recommended: 2048 for quick tests, 4096+ for production."
        )

        self._use_gpu = QtWidgets.QCheckBox()
        self._use_gpu.setToolTip(
            "Enable GPU acceleration for deep-learning feature detectors\n"
            "(SuperPoint, DISK, DeDoDe).\n"
            "Requires CUDA-compatible GPU and PyTorch with CUDA support."
        )
        if not self._check_gpu_available():
            self._use_gpu.setEnabled(False)
            self._use_gpu.setChecked(False)
            self._use_gpu.setToolTip(
                "GPU acceleration not available.\n"
                "Requires CUDA-compatible GPU and PyTorch with CUDA."
            )
            logger.info("GPU not available – checkbox disabled")

        form.addRow("Project name", self._project_name)
        form.addRow("Rigid registration", self._rigid)
        form.addRow("Non-rigid registration", self._non_rigid)
        form.addRow("Max image size", self._max_size)
        form.addRow("Use GPU", self._use_gpu)
        layout.addLayout(form)

        # ── Advanced settings (collapsible) ─────────────────────────
        self._advanced_group = QtWidgets.QGroupBox("Advanced Settings")
        self._advanced_group.setCheckable(True)
        self._advanced_group.setChecked(False)
        self._advanced_group.setToolTip("Show / hide advanced registration options")

        adv = QtWidgets.QFormLayout()
        adv.setHorizontalSpacing(GRID_SPACING)
        adv.setVerticalSpacing(max(4, GRID_SPACING - 1))
        adv.setFieldGrowthPolicy(
            QtWidgets.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )

        # Feature detector – show human-readable labels
        self._feature_detector = QtWidgets.QComboBox()
        for key in FeatureDetectors.all():
            self._feature_detector.addItem(FeatureDetectors.label_for(key), key)
        self._feature_detector.setCurrentIndex(0)  # VGG
        self._feature_detector.setToolTip(
            "Feature detection algorithm used during rigid registration.\n"
            "VGG is the default and works well for most histology images.\n"
            "Deep-learning detectors (SuperPoint, DISK, DeDoDe) may give\n"
            "better results for challenging cases but require GPU."
        )

        # Rigid transformer – show labels, store keys
        self._transformer_type = QtWidgets.QComboBox()
        for key in TransformerTypes.all():
            self._transformer_type.addItem(TransformerTypes.label_for(key), key)
        self._transformer_type.setCurrentIndex(0)  # Similarity
        self._transformer_type.setToolTip(
            "Rigid transformation model:\n"
            "• Similarity (default): rotation + uniform scale + translation\n"
            "• Affine: rotation + scale + shear + translation\n"
            "• Rigid / Euclidean: rotation + translation only (no scale)"
        )

        # Reference slide
        self._reference_slide = QtWidgets.QComboBox()
        self._reference_slide.addItem("Auto-detect")
        self._reference_slide.setToolTip(
            "Reference slide for alignment.\n"
            "• Auto-detect: VALIS picks the middle image.\n"
            "• Manual: choose a specific slide after loading."
        )

        # Crop mode
        self._crop_mode = QtWidgets.QComboBox()
        self._crop_mode.addItems(CropModes.all())
        self._crop_mode.setCurrentText(CropModes.REFERENCE)
        self._crop_mode.setToolTip(
            "Output cropping mode:\n"
            "• reference – crop to reference slide bounds\n"
            "• all_overlap – crop to intersection of all slides\n"
            "• all – include all slide areas (union, no cropping)\n"
            "• unchanged – keep original slide dimensions"
        )

        # Tissue masks
        self._use_masks = QtWidgets.QCheckBox()
        self._use_masks.setToolTip(
            "Generate tissue masks and use them during registration.\n"
            "Improves accuracy by focusing on tissue regions."
        )

        # Denoise
        self._denoise = QtWidgets.QCheckBox()
        self._denoise.setToolTip(
            "Denoise processed images before rigid registration.\n"
            "Can improve feature detection in noisy images.\n"
            "Non-denoised images are still used for non-rigid registration."
        )

        # Auto-sort vs. ordered
        self._imgs_ordered = QtWidgets.QCheckBox()
        self._imgs_ordered.setToolTip(
            "Check if your slides are already in the correct z-stack order.\n"
            "If unchecked (default), VALIS will optimally sort images\n"
            "based on feature similarity before alignment."
        )

        # Micro-registration
        self._micro_registration = QtWidgets.QCheckBox()
        self._micro_registration.setToolTip(
            "Perform a high-resolution micro-registration pass.\n"
            "Refines alignment at finer resolution (slower but more precise)."
        )
        self._micro_max_size = QtWidgets.QSpinBox()
        self._micro_max_size.setRange(2048, 32768)
        self._micro_max_size.setValue(4096)
        self._micro_max_size.setSuffix(" px")
        self._micro_max_size.setEnabled(False)
        self._micro_max_size.setToolTip(
            "Maximum size for micro-registration.\n"
            "Higher = better precision but slower."
        )
        self._micro_registration.toggled.connect(self._micro_max_size.setEnabled)

        adv.addRow("Feature detector", self._feature_detector)
        adv.addRow("Rigid transform", self._transformer_type)
        adv.addRow("Reference slide", self._reference_slide)
        adv.addRow("Crop mode", self._crop_mode)
        adv.addRow("Use tissue masks", self._use_masks)
        adv.addRow("Denoise images", self._denoise)
        adv.addRow("Slides pre-ordered", self._imgs_ordered)
        adv.addRow("Micro-registration", self._micro_registration)
        adv.addRow("Micro max size", self._micro_max_size)

        self._advanced_group.setLayout(adv)
        layout.addWidget(self._advanced_group)

        # ── Output / save settings (collapsible) ────────────────────
        self._output_group = QtWidgets.QGroupBox("Output Settings")
        self._output_group.setCheckable(True)
        self._output_group.setChecked(False)
        self._output_group.setToolTip("Settings for saved registered images")

        out = QtWidgets.QFormLayout()
        out.setHorizontalSpacing(GRID_SPACING)
        out.setVerticalSpacing(max(4, GRID_SPACING - 1))
        out.setFieldGrowthPolicy(
            QtWidgets.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )

        self._output_profile = QtWidgets.QComboBox()
        self._output_profile.addItems(
            ["Custom", "WSI Archive", "Fast Review", "Publication"]
        )
        self._output_profile.setToolTip("Apply output templates for common workflows")
        self._output_profile.currentTextChanged.connect(self.apply_output_profile)

        self._compression_level_spin = QtWidgets.QSpinBox()
        self._compression_level_spin.setRange(0, 9)
        self._compression_level_spin.setValue(1)
        self._compression_level_spin.setToolTip(
            "TIFF compression level (0 = none, 9 = maximum).\n"
            "Higher compression = smaller files, slower saving."
        )

        self._pyramid_levels_spin = QtWidgets.QSpinBox()
        self._pyramid_levels_spin.setRange(0, 10)
        self._pyramid_levels_spin.setValue(4)
        self._pyramid_levels_spin.setToolTip(
            "Number of resolution pyramid levels.\n"
            "0 = no pyramid; 4 = default for OME-TIFF viewers.\n"
            "Pyramids enable fast multi-scale viewing."
        )

        self._tile_size_spin = QtWidgets.QSpinBox()
        self._tile_size_spin.setRange(128, 4096)
        self._tile_size_spin.setSingleStep(128)
        self._tile_size_spin.setValue(512)
        self._tile_size_spin.setSuffix(" px")
        self._tile_size_spin.setToolTip(
            "Tile width/height for tiled TIFF output.\n"
            "512 is a good default for most viewers."
        )

        self._image_quality_spin = QtWidgets.QSpinBox()
        self._image_quality_spin.setRange(1, 100)
        self._image_quality_spin.setValue(95)
        self._image_quality_spin.setSuffix(" %")
        self._image_quality_spin.setToolTip(
            "JPEG compression quality (1–100).\nOnly affects JPEG-compressed TIFFs."
        )

        out.addRow("Output profile", self._output_profile)
        out.addRow("Compression level", self._compression_level_spin)
        out.addRow("Pyramid levels", self._pyramid_levels_spin)
        out.addRow("Tile size", self._tile_size_spin)
        out.addRow("JPEG quality", self._image_quality_spin)

        self._output_group.setLayout(out)
        layout.addWidget(self._output_group)

        layout.addStretch(1)
        self.setWidget(container)

        self._applying_profile = False
        self._refresh_preset_list()
        self._apply_simple_elastix_state()

    # ── Helpers ─────────────────────────────────────────────────────

    def _apply_simple_elastix_state(self) -> None:
        if not self._simple_elastix_available:
            self._banner.setText(SIMPLE_ELASTIX_BANNER)
            self._non_rigid.setChecked(False)
            self._non_rigid.setEnabled(False)
        else:
            self._banner.setText("")

    def _preset_store_key(self) -> str:
        return "config_presets"

    def _get_presets(self) -> dict[str, dict]:
        settings = QtCore.QSettings("VALIS", "Workstation")
        raw = settings.value(self._preset_store_key(), "{}")
        if isinstance(raw, dict):
            return raw
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    def _set_presets(self, presets: dict[str, dict]) -> None:
        settings = QtCore.QSettings("VALIS", "Workstation")
        settings.setValue(self._preset_store_key(), json.dumps(presets))

    def _refresh_preset_list(self) -> None:
        current = self._preset_combo.currentText()
        self._preset_combo.clear()
        self._preset_combo.addItem("(Select preset)")
        for name in sorted(self._get_presets().keys()):
            self._preset_combo.addItem(name)
        idx = self._preset_combo.findText(current)
        self._preset_combo.setCurrentIndex(idx if idx >= 0 else 0)

    def _save_current_preset(self) -> None:
        name, ok = QtWidgets.QInputDialog.getText(self, "Save Preset", "Preset name")
        if not ok or not name.strip():
            return
        name = name.strip()
        cfg = self.config()
        presets = self._get_presets()
        presets[name] = dataclasses.asdict(cfg)
        self._set_presets(presets)
        self._refresh_preset_list()
        self._preset_combo.setCurrentText(name)
        logger.info("Saved preset '%s'", name)

    def _load_selected_preset(self) -> None:
        name = self._preset_combo.currentText()
        if not name or name == "(Select preset)":
            return
        preset = self._get_presets().get(name)
        if not preset:
            return
        cfg = Config(
            **{k: v for k, v in preset.items() if k in Config.__dataclass_fields__}
        )
        self.set_config(cfg)
        logger.info("Loaded preset '%s'", name)

    def _delete_selected_preset(self) -> None:
        name = self._preset_combo.currentText()
        if not name or name == "(Select preset)":
            return
        presets = self._get_presets()
        if name in presets:
            presets.pop(name)
            self._set_presets(presets)
            self._refresh_preset_list()
            logger.info("Deleted preset '%s'", name)

    def apply_output_profile(self, profile_name: str) -> None:
        """Apply output profile template values.

        Selecting `Custom` preserves user-entered values.
        """
        if self._applying_profile:
            return
        self._applying_profile = True
        try:
            templates = {
                "WSI Archive": {
                    "compression": 6,
                    "pyramid": 5,
                    "tile": 512,
                    "quality": 95,
                },
                "Fast Review": {
                    "compression": 2,
                    "pyramid": 3,
                    "tile": 256,
                    "quality": 85,
                },
                "Publication": {
                    "compression": 4,
                    "pyramid": 4,
                    "tile": 512,
                    "quality": 100,
                },
            }
            t = templates.get(profile_name)
            if t is None:
                return
            self._compression_level_spin.setValue(t["compression"])
            self._pyramid_levels_spin.setValue(t["pyramid"])
            self._tile_size_spin.setValue(t["tile"])
            self._image_quality_spin.setValue(t["quality"])
        finally:
            self._applying_profile = False

    def _check_gpu_available(self) -> bool:
        try:
            import torch

            available = torch.cuda.is_available()
            if available:
                logger.info("GPU detected: %s", torch.cuda.get_device_name(0))
            return available
        except ImportError:
            logger.debug("PyTorch not installed – GPU acceleration not available")
            return False
        except Exception as exc:
            logger.warning("Error checking GPU: %s", exc)
            return False

    def _validate_project_name(self, text: str) -> None:
        invalid_chars = r'[<>:"/\\|?*]'
        reserved_names = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            *(f"COM{i}" for i in range(1, 10)),
            *(f"LPT{i}" for i in range(1, 10)),
        }
        if not text.strip():
            self._project_name.setStyleSheet("QLineEdit { border: 1px solid orange; }")
            self._project_name.setToolTip("Project name cannot be empty")
        elif re.search(invalid_chars, text):
            self._project_name.setStyleSheet("QLineEdit { border: 2px solid red; }")
            self._project_name.setToolTip('Invalid characters: < > : " / \\ | ? *')
        elif text.strip().upper() in reserved_names:
            self._project_name.setStyleSheet("QLineEdit { border: 2px solid red; }")
            self._project_name.setToolTip(f"'{text}' is a reserved system name")
        else:
            self._project_name.setStyleSheet("")
            self._project_name.setToolTip(
                "Name for the registration project.\nResults → output/<project_name>/"
            )

    # ── Config read / write ─────────────────────────────────────────

    def config(self) -> Config:
        """Build a :class:`Config` from the current widget state."""
        # Sanitize project name
        project_name = re.sub(r'[<>:"/\\|?*]', "_", self._project_name.text().strip())
        if not project_name:
            project_name = "New Project"
        reserved = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            *(f"COM{i}" for i in range(1, 10)),
            *(f"LPT{i}" for i in range(1, 10)),
        }
        if project_name.upper() in reserved:
            project_name = f"{project_name}_project"

        # Reference slide (None ⇒ auto-detect)
        ref_slide = None
        if self._reference_slide.currentText() != "Auto-detect":
            ref_slide = self._reference_slide.currentText()

        return Config(
            # Basic
            project_name=project_name,
            rigid_registration=self._rigid.isChecked(),
            non_rigid_registration=self._non_rigid.isChecked(),
            max_image_size=int(self._max_size.value()),
            use_gpu=self._use_gpu.isChecked(),
            # Advanced
            feature_detector=self._feature_detector.currentData()
            or FeatureDetectors.VGG,
            transformer_type=self._transformer_type.currentData()
            or TransformerTypes.SIMILARITY,
            reference_slide=ref_slide,
            crop_mode=self._crop_mode.currentText(),
            use_masks=self._use_masks.isChecked(),
            denoise=self._denoise.isChecked(),
            imgs_ordered=self._imgs_ordered.isChecked(),
            # Micro-registration
            micro_registration=self._micro_registration.isChecked(),
            micro_max_image_size=int(self._micro_max_size.value()),
            # Output
            compression_level=int(self._compression_level_spin.value()),
            pyramid_levels=int(self._pyramid_levels_spin.value()),
            tile_size=int(self._tile_size_spin.value()),
            image_quality=int(self._image_quality_spin.value()),
        )

    def set_config(self, cfg: Config) -> None:
        """Populate all widgets from *cfg*."""
        self._project_name.setText(cfg.project_name)
        self._rigid.setChecked(cfg.rigid_registration)
        self._non_rigid.setChecked(cfg.non_rigid_registration)
        self._max_size.setValue(cfg.max_image_size)
        self._use_gpu.setChecked(cfg.use_gpu)

        # Feature detector — find by data key
        idx = self._feature_detector.findData(cfg.feature_detector)
        if idx >= 0:
            self._feature_detector.setCurrentIndex(idx)

        # Transformer
        idx = self._transformer_type.findData(cfg.transformer_type)
        if idx >= 0:
            self._transformer_type.setCurrentIndex(idx)

        # Reference slide
        if cfg.reference_slide:
            idx = self._reference_slide.findText(cfg.reference_slide)
            if idx >= 0:
                self._reference_slide.setCurrentIndex(idx)
        else:
            self._reference_slide.setCurrentIndex(0)  # Auto-detect

        self._crop_mode.setCurrentText(cfg.crop_mode)
        self._use_masks.setChecked(cfg.use_masks)
        self._denoise.setChecked(cfg.denoise)
        self._imgs_ordered.setChecked(cfg.imgs_ordered)
        self._micro_registration.setChecked(cfg.micro_registration)
        self._micro_max_size.setValue(cfg.micro_max_image_size)

        self._compression_level_spin.setValue(cfg.compression_level)
        self._pyramid_levels_spin.setValue(cfg.pyramid_levels)
        self._tile_size_spin.setValue(cfg.tile_size)
        self._image_quality_spin.setValue(cfg.image_quality)
        self._output_profile.setCurrentText("Custom")

    def update_reference_slide_list(self, slide_names: list[str]) -> None:
        """Update the reference-slide dropdown with available slide names."""
        current = self._reference_slide.currentText()
        self._reference_slide.clear()
        self._reference_slide.addItem("Auto-detect")
        self._reference_slide.addItems(slide_names)
        idx = self._reference_slide.findText(current)
        if idx >= 0:
            self._reference_slide.setCurrentIndex(idx)
