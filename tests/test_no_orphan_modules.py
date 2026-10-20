"""Guard: every module in the package is imported or referenced somewhere.

``utils/pyramid_utils.py`` sat in the tree with 0% coverage and no importer
(and a level-selection bug nobody could hit); it was removed. This sweep stops
the same kind of orphan from accumulating again.
"""

from __future__ import annotations

import re
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "src" / "valis_workstation"

# Entry points that are run, not imported.
ENTRY_POINTS = {"__main__"}


def _modules() -> list[Path]:
    return [p for p in PKG.rglob("*.py") if p.stem != "__init__" and p.stem not in ENTRY_POINTS]


def test_every_module_is_referenced_by_another_file() -> None:
    sources = {p: p.read_text(encoding="utf-8") for p in PKG.rglob("*.py")}
    tests_dir = Path(__file__).resolve().parent
    for p in tests_dir.glob("*.py"):
        if p.name != Path(__file__).name:
            sources[p] = p.read_text(encoding="utf-8")

    orphans = []
    for mod in _modules():
        pattern = re.compile(rf"\b{re.escape(mod.stem)}\b")
        if not any(pattern.search(text) for path, text in sources.items() if path != mod):
            orphans.append(str(mod.relative_to(PKG)))
    assert not orphans, f"Modules nothing refers to (dead code?): {orphans}"
