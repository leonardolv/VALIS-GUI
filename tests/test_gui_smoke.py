import importlib.util

import pytest

pytest.importorskip("PySide6")

if importlib.util.find_spec("napari") is None:
    pytest.skip("napari not available", allow_module_level=True)

from PySide6 import QtWidgets

from valis_workstation.main_window import MainWindow
from valis_workstation.utils.qt_logging import QtLogEmitter


def test_main_window_smoke(qtbot, tmp_path):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    window = MainWindow(tmp_path, QtLogEmitter(), simple_elastix_available=False)
    qtbot.addWidget(window)
    window.show()
    window.close()
    app.processEvents()
