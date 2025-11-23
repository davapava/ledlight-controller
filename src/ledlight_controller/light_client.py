"""Interfaces for communicating with a Wi-Fi RGB lamp."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from .models import ColorRGB, LampColorCommand

_LOGGER = logging.getLogger(__name__)


class LampController(ABC):
    """Abstract lamp controller capable of pushing RGB updates."""

    @abstractmethod
    def apply_state(self, command: LampColorCommand) -> None:
        """Send a full color command to the lamp."""
        raise NotImplementedError

    def apply_color(self, color: ColorRGB) -> None:
        """Helper to send a plain RGB color at full brightness and saturation."""
        self.apply_state(LampColorCommand(color=color, brightness=255, saturation=255))


class YeelightController(LampController):
    """Placeholder Wi-Fi lamp implementation using a Yeelight-like API."""

    def __init__(self, *, host: str, port: int = 55443, transition_ms: int = 500, token: str | None = None) -> None:
        self._host = host
        self._port = port
        self._transition_ms = transition_ms
        self._token = token

    def apply_state(self, command: LampColorCommand) -> None:
        """Placeholder method for the future socket call."""
        raise NotImplementedError("Implement TCP command to update lamp color")


class TuyaBulbController(LampController):
    """Lamp controller using the local Tuya (tinytuya) protocol."""

    def __init__(
        self,
        *,
        device_id: str,
        address: str,
        local_key: str,
        version: str = "3.3",
        persist_session: bool = True,
        connection_timeout_s: float = 4.0,
    ) -> None:
        self._device_id = device_id
        self._address = address
        self._local_key = local_key
        self._version = version
        self._persist_session = persist_session
        self._connection_timeout_s = connection_timeout_s
        self._device = self._build_device()

    def _build_device(self):  # type: ignore[no-untyped-def]
        try:
            import tinytuya  # type: ignore[import]
        except ModuleNotFoundError as exc:  # pragma: no cover - runtime guard
            raise RuntimeError(
                "tinytuya must be installed to use TuyaBulbController"
            ) from exc

        bulb = tinytuya.BulbDevice(self._device_id, self._address, self._local_key)
        try:
            bulb.set_version(float(self._version))
        except ValueError:
            _LOGGER.warning("Invalid Tuya protocol version '%s'; defaulting to 3.3", self._version)
            bulb.set_version(3.3)
        bulb.set_socketPersistent(self._persist_session)
        bulb.set_socketRetryLimit(3)
        bulb.set_dpsUsed({"20": True, "21": True, "22": True, "23": True, "24": True, "25": True})
        bulb.set_socketTimeout(self._connection_timeout_s)
        return bulb

    def apply_state(self, command: LampColorCommand) -> None:
        """Send a full color command (RGB + brightness/saturation) to the Tuya bulb."""
        bulb = self._device
        try:
            _LOGGER.debug(
                "Setting Tuya bulb %s at %s to RGB(%d,%d,%d) brightness=%d saturation=%d",
                self._device_id,
                self._address,
                command.color.red,
                command.color.green,
                command.color.blue,
                command.brightness,
                command.saturation,
            )
            if not getattr(bulb, "bulb_configured", False):
                bulb.status()
            bulb.turn_on()
            bulb.set_mode("colour")
            bulb.set_colour(command.color.red, command.color.green, command.color.blue)
        except Exception as exc:  # noqa: BLE001
            _LOGGER.exception("Failed to update Tuya bulb: %s", exc)
            raise

    # Backwards compatibility for older callers
    def apply_color(self, color: ColorRGB) -> None:  # type: ignore[override]
        self.apply_state(LampColorCommand(color=color, brightness=255, saturation=255))
