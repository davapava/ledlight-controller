"""Simple capture loop for polling a Tapo C100 RTSP stream."""
from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_LOGGER = logging.getLogger(__name__)


def _capture_snapshot(rtsp_url: str, destination: Path, timeout_s: float) -> None:
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


def capture_loop(rtsp_url: str, interval_s: float, timeout_s: float) -> None:
    """Continuously pull frames on an interval and remove temporary files."""
    _LOGGER.info("Starting capture loop against %s", rtsp_url)
    while True:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as handle:
            snapshot_path = Path(handle.name)
        try:
            _capture_snapshot(rtsp_url, snapshot_path, timeout_s)
            size_kb = snapshot_path.stat().st_size / 1024
            _LOGGER.debug("Snapshot saved at %s (%.1f KiB)", snapshot_path, size_kb)
        except subprocess.CalledProcessError as exc:
            _LOGGER.error("ffmpeg failed with exit code %s", exc.returncode)
        except subprocess.TimeoutExpired:
            _LOGGER.error("ffmpeg timed out after %.1f seconds", timeout_s)
        except Exception as exc:  # noqa: BLE001
            _LOGGER.exception("Unexpected error while capturing snapshot: %s", exc)
        finally:
            if snapshot_path.exists():
                snapshot_path.unlink()
        time.sleep(interval_s)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Poll a Tapo C100 RTSP stream")
    parser.add_argument("--rtsp-url", required=True, help="Full RTSP URL including credentials")
    parser.add_argument("--interval", type=float, default=20.0, help="Seconds between captures")
    parser.add_argument("--timeout", type=float, default=10.0, help="Seconds before ffmpeg times out")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    capture_loop(args.rtsp_url, interval_s=args.interval, timeout_s=args.timeout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
