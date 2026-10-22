"""Long combo entries in the Properties dock stay readable (tooltips + wide list)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")
from PySide6 import QtCore, QtWidgets

from valis_workstation.ui.properties_dock import PropertiesDock, make_combo_readable


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_helper_sets_full_text_tooltips_and_wide_popup(app):
    combo = QtWidgets.QComboBox()
    combo.addItems(["Short", "A very long entry that would be elided in a narrow dock"])
    make_combo_readable(combo)
    long_text = combo.itemText(1)
    assert combo.itemData(1, QtCore.Qt.ItemDataRole.ToolTipRole) == long_text
    assert combo.view().minimumWidth() >= combo.fontMetrics().horizontalAdvance(long_text)
    assert combo.minimumContentsLength() == 12


def test_properties_dock_long_combos_have_item_tooltips(app):
    dock = PropertiesDock(simple_elastix_available=True)
    combo = dock._feature_detector
    for i in range(combo.count()):
        assert combo.itemData(i, QtCore.Qt.ItemDataRole.ToolTipRole) == combo.itemText(i)
    assert dock._transformer_type.itemData(0, QtCore.Qt.ItemDataRole.ToolTipRole).startswith("Similarity")


def test_reference_slide_list_refresh_keeps_tooltips(app):
    dock = PropertiesDock(simple_elastix_available=True)
    dock.update_reference_slide_list(["slide_a_with_a_really_long_name.ome.tiff"])
    combo = dock._reference_slide
    assert combo.itemData(1, QtCore.Qt.ItemDataRole.ToolTipRole) == combo.itemText(1)
