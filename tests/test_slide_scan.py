from pathlib import Path

from valis_workstation.services.slide_scan import scan_slide_folder


def test_scan_slide_folder_filters_and_orders(tmp_path: Path) -> None:
    (tmp_path / "b_slide.tif").write_text("a")
    (tmp_path / "a_slide.png").write_text("b")
    (tmp_path / "ignore.txt").write_text("c")

    slides = scan_slide_folder(tmp_path)

    assert [slide.name for slide in slides] == ["a_slide.png", "b_slide.tif"]
