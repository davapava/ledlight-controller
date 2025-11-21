"""Interfaces for communicating with a Wi-Fi RGB lamp."""
from __future__ import annotations

from abc import ABC, abstractmethod

from .models import ColorRGB


class LampController(ABC):
    """Abstract lamp controller capable of pushing RGB updates."""

    @abstractmethod
    def apply_color(self, color: ColorRGB) -> None:
        """Send a color command to the lamp."""
        raise NotImplementedError


class YeelightController(LampController):
    """Placeholder Wi-Fi lamp implementation using a Yeelight-like API."""

    def __init__(self, *, host: str, port: int = 55443, transition_ms: int = 500, token: str | None = None) -> None:
        self._host = host
        self._port = port
        self._transition_ms = transition_ms
        self._token = token

    def apply_color(self, color: ColorRGB) -> None:
        """Placeholder method for the future socket call."""
        raise NotImplementedError("Implement TCP command to update lamp color")
