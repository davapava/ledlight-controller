"""Utilities for extracting luminance and color statistics from images."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import cv2  # type: ignore[import]
    import numpy as np
except ModuleNotFoundError as exc:  # pragma: no cover - runtime guard
    raise RuntimeError(
        "The image analysis module requires OpenCV (cv2) and NumPy to be installed"
    ) from exc

from .models import ColorRGB, LightMeasurement

_LOGGER = logging.getLogger(__name__)


@dataclass
class ImageLightStats:
    """Aggregated light and color statistics for a single frame."""

    measurement: LightMeasurement
    average_color: ColorRGB
    dominant_channel: str


class ImageAnalysisError(RuntimeError):
    """Raised when an image cannot be analysed."""


def _load_image_bgr(path: Path) -> np.ndarray:
    """Load an image from *path* as a BGR NumPy array."""
    if not path.exists():
        raise ImageAnalysisError(f"Image path {path} does not exist")
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ImageAnalysisError(f"Unable to decode image at {path}")
    return image


def _compute_average_rgb(image_bgr: np.ndarray) -> tuple[float, float, float]:
    """Return the average RGB components for the provided image."""
    mean_bgr: np.ndarray = image_bgr.mean(axis=(0, 1))
    mean_rgb = mean_bgr[::-1]  # convert BGR -> RGB ordering
    return float(mean_rgb[0]), float(mean_rgb[1]), float(mean_rgb[2])


def _compute_luminance(mean_rgb: tuple[float, float, float]) -> float:
    """Compute the relative luminance (0-255) using the sRGB transfer."""
    r, g, b = mean_rgb
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return float(luminance)


def _infer_dominant_channel(mean_rgb: tuple[float, float, float]) -> str:
    """Identify which channel dominates the average color."""
    channels = {"red": mean_rgb[0], "green": mean_rgb[1], "blue": mean_rgb[2]}
    return max(channels, key=channels.get)


def analyse_image(path: Path) -> ImageLightStats:
    """Analyse the image at *path* and return luminance and color statistics."""
    _LOGGER.debug("Analysing image %s", path)
    image_bgr = _load_image_bgr(path)
    mean_rgb = _compute_average_rgb(image_bgr)
    luminance = _compute_luminance(mean_rgb)

    average_color = ColorRGB(
        red=int(round(mean_rgb[0])),
        green=int(round(mean_rgb[1])),
        blue=int(round(mean_rgb[2])),
    )
    dominant_channel = _infer_dominant_channel(mean_rgb)
    measurement = LightMeasurement(
        lux=luminance,
        normalized=luminance / 255.0,
        average_color=average_color,
        dominant_channel=dominant_channel,
    )
    return ImageLightStats(
        measurement=measurement,
        average_color=average_color,
        dominant_channel=dominant_channel,
    )


def analyse_array(image_bgr: Any) -> ImageLightStats:
    """Variant of :func:`analyse_image` that accepts an in-memory BGR array."""
    if not isinstance(image_bgr, np.ndarray):
        raise ImageAnalysisError("image_bgr must be a NumPy ndarray")
    mean_rgb = _compute_average_rgb(image_bgr)
    luminance = _compute_luminance(mean_rgb)
    average_color = ColorRGB(
        red=int(round(mean_rgb[0])),
        green=int(round(mean_rgb[1])),
        blue=int(round(mean_rgb[2])),
    )
    dominant_channel = _infer_dominant_channel(mean_rgb)
    measurement = LightMeasurement(
        lux=luminance,
        normalized=luminance / 255.0,
        average_color=average_color,
        dominant_channel=dominant_channel,
    )
    return ImageLightStats(
        measurement=measurement,
        average_color=average_color,
        dominant_channel=dominant_channel,
    )
