"""``_numpy_to_pixmap`` must render float, constant and multi-channel arrays."""

import numpy as np
import pytest

from valis_workstation.services.thumbnail_generator import (
    _numpy_to_pixmap,
    _to_uint8,
)


@pytest.fixture(scope="module", autouse=True)
def _app():
    from PySide6 import QtWidgets

    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_unit_range_float_is_scaled_not_truncated_to_black():
    arr = np.linspace(0, 1, 16, dtype=np.float32).reshape(4, 4)
    out = _to_uint8(arr)
    assert out.max() == 255 and out.dtype == np.uint8


def test_constant_wide_range_image_does_not_divide_by_zero():
    arr = np.full((4, 4), 1000, dtype=np.uint16)
    with np.errstate(all="raise"):
        out = _to_uint8(arr)
    assert not out.any()


def test_uint16_is_stretched_and_nan_is_tolerated():
    arr = np.array([[0, 1000], [2000, 4000]], dtype=np.uint16)
    assert _to_uint8(arr).max() == 255
    f = np.array([[np.nan, 0.5], [1.0, 0.0]], dtype=np.float32)
    assert _to_uint8(f).dtype == np.uint8


def test_uint8_passes_through_unchanged():
    arr = np.arange(16, dtype=np.uint8).reshape(4, 4)
    assert np.array_equal(_to_uint8(arr), arr)


def test_multichannel_uses_first_three_channels_correctly():
    arr = np.zeros((5, 7, 5), dtype=np.uint8)
    arr[..., 0] = 10
    arr[..., 1] = 20
    arr[..., 2] = 30
    arr[..., 3:] = 200
    pm = _numpy_to_pixmap(arr, 512)
    img = pm.toImage()
    assert (img.width(), img.height()) == (7, 5)
    c = img.pixelColor(6, 4)
    assert (c.red(), c.green(), c.blue()) == (10, 20, 30)


def test_float_rgb_thumbnail_is_not_black():
    arr = np.full((4, 4, 3), 0.8, dtype=np.float32)
    c = _numpy_to_pixmap(arr, 512).toImage().pixelColor(1, 1)
    assert c.red() > 150
