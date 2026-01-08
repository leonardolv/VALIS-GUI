import logging
from pathlib import Path

from valis_workstation.utils.logging_config import setup_logging


def test_logging_creates_file(tmp_path: Path) -> None:
    setup_logging(tmp_path)
    logger = logging.getLogger("valis_workstation.test")
    logger.info("Hello log")

    log_file = tmp_path / "valis_workstation.log"
    assert log_file.exists()
    assert log_file.read_text(encoding="utf-8")
