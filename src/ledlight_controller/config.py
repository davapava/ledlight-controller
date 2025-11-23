"""Application configuration models and helpers."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

from .models import ColorRGB
from .settings_loader import get_section, load_settings

_LOGGER = logging.getLogger(__name__)

DEFAULT_SETTINGS_PATH = Path(__file__).resolve().parents[2] / "config" / "settings.toml"


@dataclass
class CameraConfig:
    """Settings for the webcam capture pipeline."""

    device_index: int = 0
    frame_width: Optional[int] = None
    frame_height: Optional[int] = None
    frame_rate: Optional[int] = None
    rtsp_url: Optional[str] = None
    snapshot_timeout_s: float = 10.0


@dataclass
class LampConfig:
    """Settings required to reach the Wi-Fi RGB lamp.""" 

    protocol: str = "tuya"
    host: Optional[str] = None
    address: Optional[str] = None
    port: int = 55443
    transition_ms: int = 500
    access_token: Optional[str] = None
    device_id: Optional[str] = None
    local_key: Optional[str] = None
    version: str = "3.3"


@dataclass
class MapperSettings:
    """Tuning parameters for the daylight-to-lamp mapper."""

    dark_lux: float = 0.0
    bright_lux: float = 255.0
    min_brightness: float = 40.0
    max_brightness: float = 255.0
    use_camera_average: bool = False
    min_saturation: float = 0.0
    max_saturation: float = 255.0
    dark_color: ColorRGB = ColorRGB(20, 4, 3)
    dark_brightness: float = 12.0


@dataclass
class TapoCaptureConfig:
    """Configuration for snapshot-based capture against a Tapo RTSP stream."""

    interval_seconds: float = 20.0
    timeout_seconds: float = 10.0
    rtsp_url: Optional[str] = None


@dataclass
class AppConfig:
    """Top-level application configuration."""

    camera: CameraConfig
    lamp: LampConfig
    mapper: MapperSettings
    capture_interval_s: float = 5.0
    config_path: Optional[Path] = None


def _parse_tapo_capture(settings: Mapping[str, Mapping[str, object]]) -> TapoCaptureConfig:
    config = TapoCaptureConfig()
    section = get_section(settings, "tapo_capture")

    interval_value = section.get("interval_seconds")
    if isinstance(interval_value, (int, float)) and float(interval_value) > 0:
        config.interval_seconds = float(interval_value)
    elif interval_value is not None:
        _LOGGER.warning(
            "Invalid interval_seconds '%s'; using %.1fs",
            interval_value,
            config.interval_seconds,
        )

    timeout_value = section.get("timeout_seconds")
    if isinstance(timeout_value, (int, float)) and float(timeout_value) > 0:
        config.timeout_seconds = float(timeout_value)
    elif timeout_value is not None:
        _LOGGER.warning(
            "Invalid timeout_seconds '%s'; using %.1fs",
            timeout_value,
            config.timeout_seconds,
        )

    rtsp_value = section.get("rtsp_url")
    if isinstance(rtsp_value, str) and rtsp_value.strip():
        config.rtsp_url = rtsp_value.strip()
    elif rtsp_value is not None:
        _LOGGER.warning("Invalid rtsp_url '%s'; ignoring entry", rtsp_value)

    return config


def _parse_lamp(settings: Mapping[str, Mapping[str, object]]) -> LampConfig:
    config = LampConfig()
    section = get_section(settings, "lamp")

    protocol_value = section.get("protocol")
    if isinstance(protocol_value, str) and protocol_value.strip():
        config.protocol = protocol_value.strip()

    device_id_value = section.get("device_id")
    if isinstance(device_id_value, str) and device_id_value.strip():
        config.device_id = device_id_value.strip()

    local_key_value = section.get("local_key")
    if isinstance(local_key_value, str) and local_key_value.strip():
        config.local_key = local_key_value.strip()

    version_value = section.get("version")
    if isinstance(version_value, (int, float, str)) and str(version_value).strip():
        config.version = str(version_value).strip()

    address_value = section.get("address") or section.get("host")
    if isinstance(address_value, str) and address_value.strip():
        config.address = address_value.strip()
        config.host = address_value.strip()

    return config


def _parse_mapper(settings: Mapping[str, Mapping[str, object]]) -> MapperSettings:
    config = MapperSettings()
    section = get_section(settings, "mapper")

    dark_value = section.get("dark_lux")
    if isinstance(dark_value, (int, float)):
        config.dark_lux = float(dark_value)
    elif dark_value is not None:
        _LOGGER.warning("Invalid mapper.dark_lux '%s'; using %.1f", dark_value, config.dark_lux)

    bright_value = section.get("bright_lux")
    if isinstance(bright_value, (int, float)):
        config.bright_lux = float(bright_value)
    elif bright_value is not None:
        _LOGGER.warning("Invalid mapper.bright_lux '%s'; using %.1f", bright_value, config.bright_lux)

    min_brightness_value = section.get("min_brightness")
    if isinstance(min_brightness_value, (int, float)):
        config.min_brightness = max(0.0, float(min_brightness_value))
    elif min_brightness_value is not None:
        _LOGGER.warning(
            "Invalid mapper.min_brightness '%s'; using %.1f",
            min_brightness_value,
            config.min_brightness,
        )

    max_brightness_value = section.get("max_brightness")
    if isinstance(max_brightness_value, (int, float)):
        config.max_brightness = max(0.0, float(max_brightness_value))
    elif max_brightness_value is not None:
        _LOGGER.warning(
            "Invalid mapper.max_brightness '%s'; using %.1f",
            max_brightness_value,
            config.max_brightness,
        )

    if config.bright_lux <= config.dark_lux:
        adjusted = config.dark_lux + 1.0
        _LOGGER.warning(
            "mapper.bright_lux %.1f must be greater than mapper.dark_lux %.1f; using %.1f",
            config.bright_lux,
            config.dark_lux,
            adjusted,
        )
        config.bright_lux = adjusted

    if config.max_brightness < config.min_brightness:
        _LOGGER.warning(
            "mapper.max_brightness %.1f lower than mapper.min_brightness %.1f; matching minimum",
            config.max_brightness,
            config.min_brightness,
        )
        config.max_brightness = config.min_brightness

    use_camera_value = section.get("use_camera_average")
    if isinstance(use_camera_value, bool):
        config.use_camera_average = use_camera_value
    elif use_camera_value is not None:
        _LOGGER.warning("Invalid mapper.use_camera_average '%s'; using %s", use_camera_value, config.use_camera_average)

    min_sat_value = section.get("min_saturation")
    if isinstance(min_sat_value, (int, float)):
        config.min_saturation = max(0.0, float(min_sat_value))
    elif min_sat_value is not None:
        _LOGGER.warning(
            "Invalid mapper.min_saturation '%s'; using %.1f",
            min_sat_value,
            config.min_saturation,
        )

    max_sat_value = section.get("max_saturation")
    if isinstance(max_sat_value, (int, float)):
        config.max_saturation = max(0.0, float(max_sat_value))
    elif max_sat_value is not None:
        _LOGGER.warning(
            "Invalid mapper.max_saturation '%s'; using %.1f",
            max_sat_value,
            config.max_saturation,
        )

    if config.max_saturation < config.min_saturation:
        _LOGGER.warning(
            "mapper.max_saturation %.1f lower than mapper.min_saturation %.1f; matching minimum",
            config.max_saturation,
            config.min_saturation,
        )
        config.max_saturation = config.min_saturation

    dark_brightness_value = section.get("dark_brightness")
    if isinstance(dark_brightness_value, (int, float)):
        config.dark_brightness = max(0.0, float(dark_brightness_value))
    elif dark_brightness_value is not None:
        _LOGGER.warning(
            "Invalid mapper.dark_brightness '%s'; using %.1f",
            dark_brightness_value,
            config.dark_brightness,
        )

    red_value = section.get("dark_color_red")
    green_value = section.get("dark_color_green")
    blue_value = section.get("dark_color_blue")
    if all(isinstance(value, (int, float)) for value in (red_value, green_value, blue_value)):
        config.dark_color = ColorRGB(
            red=int(max(0, min(255, int(red_value)))),
            green=int(max(0, min(255, int(green_value)))),
            blue=int(max(0, min(255, int(blue_value)))),
        )
    elif any(value is not None for value in (red_value, green_value, blue_value)):
        _LOGGER.warning(
            "Invalid dark_color components (red=%s green=%s blue=%s); using default %s",
            red_value,
            green_value,
            blue_value,
            config.dark_color,
        )

    return config


def load_tapo_capture_config(settings_path: Path | None = None) -> TapoCaptureConfig:
    """Load the Tapo capture configuration from the provided settings file."""

    path = (settings_path or DEFAULT_SETTINGS_PATH).expanduser()
    settings = load_settings(path)
    return _parse_tapo_capture(settings)


def load_lamp_config(settings_path: Path | None = None) -> LampConfig:
    """Load the lamp configuration from the provided settings file."""

    path = (settings_path or DEFAULT_SETTINGS_PATH).expanduser()
    settings = load_settings(path)
    return _parse_lamp(settings)


def load_app_config(settings_path: Path | None = None) -> AppConfig:
    """Load the composite application configuration from settings."""

    path = (settings_path or DEFAULT_SETTINGS_PATH).expanduser()
    settings = load_settings(path)

    capture_config = _parse_tapo_capture(settings)
    lamp_config = _parse_lamp(settings)
    mapper_config = _parse_mapper(settings)

    camera_config = CameraConfig(
        rtsp_url=capture_config.rtsp_url,
        snapshot_timeout_s=capture_config.timeout_seconds,
    )

    return AppConfig(
        camera=camera_config,
        lamp=lamp_config,
        mapper=mapper_config,
        capture_interval_s=capture_config.interval_seconds,
        config_path=path,
    )
