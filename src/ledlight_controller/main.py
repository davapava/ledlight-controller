"""Command-line entrypoint connecting the service wiring."""
from __future__ import annotations

import logging

from .camera_client import CameraReader
from .config import AppConfig, CameraConfig, LampConfig
from .light_client import LampController
from .pipeline import ColorMapper
from .service import DaylightSyncService


def build_default_app() -> DaylightSyncService:
    """Construct the service with placeholder dependencies."""
    raise NotImplementedError("Wire concrete camera, mapper, and lamp components")


def main() -> None:
    """CLI entrypoint to launch the daylight sync service."""
    logging.basicConfig(level=logging.INFO)
    _app = build_default_app()
    _app.run()


if __name__ == "__main__":
    main()
