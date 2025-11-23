"""Core logic for translating daylight measurements into lamp colors."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from typing import Tuple
from colorsys import rgb_to_hsv

from .models import ColorRGB, LampColorCommand, LightMeasurement


class ColorMapper(ABC):
    """Abstract mapper turning light measurements into RGB colors."""

    @abstractmethod
    def map_measurement(self, measurement: LightMeasurement) -> LampColorCommand:
        """Convert a measurement to a lamp command."""
        raise NotImplementedError


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _blend(a: float, b: float, factor: float) -> float:
    return a + (b - a) * factor


def _blend_color(color_a: ColorRGB, color_b: ColorRGB, factor: float) -> Tuple[float, float, float]:
    return (
        _blend(color_a.red, color_b.red, factor),
        _blend(color_a.green, color_b.green, factor),
        _blend(color_a.blue, color_b.blue, factor),
    )


@dataclass(frozen=True)
class MapperConfig:
    warm_color: ColorRGB = ColorRGB(255, 160, 64)
    cool_color: ColorRGB = ColorRGB(255, 255, 235)
    min_brightness: float = 40.0
    max_brightness: float = 255.0
    dark_lux: float = 0.0
    bright_lux: float = 255.0
    use_camera_average: bool = False
    min_saturation: float = 0.0
    max_saturation: float = 255.0
    dark_color: ColorRGB = ColorRGB(20, 4, 3)
    dark_brightness: float = 12.0


class DefaultColorMapper(ColorMapper):
    """Mapping daylight measurements to lamp commands with configurable strategy."""

    def __init__(self, config: MapperConfig | None = None) -> None:
        self._config = config or MapperConfig()

    def map_measurement(self, measurement: LightMeasurement) -> LampColorCommand:
        """Convert a measurement to a lamp command using configured strategy."""
        normalized = measurement.normalized
        lux_value = measurement.lux
        if lux_value is None and normalized is not None:
            lux_value = normalized * self._config.bright_lux
        if lux_value is None:
            lux_value = self._config.dark_lux

        lux_range = max(self._config.bright_lux - self._config.dark_lux, 1e-6)
        adjusted = (lux_value - self._config.dark_lux) / lux_range
        normalized = _clamp(adjusted, 0.0, 1.0)
        brightness = _blend(self._config.min_brightness, self._config.max_brightness, normalized)
        scale = brightness / 255.0

        if normalized <= 0.0:
            rgb_color = self._config.dark_color
            brightness = max(brightness, self._config.dark_brightness)
            source = rgb_color
        else:
            if self._config.use_camera_average and measurement.average_color is not None:
                source = measurement.average_color
            else:
                blended = _blend_color(self._config.warm_color, self._config.cool_color, normalized)
                source = ColorRGB(
                    red=int(round(_clamp(blended[0], 0.0, 255.0))),
                    green=int(round(_clamp(blended[1], 0.0, 255.0))),
                    blue=int(round(_clamp(blended[2], 0.0, 255.0))),
                )

            red = int(round(_clamp(source.red * scale, 0.0, 255.0)))
            green = int(round(_clamp(source.green * scale, 0.0, 255.0)))
            blue = int(round(_clamp(source.blue * scale, 0.0, 255.0)))
            rgb_color = ColorRGB(red=red, green=green, blue=blue)

        sat_source = measurement.average_color if measurement.average_color is not None else source
        r_norm = sat_source.red / 255.0
        g_norm = sat_source.green / 255.0
        b_norm = sat_source.blue / 255.0
        _, saturation, _ = rgb_to_hsv(r_norm, g_norm, b_norm)
        saturation_value = _clamp(saturation * 255.0, self._config.min_saturation, self._config.max_saturation)

        brightness_value = int(round(_clamp(brightness, 0.0, 255.0)))
        return LampColorCommand(
            color=rgb_color,
            brightness=brightness_value,
            saturation=int(round(_clamp(saturation_value, 0.0, 255.0))),
        )
