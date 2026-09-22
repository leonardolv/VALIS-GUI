"""``SettingsKeys.CACHE_MAX_TILE_MB``/``PERF_TILE_SIZE`` were orphaned enum
members left over from the 2026-08-19 (2) ``utils/tile_cache.py`` removal.

That change deleted the Preferences "Max Tile Cache" spinbox and "Tile
Size (pixels)" combo (their only readers/writers) but left the two
``SettingsKeys`` enum members themselves (``"cache/max_tile_mb"``,
``"performance/tile_size"``) in place — harmless (QSettings itself never
sees a key nothing reads or writes), but genuine dead code, found by a
2026-09-18 audit and fixed here.

This file does two things:

1. Pins the removal directly (the two names no longer resolve on the
   enum).
2. Guards against the same rot recurring silently: every *remaining*
   member of ``SettingsKeys``/``SplitterKeys`` must be referenced
   somewhere in ``src/`` outside the enum's own definition file, either
   by its literal string value (most call sites read/write via a bare
   string, e.g. ``settings.value("cache/directory", ...)``) or by a
   direct enum reference (a handful of call sites, e.g.
   ``SettingsKeys.LEFT_TAB_INDEX``, pass the enum member itself — a
   ``StrEnum`` is usable as a ``str`` directly). Checking only one of
   the two shapes would under- or over-count: an enum-reference-only grep
   misses the (majority) string-literal call sites, and a
   literal-string-only grep misses the enum-reference call sites, exactly
   as happened when this bug was first triaged.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from valis_workstation.settings_keys import SettingsKeys, SplitterKeys

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src" / "valis_workstation"
SETTINGS_KEYS_FILE = SRC_ROOT / "settings_keys.py"


def _all_python_source(exclude: Path) -> str:
    """Concatenate every ``.py`` file under ``SRC_ROOT`` except ``exclude``."""
    chunks = []
    for path in SRC_ROOT.rglob("*.py"):
        if path == exclude:
            continue
        chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def _member_names_and_values(enum_source: str) -> list[tuple[str, str]]:
    """Parse ``NAME = "value"`` pairs out of the raw enum source text."""
    return re.findall(r'^\s{4}(\w+) = "([^"]+)"', enum_source, re.MULTILINE)


class TestOrphanedTileCacheMembersRemoved:
    """Pins the exact fix: both dead members no longer exist."""

    def test_cache_max_tile_mb_no_longer_exists(self):
        assert not hasattr(SettingsKeys, "CACHE_MAX_TILE_MB")

    def test_perf_tile_size_no_longer_exists(self):
        assert not hasattr(SettingsKeys, "PERF_TILE_SIZE")

    def test_the_literal_key_strings_are_gone_from_the_enum_source(self):
        text = SETTINGS_KEYS_FILE.read_text(encoding="utf-8")
        assert '"cache/max_tile_mb"' not in text
        assert '"performance/tile_size"' not in text

    def test_no_remaining_reference_anywhere_in_src(self):
        # Even if the dead strings appear as a `# TODO` comment or similar,
        # they should not appear as real code anywhere outside the enum's
        # own file (which no longer defines them either, per the test
        # above) — this is a stronger regression guard than "the enum
        # member is gone" alone, since a call site could in principle keep
        # a hardcoded literal.
        source = _all_python_source(exclude=SETTINGS_KEYS_FILE)
        assert "cache/max_tile_mb" not in source
        assert "performance/tile_size" not in source


class TestNoOrphanedSettingsKeyMembers:
    """The general regression guard: every remaining member must be used.

    A member is "used" when either its literal string value or a direct
    ``SettingsKeys.NAME`` / ``SplitterKeys.NAME`` reference appears
    somewhere in ``src/`` outside ``settings_keys.py`` itself.
    """

    @pytest.mark.parametrize(
        "enum_cls,enum_name",
        [(SettingsKeys, "SettingsKeys"), (SplitterKeys, "SplitterKeys")],
    )
    def test_every_member_is_referenced_outside_the_enum_file(
        self, enum_cls, enum_name
    ):
        source = _all_python_source(exclude=SETTINGS_KEYS_FILE)
        unused = []
        for member in enum_cls:
            literal_hit = f'"{member.value}"' in source or f"'{member.value}'" in source
            enum_ref_hit = f"{enum_name}.{member.name}" in source
            if not (literal_hit or enum_ref_hit):
                unused.append(member.name)
        assert unused == [], (
            f"{enum_name} member(s) with zero references outside "
            f"settings_keys.py: {unused}"
        )

    def test_the_check_actually_looked_something_real_was_found_pre_fix(self):
        # Confirms the detector itself has teeth: re-running the exact same
        # literal-value scan against the two names this file's own fix
        # removed would have flagged them, had they still been declared.
        # This does not re-add them to the enum (that would be the bug
        # again) — it just proves the scan used above is not vacuously
        # passing because it can't find anything.
        source = _all_python_source(exclude=SETTINGS_KEYS_FILE)
        for literal in ("cache/max_tile_mb", "performance/tile_size"):
            literal_hit = f'"{literal}"' in source or f"'{literal}'" in source
            assert not literal_hit, (
                f"{literal!r} unexpectedly still referenced in src/ — "
                "the dead-key removal may have been incomplete"
            )
