"""Domain models representing light measurements and color commands."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ColorRGB:
    """Simple RGB color representation using 0-255 channel values."""

    red: int
    green: int
    blue: int


@dataclass
class LightMeasurement:
    """Scalar light intensity measurement with optional normalized value."""

    lux: float
    normalized: float | None = None
