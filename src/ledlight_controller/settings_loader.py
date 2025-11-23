"""Lightweight helper for reading project configuration settings."""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, Mapping, MutableMapping, Any

_LOGGER = logging.getLogger(__name__)

_SECTION_PATTERN = re.compile(r"^\s*\[(?P<name>[^\]]+)\]\s*$")
_KEY_VALUE_PATTERN = re.compile(r"^\s*(?P<key>[A-Za-z0-9_\-]+)\s*=\s*(?P<value>.+)\s*$")


def _strip_inline_comment(line: str) -> str:
    in_single_quote = False
    in_double_quote = False
    for index, char in enumerate(line):
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif char == "#" and not in_single_quote and not in_double_quote:
            return line[:index]
    return line


def _parse_value(raw: str) -> object:
    value = raw.strip()
    if not value:
        return ""
    if value[0] in {'"', '\''} and value[-1] == value[0]:
        return value[1:-1]
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def load_settings(path: Path) -> Dict[str, MutableMapping[str, object]]:
    """Parse a minimal subset of TOML into a nested dictionary."""
    result: Dict[str, MutableMapping[str, object]] = {}
    if not path.exists():
        _LOGGER.debug("Settings file %s missing; returning empty dict", path)
        return result
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        _LOGGER.warning("Could not read %s: %s", path, exc)
        return result

    current_section: MutableMapping[str, object] | None = None

    for raw_line in text.splitlines():
        line = _strip_inline_comment(raw_line).strip()
        if not line:
            continue
        section_match = _SECTION_PATTERN.match(line)
        if section_match:
            section_name = section_match.group("name").strip()
            current_section = result.setdefault(section_name, {})
            continue
        key_value_match = _KEY_VALUE_PATTERN.match(line)
        if key_value_match and current_section is not None:
            key = key_value_match.group("key")
            raw_value = key_value_match.group("value")
            current_section[key] = _parse_value(raw_value)

    return result


def get_section(settings: Mapping[str, Mapping[str, object]], name: str) -> Mapping[str, object]:
    """Return a section mapping, defaulting to an empty dict when missing."""
    return settings.get(name, {})
