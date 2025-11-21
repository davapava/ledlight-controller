"""Application configuration models and helpers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class CameraConfig:
    """Settings for the webcam capture pipeline."""

    device_index: int = 0
    frame_width: Optional[int] = None
    frame_height: Optional[int] = None
    frame_rate: Optional[int] = None


@dataclass
class LampConfig:
    """Settings required to reach the Wi-Fi RGB lamp.""" 

    host: str
    port: int = 55443
    transition_ms: int = 500
    access_token: Optional[str] = None


@dataclass
class AppConfig:
    """Top-level application configuration."""

    camera: CameraConfig
    lamp: LampConfig
    capture_interval_s: float = 5.0
    config_path: Optional[Path] = None
