"""Orchestration service that keeps the lamp aligned with ambient daylight."""
from __future__ import annotations

import logging
import time
from typing import Callable

from .camera_client import CameraReader
from .config import AppConfig
from .light_client import LampController
from .pipeline import ColorMapper

_LOGGER = logging.getLogger(__name__)

StopCondition = Callable[[], bool]


class DaylightSyncService:
    """Coordinates webcam measurements and lamp color updates."""

    def __init__(
        self,
        *,
        camera: CameraReader,
        lamp: LampController,
        mapper: ColorMapper,
        config: AppConfig,
        stop_condition: StopCondition | None = None,
    ) -> None:
        self._camera = camera
        self._lamp = lamp
        self._mapper = mapper
        self._config = config
        self._stop_condition = stop_condition or (lambda: False)

    def run(self) -> None:
        """Run the synchronization loop until the stop condition triggers."""
        _LOGGER.info("Starting daylight synchronization loop")
        while not self._stop_condition():
            try:
                measurement = self._camera.capture_measurement()
                lux_value = measurement.lux if measurement.lux is not None else 0.0
                raw_normalized = measurement.normalized
                if raw_normalized is None:
                    raw_normalized = lux_value / 255.0 if lux_value else 0.0

                mapper_settings = self._config.mapper
                lux_range = max(mapper_settings.bright_lux - mapper_settings.dark_lux, 1e-6)
                mapped_normalized = (lux_value - mapper_settings.dark_lux) / lux_range
                mapped_normalized = max(0.0, min(1.0, mapped_normalized))
                target_brightness = (
                    mapper_settings.min_brightness
                    + (mapper_settings.max_brightness - mapper_settings.min_brightness) * mapped_normalized
                )

                command = self._mapper.map_measurement(measurement)
                target_brightness = command.brightness

                average_color = measurement.average_color
                average_color_str = (
                    f"({average_color.red},{average_color.green},{average_color.blue})"
                    if average_color is not None
                    else "(n/a)"
                )

                _LOGGER.info(
                    "Measurement lux=%.2f raw_norm=%.3f avg_rgb=%s dominant=%s mapped_norm=%.3f target_brightness=%d saturation=%d -> lamp RGB(%d,%d,%d)",
                    lux_value,
                    raw_normalized,
                    average_color_str,
                    measurement.dominant_channel or "n/a",
                    mapped_normalized,
                    target_brightness,
                    command.saturation,
                    command.color.red,
                    command.color.green,
                    command.color.blue,
                )
                self._lamp.apply_state(command)
            except Exception as exc:  # noqa: BLE001
                _LOGGER.exception("Daylight sync iteration failed: %s", exc)
            time.sleep(self._config.capture_interval_s)
        _LOGGER.info("Daylight synchronization loop stopped")
