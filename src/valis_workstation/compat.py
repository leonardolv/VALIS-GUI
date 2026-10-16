"""Backports so the package imports on every supported Python (>=3.9)."""

from __future__ import annotations

import enum

if hasattr(enum, "StrEnum"):
    StrEnum = enum.StrEnum
else:  # Python 3.9 / 3.10

    class StrEnum(str, enum.Enum):  # type: ignore[no-redef]
        """Minimal ``enum.StrEnum`` (3.11+) stand-in: str() gives the value."""

        def __str__(self) -> str:
            return str(self.value)

        @staticmethod
        def _generate_next_value_(name, start, count, last_values):
            return name.lower()
