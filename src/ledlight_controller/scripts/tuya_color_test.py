"""Simple CLI helper to send an RGB colour to a Tuya-compatible lamp."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from ..config import DEFAULT_SETTINGS_PATH, LampConfig, load_lamp_config
from ..light_client import TuyaBulbController
from ..models import ColorRGB

_LOGGER = logging.getLogger(__name__)


def _parse_rgb(args: argparse.Namespace) -> ColorRGB:
    if args.hex:
        hex_value = args.hex.lstrip("#")
        if len(hex_value) != 6:
            raise ValueError("Hex colour must be 6 characters like FF8800")
        return ColorRGB(
            red=int(hex_value[0:2], 16),
            green=int(hex_value[2:4], 16),
            blue=int(hex_value[4:6], 16),
        )

    if args.rgb:
        red, green, blue = args.rgb
        for channel, value in zip(("R", "G", "B"), (red, green, blue), strict=False):
            if not (0 <= value <= 255):
                raise ValueError(f"{channel} component {value} must be within 0-255")
        return ColorRGB(red=red, green=green, blue=blue)

    raise ValueError("Provide either --hex or --rgb for the target colour")


def _build_controller(config: LampConfig) -> TuyaBulbController:
    if config.device_id is None or config.local_key is None:
        raise ValueError("lamp.device_id and lamp.local_key must be provided in settings")
    address = config.address or config.host
    if not address:
        raise ValueError("lamp.address (or host) must be provided in settings")

    return TuyaBulbController(
        device_id=config.device_id,
        local_key=config.local_key,
        address=address,
        version=config.version,
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a colour command to the Tuya lamp")
    colour_group = parser.add_mutually_exclusive_group(required=True)
    colour_group.add_argument("--hex", help="Hex colour value, e.g. ff8800")
    colour_group.add_argument("--rgb", nargs=3, type=int, metavar=("R", "G", "B"), help="RGB components 0-255")
    parser.add_argument(
        "--settings-path",
        type=Path,
        default=None,
        help="Optional settings file (defaults to config/settings.toml)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(asctime)s %(levelname)s %(message)s")

    settings_path = (args.settings_path or DEFAULT_SETTINGS_PATH).expanduser()
    config = load_lamp_config(settings_path)
    try:
        rgb = _parse_rgb(args)
    except ValueError as exc:
        _LOGGER.error("%s", exc)
        return 1

    try:
        controller = _build_controller(config)
    except ValueError as exc:
        _LOGGER.error("%s", exc)
        return 1

    _LOGGER.info("Applying colour RGB(%d,%d,%d)", rgb.red, rgb.green, rgb.blue)
    controller.apply_color(rgb)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
