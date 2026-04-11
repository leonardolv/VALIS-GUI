# VALIS Workstation - Quick Start Guide

**Get up and running in 5 minutes!**

---

## 🚀 Installation (2 minutes)

### Option 1: Quick Install

```bash
# Clone the repository
git clone https://github.com/leonardolv/VALIS-GUI.git
cd VALIS-GUI

# Install dependencies
pip install -r requirements.txt

# Run the application
python run_valis_workstation.py
```

### Option 2: With Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run
python run_valis_workstation.py
```

---

## 📋 Basic Workflow (3 minutes)

### Step 1: Open Slides

1. Click **File → Open Slide Folder**
2. Select folder with your slide images (.tif, .svs, .png, etc.)
3. Slides appear in left panel

### Step 2: Configure (Optional)

In the **Properties** panel (right):
- **Project name:** Give it a name
- **Registration type:** Check both boxes for best results
- Leave other settings at defaults

### Step 3: Run Registration

1. Click **File → Run Registration**
2. Wait 5-30 minutes (progress bar shows status)
3. When done, registered slides appear in the viewer

### Step 4: Review Results

- **Napari Viewer (center):** See your registered slides
- **Layers panel (right tab):** Control visibility/opacity
- **Tools → Blink:** Compare slides side-by-side

---

## 🎯 Common Tasks

### Compare Two Registered Slides

1. **Tools → Blink**
2. Select slides A and B
3. Click **Start Blink** or use the **Blend** slider

### View Registration Quality

1. **Tools → Analysis Plot** - See error graph
2. **Tools → Quality Report** - See detailed metrics table

### Export Results

Registered slides are automatically saved to:
```
output/<project_name>/registered/
```

Files are in OME-TIFF format, readable by:
- QuPath
- ImageJ/Fiji
- Python (tifffile, scikit-image)
- MATLAB

---

## ⚠️ Troubleshooting Quick Fixes

| Problem | Quick Fix |
|---------|----------|
| "Napari not available" | `pip install --upgrade napari[all]` |
| "SimpleElastix not found" | Use rigid-only registration (still works!) |
| Out of memory | Reduce "Max image size" to 1024 |
| Slow performance | Uncheck "Non-rigid registration" |
| App won't start | Check Python version: `python --version` (need 3.9+) |

---

## 📖 Need More Help?

- **Full Manual:** [BioSlide-Manual.html](BioSlide-Manual.html)
- **Step-by-step Tutorial:** [BioSlide-Tutorial.html](BioSlide-Tutorial.html)
- **VALIS Docs:** https://valis.readthedocs.io/
- **Report Issues:** https://github.com/leonardolv/VALIS-GUI/issues

---

## 🏃 Example: Registering IHC Slides

```bash
# 1. Start app
python run_valis_workstation.py

# 2. File → Open Slide Folder
#    Navigate to: examples/example_datasets/ihc/

# 3. Set project name: "IHC_Test"

# 4. File → Run Registration

# 5. Wait ~5 minutes

# 6. Tools → Blink to compare results
```

**That's it!** You've registered your first slide series. 🎉

---

**Next Steps:**
- Read the [Full User Manual](BioSlide-Manual.html) for advanced features
- Try warping annotations (Tools → Warp Annotations)
- Experiment with different parameters

Happy registering! 🔬
