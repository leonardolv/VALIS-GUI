from __future__ import annotations

import logging
import logging.config
import sys
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """Terminal-friendly colored log formatter for rapid debugging."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[1;31m",  # Bold Red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        # Shorten module path for readability
        name = record.name
        if name.startswith("valis_workstation."):
            name = name.replace("valis_workstation.", "vw.")
        record.shortname = name
        msg = super().format(record)
        return f"{color}{msg}{self.RESET}"


def setup_logging(log_dir: Path, *, verbose: bool = False) -> None:
    """Configure application-wide logging with colored console + rotating file.

    Parameters
    ----------
    log_dir : Path
        Directory where log files are stored.
    verbose : bool
        If True, console level is set to DEBUG; otherwise INFO.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "valis_workstation.log"

    console_level = "DEBUG" if verbose else "INFO"

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": (
                    "%(asctime)s.%(msecs)03d [%(levelname)-8s] "
                    "%(name)s:%(funcName)s:%(lineno)d  %(message)s"
                ),
                "datefmt": "%H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": console_level,
                "formatter": "detailed",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "filename": str(log_file),
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
            },
        },
        "loggers": {
            "valis_workstation": {
                "level": "DEBUG",
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
        "root": {
            "level": "WARNING",
            "handlers": ["console", "file"],
        },
    }

    logging.config.dictConfig(config)

    # Apply colored formatter to console if stdout supports ANSI
    if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        for handler in logging.getLogger("valis_workstation").handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(
                handler, logging.FileHandler
            ):
                handler.setFormatter(
                    ColoredFormatter(
                        fmt=(
                            "%(asctime)s.%(msecs)03d [%(levelname)-8s] "
                            "%(shortname)s:%(funcName)s:%(lineno)d  %(message)s"
                        ),
                        datefmt="%H:%M:%S",
                    )
                )

    logger = logging.getLogger("valis_workstation")
    logger.info("Logging initialised  file=%s  console=%s", log_file, console_level)
