"""Interfaces for interacting with a webcam to read daylight."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from .models import LightMeasurement


class CameraReader(ABC):
    """Abstract camera reader that yields light measurements."""

    @abstractmethod
    def capture_measurement(self) -> LightMeasurement:
        """Return a single daylight measurement from the camera feed."""
        raise NotImplementedError


class FrameExtractor(Protocol):
    """Callable protocol extracting a measurement from a BGR frame."""

    def __call__(self, frame: Any) -> LightMeasurement:
        ...


class OpenCVCameraReader(CameraReader):
    """Placeholder OpenCV implementation to be completed later."""

    def __init__(self, *, device_index: int = 0, extractor: FrameExtractor | None = None) -> None:
        self._device_index = device_index
        self._extractor = extractor

    def capture_measurement(self) -> LightMeasurement:
        """Placeholder method that needs OpenCV integration."""
        raise NotImplementedError("Integrate cv2.VideoCapture and extractor pipeline")
