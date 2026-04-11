# VALIS Workstation - GUI Application

[![CI](https://github.com/MathOnco/valis/workflows/CI/badge.svg?branch=main)](https://github.com/MathOnco/valis/actions?workflow=CI)
[![Documentation](https://readthedocs.org/projects/valis/badge/?version=latest)](https://valis.readthedocs.io/)
[![PyPI](https://badge.fury.io/py/valis-wsi.svg)](https://badge.fury.io/py/valis-wsi)

**A professional graphical user interface for VALIS - Virtual Alignment of pathoLogy Image Series**

![VALIS Workstation Banner](https://github.com/MathOnco/valis/raw/main/docs/_images/banner.gif)

---

## 🎯 What is VALIS Workstation?

VALIS Workstation is a modern, user-friendly GUI application built on top of the [VALIS](https://github.com/MathOnco/valis) registration library. It provides an intuitive interface for aligning whole slide images (WSI) with advanced visualization and quality assessment tools.

### ✨ Key Features

- 🖥️ **Modern Qt-based Interface** - Professional UI built with PySide6
- 🔬 **Napari Integration** - Interactive slide visualization with layer controls
- ⚡ **Automated Registration** - Rigid and non-rigid alignment with minimal user input
- 📊 **Quality Assessment Tools** - Built-in blink viewer, analysis plots, and quality reports
- 🎨 **Layer Management** - Control visibility, opacity, and colormaps
- 📝 **Annotation Warping** - Transfer annotations between aligned slides
- 🔄 **Real-time Progress** - Live logging and progress tracking
- 🧭 **Preflight Estimation** - Input size, output size, and runtime estimate before run
- 🧪 **Diagnostics Dialog** - Runtime/environment snapshot for troubleshooting
- 💾 **Config Presets** - Save/load/delete reusable registration configurations
- 📦 **Session Bundle Export** - ZIP export of run summary + logs for support/handoff
- 💾 **OME-TIFF Output** - Industry-standard format compatible with QuPath, ImageJ, HALO, etc.

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/leonardolv/VALIS-GUI.git
cd VALIS-GUI

# Install dependencies
pip install -r requirements.txt

# Run the application
python run_valis_workstation.py
```

### Basic Usage

1. **Open slides:** File → Open Slide Folder
2. **Configure:** Use Properties panel, presets, and output profiles (optional)
3. **Register:** File → Run Registration and confirm preflight summary
4. **Review:** Use Tools menu for comparison, reports, export bundle, etc.

**📖 [See Quick Start Guide](QUICK_START.md) for detailed walkthrough**

---

## 📋 Requirements

- **Python:** 3.9 or higher
- **Operating System:** Windows, macOS, or Linux
- **RAM:** 16GB minimum, 32GB+ recommended for large slides
- **Disk Space:** 2-3× the size of your input slides

### Dependencies

Core packages (automatically installed):
- `PySide6` - Qt GUI framework
- `napari[all]` - Image visualization
- `valis-wsi` - Registration library
- `matplotlib`, `pandas` - Data visualization
- `pytest`, `pytest-qt` - Testing

Optional:
- `SimpleElastix` - Required for non-rigid registration

---

## 🏗️ Architecture

The application follows a modular design:

```
VALIS-GUI/
├── run_valis_workstation.py    # Entry point
├── src/valis_workstation/
│   ├── app.py                  # Application lifecycle
│   ├── main_window.py          # Main UI window
│   ├── ui/                     # UI components
│   │   ├── project_dock.py
│   │   ├── properties_dock.py
│   │   ├── status_dock.py
│   │   ├── layer_controls_dock.py
│   │   └── dialogs/            # Dialog windows
│   ├── workers/                # Background tasks
│   ├── services/               # Business logic
│   │   ├── valis_pipeline.py
│   │   ├── slide_scan.py
│   │   └── error_metrics.py
│   ├── models/                 # Data structures
│   └── utils/                  # Utilities
│       ├── logging_config.py
│       └── qt_logging.py
├── tests/                      # Test suite
├── logs/                       # Application logs
└── output/                     # Registration results
```

---

## 🎨 User Interface

### Main Window

```
┌─────────────────────────────────────────────────────┐
│  File    Tools                          [Menu Bar]  │
├──────────┬────────────────────────┬─────────────────┤
│          │                        │                 │
│ Project  │   Napari Viewer        │  Properties    │
│  Dock    │   (Central Widget)     │    Dock        │
│          │                        │  ─────────────  │
│          │                        │  Layers Dock   │
│          │                        │   (Tabbed)     │
└──────────┴────────────────────────┴─────────────────┤
│              Status Dock                            │
│  [Progress Bar] [Log Console]                       │
└─────────────────────────────────────────────────────┘
```

### Panels

- **Project Dock:** Slide management and ordering (drag & drop to reorder)
- **Properties Dock:** Registration parameter configuration
- **Layers Dock:** Control layer visibility, opacity, and colormaps
- **Status Dock:** Progress monitoring and real-time logs
- **Napari Viewer:** Interactive slide visualization

---

## 🛠️ Features in Detail

### Registration Pipeline

VALIS Workstation implements the full VALIS pipeline:

1. **Slide Loading** - Supports 300+ formats via Bio-Formats and OpenSlide
2. **Preprocessing** - Automatic normalization and masking
3. **Feature Detection** - Advanced feature matching algorithms
4. **Rigid Registration** - Translation, rotation, and scaling
5. **Non-rigid Registration** (optional) - Local deformation correction
6. **Quality Assessment** - Error metrics and validation
7. **Output Generation** - OME-TIFF registered slides

### Tools Menu

#### Blink Viewer
- Rapidly toggle between registered slides
- Adjustable blend opacity
- Automatic blinking mode
- Mode selector: Blink, Side-by-side, Swipe
- Perfect for detecting misalignments

#### Analysis Plot
- Visualize registration error metrics
- Plot TRE (Target Registration Error) per slide pair
- Identify problematic registrations

#### Quality Report
- Detailed table of registration metrics
- Sortable columns
- Export capabilities

#### Warp Annotations
- Transfer ROIs and annotations between slides
- JSON-based annotation format
- Supports polygons, points, and complex shapes

### Layer Controls

- **Search:** Filter layers by name
- **Lock edits:** Prevent accidental value changes
- **Solo selected:** Show only the selected layer
- **Reset opacity:** Return all layers to full opacity
- **Visibility:** Toggle layers on/off
- **Opacity:** Blend multiple layers (0-100%)
- **Colormaps:** False-color overlays (gray, viridis, red, green, blue, etc.)
- **Auto-refresh:** Updates when layers change

### Configuration and Session Tools

- **Presets:** Save/load/delete named parameter sets in the Properties panel
- **Output profiles:** `Custom`, `WSI Archive`, `Fast Review`, `Publication`
- **Resume Last Registration:** Restart from prior run context in one action
- **Recent folder + config linking:** Reopen known data+config pairs quickly
- **Session bundle export:** Capture config, summary metadata, and logs to ZIP
- **Diagnostics:** Open Help -> Diagnostics for environment/runtime summary

---

## 📊 Output Files

Registration results are saved to `output/<project_name>/`:

```
output/MyProject/
├── registered/                 # Registered slides (OME-TIFF)
│   ├── slide_001.ome.tiff
│   ├── slide_002.ome.tiff
│   └── ...
├── summary.csv                 # Registration metrics
└── transforms/                 # Transformation data
    ├── slide_001_rigid.npy
    └── slide_001_nonrigid.npy
```

---

## 🧪 Testing

Run the test suite:

```bash
pytest tests/
```

Test coverage includes:
- ✅ Slide scanning and filtering
- ✅ Configuration mapping
- ✅ Logging system
- ✅ Worker signals
- ✅ GUI smoke tests (with guards for optional dependencies)

---

## 🔧 Configuration

### Registration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Project name | "New Project" | Output directory name |
| Rigid registration | ✓ | Enable rigid alignment |
| Non-rigid registration | ✓ | Enable non-rigid alignment (requires SimpleElastix) |
| Max image size | 2048 | Maximum dimension for processing (pixels) |
| Match threshold | 0.35 | Feature matching threshold (0.0-1.0) |
| Use GPU | ☐ | Enable GPU acceleration |

### Logging

Logs are written to `logs/valis_workstation.log`:
- **Console:** INFO level
- **File:** DEBUG level (rotating, 5 files × 5MB)
- **GUI Console:** INFO level

---

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "Napari not available" | `pip install --upgrade napari[all]` |
| "SimpleElastix not found" | Install SimpleElastix or use rigid-only mode |
| Out of memory | Reduce max image size parameter |
| Slow performance | Enable GPU or reduce image size |
| JVM initialization failed | Install Java JDK/JRE |

Tip: use **Help -> Diagnostics** and **Tools -> Export Session Bundle...** when preparing a bug report.

**📖 [See Full Troubleshooting Guide](VALIS-GUI-Manual.html#troubleshooting-and-faq)**

---

## 📚 Documentation

- **[Quick Start Guide](QUICK_START.md)** - Get running in 5 minutes
- **[User Manual](VALIS-GUI-Manual.html)** - Comprehensive documentation
- **[Guided Tutorial](VALIS-GUI-Tutorial.html)** - Step-by-step workflow
- **[VALIS Library Docs](https://valis.readthedocs.io/)** - Core library documentation
- **[Examples](examples/)** - Sample scripts and datasets

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-qt black isort

# Run tests
pytest

# Format code
black src/ tests/
isort src/ tests/
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.

---

## 📖 Citation

If you use VALIS Workstation in your research, please cite the original VALIS paper:

```bibtex
@article{gatenbee2023valis,
  title={Virtual alignment of pathology image series for multi-gigapixel whole slide images},
  author={Gatenbee, Chandler D and Baker, Ann-Marie and Prabhakaran, Sandhya and others},
  journal={Nature Communications},
  volume={14},
  number={1},
  pages={4502},
  year={2023},
  publisher={Nature Publishing Group UK London}
}
```

**DOI:** https://doi.org/10.1038/s41467-023-40218-9

---

## 🌟 Acknowledgments

- **VALIS Library:** [MathOnco/valis](https://github.com/MathOnco/valis)
- **Napari:** [napari.org](https://napari.org/)
- **Bio-Formats:** [Open Microscopy Environment](https://www.openmicroscopy.org/bio-formats/)
- **Qt Framework:** [Qt Project](https://www.qt.io/)

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/leonardolv/VALIS-GUI/issues)
- **Discussions:** [GitHub Discussions](https://github.com/leonardolv/VALIS-GUI/discussions)
- **Email:** [Contact maintainer]

---

**Made with ❤️ for the pathology and digital histology community**

---

## 🗺️ Roadmap

Future features under consideration:

- [ ] Multi-select slide deletion
- [ ] Custom colormap presets
- [ ] Batch processing mode
- [ ] Registration cancellation
- [ ] ROI-based registration
- [ ] Cloud storage integration
- [ ] Plugin system
- [ ] Undo/redo functionality

**Have a feature request?** [Open an issue](https://github.com/leonardolv/VALIS-GUI/issues/new)!
