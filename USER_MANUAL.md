# VALIS Workstation User Manual

**Version:** 1.0  
**Last Updated:** January 9, 2026

---

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [User Interface Overview](#user-interface-overview)
5. [Registration Workflow](#registration-workflow)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

---

## Introduction

### What is VALIS Workstation?

VALIS Workstation is a graphical user interface (GUI) application for the **VALIS** (Virtual Alignment of pathoLogy Image Series) registration pipeline. It provides an intuitive interface for aligning whole slide images (WSI) using rigid and non-rigid transformations.

### Key Features

- **Automated Registration:** Align multiple slides with minimal user input
- **Interactive Visualization:** View registered slides using embedded Napari viewer
- **Quality Assessment:** Built-in tools for analyzing registration quality
- **Flexible Configuration:** Customize registration parameters
- **Annotation Warping:** Transfer annotations between aligned slides
- **Multiple Output Formats:** Save registered slides as OME-TIFF files

### System Requirements

- **OS:** Windows, macOS, or Linux
- **Python:** 3.9 or higher
- **RAM:** 16GB minimum, 32GB+ recommended for large slides
- **Disk Space:** Sufficient space for slide storage (typically 2-3× input size)
- **GPU:** Optional, but recommended for faster processing

---

## Installation

### Prerequisites

Ensure you have Python 3.9+ installed:

```bash
python --version
```

### Step 1: Clone or Download the Repository

```bash
git clone https://github.com/leonardolv/VALIS-GUI.git
cd VALIS-GUI
```

### Step 2: Install Dependencies

Install required packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

**Core dependencies:**
- PySide6 (Qt GUI framework)
- napari (image viewer)
- valis-wsi (registration library)
- matplotlib, pandas (data visualization)
- pytest, pytest-qt (testing)

### Step 3: Optional - Install SimpleElastix

For **non-rigid registration**, SimpleElastix is required. Installation instructions:

1. Download from: https://github.com/SuperElastix/SimpleElastix
2. Follow platform-specific build instructions
3. Install the Python bindings

> **Note:** If SimpleElastix is not installed, the application will still work but only rigid registration will be available.

### Step 4: Verify Installation

Run the application to verify everything is installed correctly:

```bash
python run_valis_workstation.py
```

You should see the VALIS Workstation window open.

---

## Getting Started

### Launching the Application

From the repository root directory:

```bash
python run_valis_workstation.py
```

Or from VS Code, simply run the `run_valis_workstation.py` file.

### First-Time Setup

When you first launch the application:

1. **Check the Status Dock** (bottom panel) for system messages
2. **Verify Napari** is loaded (you should see a viewer in the center)
3. **Check for SimpleElastix** - if not installed, you'll see a banner in the Properties panel

---

## User Interface Overview

### Main Window Layout

The VALIS Workstation interface consists of several panels (docks):

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

### Panel Descriptions

#### 1. **Project Dock** (Left Panel)

- **Purpose:** Manage slide files for registration
- **Features:**
  - View list of loaded slides
  - **Drag & drop** to reorder slides
  - Slide order determines registration sequence

#### 2. **Properties Dock** (Right Panel - Top Tab)

- **Purpose:** Configure registration parameters
- **Parameters:**
  - **Project name:** Name for output directory
  - **Rigid registration:** Enable/disable rigid alignment (checked by default)
  - **Non-rigid registration:** Enable/disable non-rigid alignment (requires SimpleElastix)
  - **Max image size:** Maximum dimension for processing (default: 2048 pixels)
  - **Match threshold:** Feature matching threshold (0.0-1.0, default: 0.35)
  - **Use GPU:** Enable GPU acceleration if available

#### 3. **Layers Dock** (Right Panel - Bottom Tab)

- **Purpose:** Control layer visibility and appearance in Napari
- **Controls:**
  - **Visible:** Toggle layer visibility (checkbox)
  - **Name:** Layer identifier
  - **Opacity:** Adjust layer transparency (0-100%)
  - **Colormap:** Change color scheme for grayscale layers

#### 4. **Status Dock** (Bottom Panel)

- **Purpose:** Monitor registration progress and view logs
- **Components:**
  - **Progress Bar:** Shows current operation progress (0-100%)
  - **Log Console:** Real-time application logs (INFO level and above)

#### 5. **Napari Viewer** (Center)

- **Purpose:** Visualize slides and registered results
- **Controls:**
  - **Mouse wheel:** Zoom in/out
  - **Left click + drag:** Pan image
  - **Right click:** Context menu
  - Use layer controls to adjust visibility and appearance

### Menu Bar

#### File Menu

- **Open Slide Folder:** Load slides from a directory
- **Run Registration:** Start the registration pipeline

#### Tools Menu

- **Blink:** Toggle between registered slides for comparison
- **Analysis Plot:** View registration error metrics
- **Quality Report:** Detailed quality assessment table
- **Warp Annotations:** Transfer annotations between slides

---

## Registration Workflow

### Step-by-Step Guide

#### Step 1: Load Slides

1. Click **File → Open Slide Folder**
2. Navigate to the folder containing your slide images
3. Select the folder (don't select individual files)
4. Slides will appear in the **Project Dock**

**Supported formats:**
- TIFF (.tif, .tiff)
- SVS (.svs)
- NDPI (.ndpi)
- PNG (.png)
- JPEG (.jpg, .jpeg)
- And 300+ other formats via Bio-Formats

#### Step 2: Order Slides (Optional)

If the automatic ordering isn't suitable:

1. In the **Project Dock**, click and drag slides to reorder
2. The first slide is typically the reference
3. Adjacent slides should be similar for best results

#### Step 3: Configure Parameters

In the **Properties Dock**, adjust settings:

- **Project name:** Enter a descriptive name (e.g., "IHC_Series_2026")
- **Registration type:** 
  - Rigid only: Faster, for simple alignment
  - Rigid + Non-rigid: Better accuracy, slower
- **Max image size:** Larger = slower but more accurate (typical: 2048-4096)
- **Match threshold:** Lower = more matches, higher = stricter matching

#### Step 4: Run Registration

1. Click **File → Run Registration**
2. Monitor progress in the **Status Dock**
3. Registration typically takes 5-30 minutes depending on:
   - Number of slides
   - Image resolution
   - Registration type (rigid vs. non-rigid)

**Progress stages:**
- 0-10%: Initialization
- 10-60%: Registration processing
- 60-90%: Warping and saving slides
- 90-100%: Finalization

#### Step 5: Review Results

After completion:

1. Registered slides appear as layers in **Napari Viewer**
2. Layer names start with "Registered:"
3. Use the **Layers Dock** to:
   - Toggle visibility
   - Adjust opacity for blending
   - Change colormaps

**Output location:**
```
output/
└── <project_name>/
    ├── registered/          # Warped slides (OME-TIFF format)
    ├── summary.csv          # Registration metrics
    └── transforms/          # Transformation matrices
```

---

## Advanced Features

### Advanced Settings Panel (NEW in v1.1)

The **Advanced Settings** panel provides access to expert-level configuration options. To access it:

1. In the **Properties Dock**, expand the **Advanced Settings** group box
2. Configure the following options:

#### Feature Detector Selection

Choose the algorithm for detecting features in images:

- **VGG (default):** Balanced performance, works well for most cases
- **SIFT:** Classic scale-invariant features, robust but slower
- **SuperPoint:** Deep learning-based, best for complex/challenging images (requires GPU)
- **KAZE/AKAZE:** Good for textured biological images
- **BRISK/ORB:** Fast binary features, less accurate
- **DISK:** Deep learning detector, good accuracy

**When to adjust:**
- Default VGG works for 90% of cases
- Use SuperPoint for difficult registrations (requires GPU)
- Use SIFT for maximum robustness when speed isn't critical

#### Transformation Type

Control the degree of deformation allowed:

- **Non-rigid (default):** Full elastic deformation, most accurate
- **Affine:** Rotation, scaling, shearing, translation
- **Rigid:** Only rotation and translation (preserves angles/distances)
- **Similarity:** Rotation, uniform scaling, translation

**When to adjust:**
- Use **Rigid** for slides that should not deform (e.g., hard tissue sections)
- Use **Affine** for moderate tissue deformation
- Use **Non-rigid** for soft tissue with significant deformation (e.g., CyCIF, CODEX)

#### Reference Slide Selection

- **Auto-detect (default):** Automatically selects best reference slide
- **Manual:** Choose specific slide as reference (populated after loading slides)

**When to adjust:**
- Manual selection useful when you know which slide has best staining/focus
- Auto-detect typically chooses slide with most features

#### Crop Mode

Control how registered images are cropped:

- **reference (default):** Crop to reference slide bounds
- **all_overlap:** Crop to intersection of all slides
- **all:** Include all slide areas (no cropping)
- **unchanged:** Keep original slide dimensions

#### Additional Options

- **Use tissue masks:** Generate and use tissue masks for better feature detection
- **Denoise images:** Apply denoising before registration (helps with noisy images)
- **Micro-registration:** Perform high-resolution refinement at full resolution

### Micro-Registration (NEW in v1.1)

High-resolution registration refinement for maximum precision:

**How to use:**

1. Expand **Advanced Settings**
2. Check **Micro-registration**
3. Set **Micro max size** (default: 4096, up to 32768 for extreme precision)
4. Run registration as normal

**Benefits:**
- Refines alignment at higher resolution
- Better for quantitative analysis
- Essential for subcellular feature alignment

**Trade-offs:**
- Significantly slower (2-5× longer)
- Higher memory usage
- Only beneficial for high-resolution slides (>10,000 pixels)

**Recommended for:**
- Multiplexed imaging (CyCIF, CODEX, MIBI)
- Subcellular analysis
- Quantitative morphometry

### Slide Preview Panel (NEW in v1.1)

Visual preview of loaded slides before registration:

**Features:**
- Thumbnail grid view of all loaded slides
- Metadata tooltips (dimensions, file type, channels)
- Click slides to highlight/select
- Adjustable thumbnail size (64-256 pixels)
- Toggle between grid and list view

**How to use:**

1. Load slides via **File → Open Slide Folder**
2. Switch to **Slide Preview** tab (left panel)
3. Verify all slides loaded correctly
4. Adjust thumbnail size with slider
5. Click slide to select/highlight

### Save Options Dialog (NEW in v1.1)

Customize output file format and compression:

**How to access:**

1. Click **Tools → Save Options...**
2. Configure settings:

#### Pyramid Levels
- **Range:** 1-10 levels
- **Default:** 4 levels
- **Effect:** More levels = better viewer performance, larger file
- **Recommended:** 4-6 for whole slide images, 2-3 for ROIs

#### Compression
- **Range:** 0-9
- **0:** No compression (fastest, largest files)
- **1:** Fast compression (good balance) ← **Default**
- **5-6:** Balanced compression/speed
- **9:** Maximum compression (slowest, smallest files)
- **Recommended:** 1 for working files, 6-9 for archival

#### Image Quality
- **Range:** 1-100 (JPEG only)
- **Default:** 95
- **Effect:** Higher = better quality, larger files
- **Recommended:** 90-95 for diagnostic quality, 80-85 for previews

#### Tile Size
- **Options:** 128, 256, 512, 1024, 2048 pixels
- **Default:** 512
- **Effect:** Smaller tiles = better for sparse viewing, more overhead
- **Recommended:** 256-512 for web viewers, 1024 for local

#### Format
- **OME-TIFF (default):** Standard for microscopy, preserves metadata
- **TIFF:** General purpose, good compatibility
- **JPEG:** Lossy compression, smallest files
- **PNG:** Lossless, good for web/preview

**Example workflows:**

**Fast working files:**
```
Pyramid levels: 3
Compression: 0
Format: TIFF
```

**Archival storage:**
```
Pyramid levels: 6
Compression: 9
Format: OME-TIFF
```

**Web visualization:**
```
Pyramid levels: 5
Tile size: 256
Format: OME-TIFF
```

### Merge Slides Dialog (NEW in v1.1)

Combine registered slides into single multi-channel image:

**Purpose:** Essential for multiplexed imaging workflows (CyCIF, CODEX, IMC, MIBI)

**How to use:**

1. Complete registration of all slides
2. Click **Tools → Merge Slides...**
3. Configure merge options:

#### Channel Mapping Table

For each slide:
- **Include:** Check to include in merge
- **Slide Name:** Source slide (read-only)
- **Channel Name:** Output channel name (editable)
- **Color:** Visualization color (Auto, Red, Green, Blue, Cyan, Magenta, Yellow)

**Quick actions:**
- **Select All:** Include all slides
- **Select None:** Deselect all

#### Merge Options

- **Overlap handling:** How to combine overlapping pixels
  - **Average:** Mean of overlapping values (default, best for most cases)
  - **Maximum:** Take brightest value (good for sparse markers)
  - **Minimum:** Take darkest value
  - **First/Last:** Use first or last slide's value

- **Output name:** Name for merged image file
- **Normalize intensities:** Normalize intensity ranges across channels (recommended)

**Example: CyCIF Workflow**

1. Register rounds: DAPI-1, CD3, CD8, DAPI-2, PD1, etc.
2. Open **Merge Slides**
3. Configure channels:
   ```
   Slide1 (DAPI-1) → Channel: DAPI, Color: Blue
   Slide2 (CD3)    → Channel: CD3,  Color: Red
   Slide3 (CD8)    → Channel: CD8,  Color: Green
   Slide4 (PD1)    → Channel: PD1,  Color: Cyan
   ```
4. Set overlap handling: **Average**
5. Enable **Normalize intensities**
6. Click **OK** to merge

**Output:**
- Single multi-channel OME-TIFF
- Compatible with QuPath, FIJI, Napari
- Preserves spatial alignment
- Ready for multiplexed analysis

**Note:** Actual merge implementation will be available in next update. Current version shows configuration interface.

### Blink Viewer

**Purpose:** Rapidly alternate between registered slides to detect misalignments.

**How to use:**

1. Complete a registration run
2. Click **Tools → Blink**
3. In the Blink Viewer dialog:
   - **Slide A:** Select first slide
   - **Slide B:** Select second slide
   - **Blend:** Adjust opacity slider (0-100%)
   - **Start Blink:** Click to toggle automatic blinking
4. Observe the viewer - misaligned features will "jump"

**Tips:**
- Blink rate: 600ms (default)
- Perfect alignment = no movement during blink
- Use blend slider for manual comparison

### Analysis Plot

**Purpose:** Visualize registration error metrics across slide pairs.

**How to use:**

1. After registration, click **Tools → Analysis Plot**
2. View the plot showing error metrics vs. slide pairs
3. Metrics displayed (if available):
   - **TRE (Target Registration Error):** Distance between matched points
   - Lower values = better registration

**Interpreting the plot:**
- **Flat line:** Consistent registration quality
- **Spikes:** Problematic slide pairs (investigate further)
- **Trend:** Overall quality across series

### Quality Report

**Purpose:** Detailed table of registration metrics for each slide pair.

**How to use:**

1. Click **Tools → Quality Report**
2. Review the table with columns such as:
   - Slide pair identifiers
   - Registration errors (rigid, non-rigid)
   - Number of matched features
3. Sort by clicking column headers
4. Identify problematic pairs

### Warp Annotations

**Purpose:** Transfer annotations (e.g., ROIs, cell coordinates) from one slide to registered coordinates.

**How to use:**

1. Click **Tools → Warp Annotations**
2. Configure:
   - **Annotation file:** Select JSON file with annotations
   - **Source slide:** The slide where annotations were created
   - **Output directory:** Where to save warped annotations
3. Click **Warp** to process
4. Output: JSON file with transformed coordinates

**Annotation format:**
```json
{
  "annotations": [
    {
      "type": "polygon",
      "coordinates": [[x1, y1], [x2, y2], ...]
    }
  ]
}
```

### Layer Control Tips

**Overlaying slides:**
1. Load multiple layers
2. Set opacity to 50% for each
3. Toggle visibility to compare

**Color blending:**
1. Assign different colormaps (e.g., red, green)
2. Adjust opacity
3. Creates false-color overlay for feature comparison

---

## Troubleshooting

### Common Issues

#### 1. **"Napari not available" message**

**Cause:** Napari failed to import or initialize.

**Solutions:**
- Reinstall napari: `pip install --upgrade napari[all]`
- Check for Qt conflicts: Ensure only PySide6 is installed
- Restart the application

#### 2. **"SimpleElastix not found" banner**

**Cause:** SimpleElastix is not installed.

**Impact:** Non-rigid registration is disabled.

**Solutions:**
- Install SimpleElastix (see Installation section)
- Or proceed with rigid-only registration

#### 3. **Registration fails with "No slides provided"**

**Cause:** Slide folder is empty or contains unsupported formats.

**Solutions:**
- Verify folder contains image files
- Check file extensions are supported
- Try a different folder

#### 4. **Out of memory errors**

**Cause:** Slides are too large for available RAM.

**Solutions:**
- Reduce **Max image size** parameter (e.g., 1024 instead of 2048)
- Close other applications
- Process fewer slides at once
- Upgrade system RAM

#### 5. **JVM initialization failed**

**Cause:** Java runtime not found or scyjava issue.

**Solutions:**
- Install Java JDK/JRE
- Check `scyjava` installation: `pip install --upgrade scyjava`
- Restart application

#### 6. **Slow performance**

**Causes:** Large images, CPU-only processing, many slides.

**Solutions:**
- Enable **Use GPU** if you have a compatible GPU
- Reduce max image size
- Process slides in batches
- Upgrade hardware

### Log Files

**Location:** `logs/valis_workstation.log`

**Log levels:**
- **DEBUG:** Detailed execution traces
- **INFO:** General progress messages
- **WARNING:** Non-critical issues
- **ERROR:** Failures and exceptions

**Viewing logs:**
- Real-time: Check **Status Dock → Log Console**
- Full logs: Open `logs/valis_workstation.log` in a text editor

**When reporting bugs:**
Include the last 50-100 lines from the log file, especially ERROR messages.

---

## FAQ

### General Questions

**Q: What file formats are supported?**  
A: VALIS supports 300+ formats via Bio-Formats and OpenSlide, including TIFF, SVS, NDPI, PNG, JPEG, CZI, and more.

**Q: How long does registration take?**  
A: Typically 5-30 minutes for 5-10 slides. Factors: slide size, number of slides, registration type, hardware.

**Q: Can I process slides from different stains?**  
A: Yes, VALIS can register slides with different staining (e.g., H&E, IHC). Feature matching is robust to appearance changes.

**Q: Is GPU required?**  
A: No, but GPU acceleration significantly speeds up certain operations.

### Technical Questions

**Q: What is the difference between rigid and non-rigid registration?**  
A: 
- **Rigid:** Translation, rotation, scaling. Preserves shape. Fast.
- **Non-rigid:** Allows local deformations. Better for tissue distortion. Slower. Requires SimpleElastix.

**Q: What does "Max image size" do?**  
A: Resizes slides to this maximum dimension for processing. Smaller = faster but less accurate. Larger = slower but more precise.

**Q: What is the "Match threshold"?**  
A: Controls feature matching strictness. Lower (e.g., 0.2) = more matches, more potential false positives. Higher (e.g., 0.5) = fewer, more reliable matches.

**Q: Can I cancel a running registration?**  
A: Currently no. Close the application to stop (Ctrl+Q or close window). This will be added in a future version.

**Q: Where are the output files saved?**  
A: In `output/<project_name>/` within the repository directory. Registered slides are in the `registered/` subfolder.

### Workflow Questions

**Q: Do I need to order slides manually?**  
A: No, VALIS can auto-order by feature similarity. Manual ordering helps if you know the sequence.

**Q: Can I register just 2 slides?**  
A: Yes, though VALIS is optimized for series of 3+ slides.

**Q: How do I know if registration succeeded?**  
A: 
1. Check for "Registration complete" message
2. Use Blink viewer to visually verify
3. Review Analysis Plot for error metrics
4. Check that output files were created

**Q: What if registration quality is poor?**  
A: 
- Increase max image size
- Adjust match threshold
- Enable non-rigid registration
- Ensure slides are from adjacent serial sections
- Check for slide quality issues (focus, staining)

---

## Additional Resources

### Documentation

- **VALIS Library Docs:** https://valis.readthedocs.io/
- **Napari Docs:** https://napari.org/
- **Original Paper:** Gatenbee et al. 2023, Nature Communications

### Support

- **GitHub Issues:** https://github.com/leonardolv/VALIS-GUI/issues
- **Email:** [Contact maintainer]

### Citation

If you use VALIS Workstation in your research, please cite:

```
Gatenbee, C.D., Baker, A.M., Prabhakaran, S. et al. 
Virtual alignment of pathology image series for multi-gigapixel whole slide images. 
Nat Commun 14, 4502 (2023). 
https://doi.org/10.1038/s41467-023-40218-9
```

---

## Version History

**v1.0** (January 2026)
- Initial release
- PySide6-based GUI
- Napari integration
- Modular architecture
- Comprehensive logging
- Test suite

---

## Quick Reference

### Feature Detectors

| Detector | Speed | Accuracy | GPU Required | Best For |
|----------|-------|----------|-------------|----------|
| VGG | Medium | High | No | H&E slides (default) |
| SIFT | Fast | Good | No | Textured images |
| KAZE | Medium | Good | No | Multi-scale features |
| BRISK | Very Fast | Fair | No | Real-time / fluorescence |
| ORB | Very Fast | Fair | No | Fast processing |
| AKAZE | Fast | Good | No | Textured images |
| SuperPoint | Slow | Excellent | Yes | Complex cases |
| DISK | Slow | Excellent | Yes | High detail |

### Transformer Types

| Type | Description | Best For |
|------|-------------|----------|
| Non-Rigid | Rigid + elastic deformation | Serial sections (default) |
| Affine | Rotation, scaling, shearing | Re-scanned slides |
| Rigid | Rotation + translation only | Minimal deformation |
| Similarity | Rotation, uniform scaling | General alignment |

### Crop Modes

| Mode | Description | Best For |
|------|-------------|----------|
| Reference | Crop to reference slide | Serial sections (default) |
| All Overlap | Intersection of all slides | Consistent coverage |
| All | No cropping | Maximum area |
| Unchanged | Original dimensions | Post-processing |

### Preprocessing Options

- **Use Tissue Masks:** Focus on tissue areas, ignore background. Good for slides with artifacts or large background areas.
- **Denoise:** Improve feature detection in noisy/low-quality scans. Adds 15-25% processing time.
- **Micro-Registration:** High-resolution refinement for cell-level accuracy. Use 4096 px for 20x, 8192 px for 40x scans.

### Save Options

| Parameter | Default | Range | Impact |
|-----------|---------|-------|--------|
| Pyramid Levels | 4 | 1-10 | +33% file size, faster viewing |
| Compression | 1 | 0-9 | 50-70% reduction at level 6 |
| Tile Size | 512 | 128-2048 | Affects viewer loading speed |
| Image Quality | 95 | 1-100 | JPEG only, 80-90% reduction at 85 |

### Workflow Presets

**High-Quality H&E:** VGG, Non-Rigid, Reference crop, Masks on, Denoise on, Micro-reg 4096 px

**Fast Fluorescence:** BRISK, Rigid, All Overlap crop, no masks/denoise/micro-reg

**High-Res Multiplexed:** SuperPoint (GPU), Affine, Reference crop, Masks on, Micro-reg 8192 px

---

**End of User Manual**

For the latest updates, visit: https://github.com/leonardolv/VALIS-GUI
