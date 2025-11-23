"""Command-line entrypoint connecting the service wiring."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .camera_client import FfmpegSnapshotCameraReader
from .config import DEFAULT_SETTINGS_PATH, AppConfig, load_app_config
from .light_client import TuyaBulbController
from .pipeline import ColorMapper, DefaultColorMapper, MapperConfig as PipelineMapperConfig
from .service import DaylightSyncService, StopCondition


def _build_lamp_controller(app_config: AppConfig) -> TuyaBulbController:
    lamp_config = app_config.lamp
    if lamp_config.device_id is None or lamp_config.local_key is None:
        raise ValueError("Lamp configuration is missing device_id or local_key")

    address = lamp_config.address or lamp_config.host
    if not address:
        raise ValueError("Lamp configuration requires an IP address (address or host)")

    return TuyaBulbController(
        device_id=lamp_config.device_id,
        address=address,
        local_key=lamp_config.local_key,
        version=lamp_config.version,
    )


def build_default_app(
    settings_path: Path | None = None,
    stop_condition: StopCondition | None = None,
) -> DaylightSyncService:
    """Construct the daylight sync service using the project settings."""

    app_config = load_app_config(settings_path or DEFAULT_SETTINGS_PATH)

    if app_config.camera.rtsp_url is None:
        raise ValueError("Camera configuration missing tapo_capture.rtsp_url")

    camera = FfmpegSnapshotCameraReader(
        rtsp_url=app_config.camera.rtsp_url,
        timeout_s=app_config.camera.snapshot_timeout_s,
    )
    mapper_settings = app_config.mapper
    mapper_config = PipelineMapperConfig(
        min_brightness=mapper_settings.min_brightness,
        max_brightness=mapper_settings.max_brightness,
        dark_lux=mapper_settings.dark_lux,
        bright_lux=mapper_settings.bright_lux,
        use_camera_average=mapper_settings.use_camera_average,
        min_saturation=mapper_settings.min_saturation,
        max_saturation=mapper_settings.max_saturation,
        dark_color=mapper_settings.dark_color,
        dark_brightness=mapper_settings.dark_brightness,
    )
    mapper: ColorMapper = DefaultColorMapper(mapper_config)
    lamp = _build_lamp_controller(app_config)

    return DaylightSyncService(
        camera=camera,
        lamp=lamp,
        mapper=mapper,
        config=app_config,
        stop_condition=stop_condition,
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the daylight sync service")
    parser.add_argument(
        "--settings",
        type=Path,
        help="Path to settings TOML (defaults to config/settings.toml)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        help="Stop after this many capture iterations",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint to launch the daylight sync service."""
    args = _parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    stop_condition: StopCondition | None = None
    if args.iterations is not None and args.iterations >= 0:
        remaining = {"count": args.iterations}

        def _stop() -> bool:
            if remaining["count"] <= 0:
                return True
            remaining["count"] -= 1
            return False

        stop_condition = _stop

    _app = build_default_app(args.settings, stop_condition=stop_condition)
    _app.run()


if __name__ == "__main__":
    main()
