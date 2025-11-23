"""Interfaces for interacting with a webcam to read daylight."""
from __future__ import annotations

import logging
import subprocess
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Protocol

from .image_analysis import ImageAnalysisError, analyse_image
from .models import LightMeasurement

_LOGGER = logging.getLogger(__name__)


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


def capture_snapshot(rtsp_url: str, destination: Path, timeout_s: float) -> None:
    """Capture a single frame using ffmpeg and store it at *destination*."""

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-rtsp_transport",
        "tcp",
        "-i",
        rtsp_url,
        "-frames:v",
        "1",
        "-y",
        str(destination),
    ]
    _LOGGER.debug("Executing capture command: %s", " ".join(cmd))
    subprocess.run(cmd, check=True, timeout=timeout_s)


class FfmpegSnapshotCameraReader(CameraReader):
    """Camera reader that samples frames from an RTSP stream via ffmpeg."""

    def __init__(self, *, rtsp_url: str, timeout_s: float = 10.0) -> None:
        if not rtsp_url:
            raise ValueError("rtsp_url must be provided for snapshot capture")
        self._rtsp_url = rtsp_url
        self._timeout_s = timeout_s

    def capture_measurement(self) -> LightMeasurement:
        """Capture a snapshot, analyse it, and return the resulting measurement."""

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as handle:
            snapshot_path = Path(handle.name)

        try:
            capture_snapshot(self._rtsp_url, snapshot_path, self._timeout_s)
            stats = analyse_image(snapshot_path)
            _LOGGER.debug(
                "Snapshot measurement lux=%.2f normalized=%.3f",
                stats.measurement.lux,
                stats.measurement.normalized or 0.0,
            )
            return stats.measurement
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError("Failed to capture snapshot via ffmpeg") from exc
        except ImageAnalysisError as exc:
            raise RuntimeError("Failed to analyse captured snapshot") from exc
        finally:
            if snapshot_path.exists():
                snapshot_path.unlink()
