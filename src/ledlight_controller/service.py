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
            measurement = self._camera.capture_measurement()
            _LOGGER.debug("Captured measurement: %s", measurement)
            color = self._mapper.map_measurement(measurement)
            _LOGGER.debug("Mapped color: %s", color)
            self._lamp.apply_color(color)
            _LOGGER.info("Applied color to lamp")
            time.sleep(self._config.capture_interval_s)
        _LOGGER.info("Daylight synchronization loop stopped")
