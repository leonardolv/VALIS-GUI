"""Headless-safe wrappers around the blocking ``QMessageBox`` static dialogs.

A modal ``QMessageBox`` run under ``QT_QPA_PLATFORM=offscreen`` (CI, automated
GUI checks) or pytest waits for a click that never comes and hangs the run.
These helpers show the dialog normally for a real user; in a headless
session they log the message and return a safe default instead.

If a caller (typically a test) has replaced ``QMessageBox.<kind>`` with its own
stub, the stub is still honoured, so existing monkeypatching keeps working.
"""

from __future__ import annotations

import logging
import os

from PySide6 import QtWidgets

logger = logging.getLogger(__name__)

_Box = QtWidgets.QMessageBox
_Button = _Box.StandardButton

_ORIGINALS = {
    "information": _Box.information,
    "warning": _Box.warning,
    "critical": _Box.critical,
    "question": _Box.question,
}


def is_headless() -> bool:
    """True when no human can answer a modal dialog."""
    return os.environ.get("QT_QPA_PLATFORM") == "offscreen" or bool(
        os.environ.get("PYTEST_CURRENT_TEST")
    )


def _is_stubbed(kind: str) -> bool:
    return getattr(_Box, kind) is not _ORIGINALS[kind]


def _show(kind: str, default, parent, title: str, text: str, *args):
    if is_headless() and not _is_stubbed(kind):
        logger.info("Headless: suppressed %s dialog %r: %s", kind, title, text)
        return default
    return getattr(_Box, kind)(parent, title, text, *args)


def information(parent, title: str, text: str, *args):
    return _show("information", _Button.Ok, parent, title, text, *args)


def warning(parent, title: str, text: str, *args):
    return _show("warning", _Button.Ok, parent, title, text, *args)


def critical(parent, title: str, text: str, *args):
    return _show("critical", _Button.Ok, parent, title, text, *args)


def question(
    parent,
    title: str,
    text: str,
    buttons=_Button.Yes | _Button.No,
    default_button=_Button.No,
):
    """Ask a Yes/No question; headless sessions get *default_button*."""
    return _show("question", default_button, parent, title, text, buttons, default_button)
