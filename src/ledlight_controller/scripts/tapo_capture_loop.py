"""Simple capture loop for polling a Tapo C100 RTSP stream."""
from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from ..camera_client import capture_snapshot
from ..config import DEFAULT_SETTINGS_PATH, TapoCaptureConfig, load_tapo_capture_config
from ..image_analysis import ImageAnalysisError, analyse_image
_LOGGER = logging.getLogger(__name__)

def capture_loop(rtsp_url: str, interval_s: float, timeout_s: float) -> None:
    """Continuously pull frames on an interval and remove temporary files."""
    _LOGGER.info(
        "Starting capture loop against %s (interval %.1fs)",
        rtsp_url,
        interval_s,
    )
    while True:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as handle:
            snapshot_path = Path(handle.name)
        try:
            capture_snapshot(rtsp_url, snapshot_path, timeout_s)
            size_kb = snapshot_path.stat().st_size / 1024
            _LOGGER.debug("Snapshot saved at %s (%.1f KiB)", snapshot_path, size_kb)
            _log_image_statistics(snapshot_path)
        except subprocess.CalledProcessError as exc:
            _LOGGER.error("ffmpeg failed with exit code %s", exc.returncode)
        except subprocess.TimeoutExpired:
            _LOGGER.error("ffmpeg timed out after %.1f seconds", timeout_s)
        except RuntimeError as exc:
            _LOGGER.error("Snapshot capture failed: %s", exc)
        except Exception as exc:  # noqa: BLE001
            _LOGGER.exception("Unexpected error while capturing snapshot: %s", exc)
        finally:
            if snapshot_path.exists():
                snapshot_path.unlink()
        time.sleep(interval_s)


def _log_image_statistics(image_path: Path) -> None:
    """Analyse the captured image and emit summary statistics."""
    try:
        stats = analyse_image(image_path)
    except ImageAnalysisError as exc:
        _LOGGER.error("Failed to analyse %s: %s", image_path, exc)
        return

    measurement = stats.measurement
    normalized = measurement.normalized
    if normalized is None:
        normalized = measurement.lux / 255.0 if measurement.lux is not None else 0.0

    avg_color = stats.average_color
    _LOGGER.info(
        "Light measurement lux=%.2f normalized=%.3f avg_rgb=(%d,%d,%d) dominant=%s",
        measurement.lux,
        normalized,
        avg_color.red,
        avg_color.green,
        avg_color.blue,
        stats.dominant_channel,
    )


def _load_capture_config(settings_path: Path) -> TapoCaptureConfig:
    """Load capture configuration, falling back to defaults when needed."""

    config = load_tapo_capture_config(settings_path)
    if config.rtsp_url is None:
        _LOGGER.info("RTSP URL not defined in settings %s", settings_path)
    return config


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Poll a Tapo C100 RTSP stream")
    parser.add_argument(
        "--rtsp-url",
        help="Full RTSP URL including credentials; overrides settings file when provided",
    )
    parser.add_argument(
        "--interval",
        type=float,
        help="Seconds between captures; overrides settings file when provided",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        help="Seconds before ffmpeg times out; overrides settings file when provided",
    )
    parser.add_argument(
        "--settings-path",
        type=Path,
        default=None,
        help="Path to TOML settings file supplying defaults",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings_path = (args.settings_path or DEFAULT_SETTINGS_PATH).expanduser()
    capture_config = _load_capture_config(settings_path)

    interval = args.interval if args.interval is not None else capture_config.interval_seconds
    timeout = args.timeout if args.timeout is not None else capture_config.timeout_seconds
    rtsp_url = args.rtsp_url or capture_config.rtsp_url

    if rtsp_url is None:
        _LOGGER.error(
            "RTSP URL missing; provide --rtsp-url or set tapo_capture.rtsp_url in %s",
            settings_path,
        )
        return 1

    capture_loop(rtsp_url, interval_s=interval, timeout_s=timeout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
