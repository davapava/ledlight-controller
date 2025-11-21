"""Core logic for translating daylight measurements into lamp colors."""
from __future__ import annotations

from abc import ABC, abstractmethod

from .models import ColorRGB, LightMeasurement


class ColorMapper(ABC):
    """Abstract mapper turning light measurements into RGB colors."""

    @abstractmethod
    def map_measurement(self, measurement: LightMeasurement) -> ColorRGB:
        """Convert a measurement to a lamp color."""
        raise NotImplementedError


class DefaultColorMapper(ColorMapper):
    """Placeholder mapping strategy for future tuning."""

    def map_measurement(self, measurement: LightMeasurement) -> ColorRGB:
        """Return a static color until the mapping is implemented."""
        raise NotImplementedError("Define mapping from lux to RGB")
