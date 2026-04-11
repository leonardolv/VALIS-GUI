# Manual & Tutorial Improvement Plan

Date: 2026-04-11
Scope: `VALIS-GUI-Manual.html` and `VALIS-GUI-Tutorial.html`

## 1) Objectives

- Improve readability and visual hierarchy for long-form documentation.
- Make feature coverage complete and explicitly aligned with current GUI actions.
- Add task-based tutorial flows that map to real user goals.
- Keep docs maintainable with repeatable update and QA steps.

## 2) Current-State Findings (Audit)

- Manual is comprehensive but very dense (`~1800` lines) and difficult to scan end-to-end.
- Tutorial is detailed (`~800` lines) but can be more guided and outcome-driven.
- Feature set in app is broader than what most users will find quickly in docs unless they already know menu structure.
- Some architecture/doc statements can drift as code is refactored (e.g., MainWindow modular split).

## 3) Feature Coverage Targets

The docs should explicitly cover all user-facing actions in the app menus.

### File Menu
- Open Slide Folder
- Recent Folders
- Save Configuration / Load Configuration
- Run Registration
- Resume Last Registration
- Preferences

### View Menu
- Reset Layout
- Toggle Left Sidebar
- Toggle Right Sidebar
- Expand Center
- Fit to Content

### Tools Menu
- Blink
- Analysis Plot
- Quality Report
- Warp Annotations
- Save Options
- Export ROI Crop
- Merge Slides
- Export Session Bundle

### Help Menu
- Manual (HTML)
- Tutorial (HTML)
- Quick Start
- Report Issue
- Performance Statistics
- Diagnostics
- About

## 4) Visual Improvement Plan

### Phase A: Foundation (Design Tokens + Layout)

- Define a cleaner design token set for both pages:
  - typography scale (headline/subhead/body/caption)
  - spacing scale
  - color roles (text, muted, border, panel, accent, warning, success)
- Standardize card/table/callout styles between manual and tutorial.
- Improve section spacing and reduce visual clutter around large tables and diagrams.

Deliverables:
- Shared style block pattern used in both HTML files.
- Consistent heading rhythm and section-intro pattern.

### Phase B: Navigation and Scannability

- Add section-level "You are here" progress in tutorial.
- Add quick-jump blocks for the most common tasks at top of each major section.
- Add "When to use this" callouts for advanced settings.
- Improve mobile behavior for sidebar/navigation and wide tables.

Deliverables:
- Better sticky nav behavior and mobile breakpoint rules.
- Faster findability for top workflows.

### Phase C: Visual Guidance Assets

- Add lightweight workflow diagrams where text is currently heavy.
- Add expected-result panels (what success looks like after each major step).
- Add compact warning/info callouts with consistent iconography.

Deliverables:
- 3-5 focused diagrams and reusable callout components.

## 5) Feature-Wise Content Improvement Plan

### Manual Enhancements

- Add a "Feature Parity Matrix" (menu action -> section link -> prerequisites).
- Add "Known Limits & Pending Features" section tied to roadmap.
- Add explicit "Failure/Recovery" section:
  - cancel behavior
  - resume behavior
  - diagnostics + session bundle workflow for support
- Add ROI and merge sections with practical constraints and output examples.

### Tutorial Enhancements

- Split into guided tracks:
  - Track 1: First successful registration (fast path)
  - Track 2: Quality validation and troubleshooting
  - Track 3: ROI export workflow
  - Track 4: Merge workflow for multiplex outputs
- Add per-step checkpoints:
  - user action
  - expected UI state
  - expected output files
  - common failure and fix

## 6) QA/Automation Plan

- Add a lightweight docs QA checklist:
  - all internal anchors resolve
  - all cross-links manual <-> tutorial resolve
  - menu/action names match app text exactly
  - outdated filenames are absent
- Add scriptable checks (optional, recommended):
  - grep for forbidden stale names (e.g., removed manual filenames)
  - HTML lint pass for obvious markup issues

## 7) Prioritized Execution Order

### Sprint 1 (High Impact, Low Risk)

- Navigation/scannability updates
- Feature parity matrix
- Track split in tutorial
- Update screenshots/diagrams for top workflows

### Sprint 2 (Depth and Robustness)

- Advanced settings decision support
- Failure/recovery playbooks
- Known limits/pending features section

### Sprint 3 (Polish)

- Visual refinement pass (spacing, type rhythm, cards, callouts)
- Mobile-specific layout polish
- Final consistency/terminology pass

## 8) Acceptance Criteria

- A new user can complete first registration + validation + ROI export from tutorial only.
- Every menu action has a discoverable section in manual and/or tutorial.
- No stale links or removed filenames remain.
- Manual and tutorial share a coherent visual language and navigation behavior.
- Docs match current app behavior and current roadmap status.

## 9) Proposed Next Step

Execute Sprint 1 now:
- restructure tutorial into task tracks,
- add feature parity matrix to manual,
- apply first-pass visual cleanup tokens/styles to both HTML files.
