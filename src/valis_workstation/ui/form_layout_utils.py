"""Helpers for working with ``QFormLayout`` widgets."""

from PySide6 import QtWidgets


def add_form_spacer(layout: QtWidgets.QFormLayout) -> None:
    """Add a visual spacer row to a ``QFormLayout``.

    ``QFormLayout`` does not provide ``addStretch`` like box layouts.
    A trailing empty row is a simple, compatible spacer.
    """
    layout.addRow(QtWidgets.QLabel(""))
