"""Project names must always map to one folder directly under output/."""

import pytest

from valis_workstation.utils.validation import is_valid_project_name, sanitize_project_name


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("MyProject", "MyProject"),
        ("  padded  ", "padded"),
        ("Bad<>Name", "Bad__Name"),
        ("a/b", "a_b"),
        ("", "New Project"),
        ("..", "New Project"),
        (".", "New Project"),
        ("...", "New Project"),
        ("study.", "study"),
        ("study . ", "study"),
        ("con", "con_project"),
        ("NUL.", "NUL_project"),
        ("v1.2", "v1.2"),
    ],
)
def test_sanitize_project_name(raw, expected):
    assert sanitize_project_name(raw) == expected


@pytest.mark.parametrize("raw", ["..", "../x", "a/..", ".", "x."])
def test_sanitized_name_never_leaves_output_dir(raw):
    name = sanitize_project_name(raw)
    assert name not in ("", ".", "..")
    assert "/" not in name and "\\" not in name


def test_is_valid_project_name():
    assert is_valid_project_name("Study 1")
    assert not is_valid_project_name("..")
    assert not is_valid_project_name("x.")
    assert not is_valid_project_name("")


def test_properties_dock_config_uses_sanitizer(qtbot):
    from valis_workstation.ui.properties_dock import PropertiesDock

    dock = PropertiesDock(simple_elastix_available=True)
    qtbot.addWidget(dock)
    dock._project_name.setText("..")
    assert dock.config().project_name == "New Project"
    assert "border: 2px solid red" in dock._project_name.styleSheet()
    dock._project_name.setText("ok")
    assert dock._project_name.styleSheet() == ""
