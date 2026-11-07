"""Diagnostics for Renault Picture.

Lists what this integration reads from each loaded ``renault`` entry, with the
VIN, the account and every secret redacted, and the picture URLs reduced to
their host and path (their query string can carry keys or the vehicle's
configuration).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

from homeassistant.components.diagnostics import REDACTED, async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .sensor import _SIZE_LARGE, _SIZE_SMALL, _picture, _renditions, _vehicle_devices, renault_hubs

TO_REDACT = {
    "access_token",
    "account_id",
    "api_key",
    "email",
    "gigya_token",
    "kamereon_account_id",
    "password",
    "refresh_token",
    "registration_number",
    "token",
    "username",
    "vin",
}


def _redact_url(url: Any, vin: str) -> Any:
    """Keep the host and path of a URL; drop credentials, query and fragment."""
    if not isinstance(url, str) or not url:
        return url
    try:
        parts = urlsplit(url)
    except ValueError:
        return REDACTED
    if not parts.scheme or not parts.hostname:
        return REDACTED
    path = parts.path.replace(vin, REDACTED) if vin else parts.path
    redacted = f"{parts.scheme}://{parts.hostname}{path}"
    if parts.query or parts.fragment:
        redacted += f"?{REDACTED}"
    return redacted


def _vehicle(vin: str, proxy: Any, device: dr.DeviceEntry | None) -> dict[str, Any]:
    """Diagnostics of one vehicle, as the sensor sees it."""
    return {
        "vin": vin,
        "device": None if device is None else {"manufacturer": device.manufacturer, "model": device.model},
        "picture_large": _redact_url(_picture(proxy, _SIZE_LARGE), vin),
        "picture_small": _redact_url(_picture(proxy, _SIZE_SMALL), vin),
        "available_renditions": [
            {**rendition, "url": _redact_url(rendition.get("url"), vin)} for rendition in _renditions(proxy)
        ],
    }


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    dev_reg = dr.async_get(hass)
    renault_entries = []
    for renault_entry, hub in renault_hubs(hass):
        devices = _vehicle_devices(dev_reg, renault_entry)
        renault_entries.append(
            {
                "state": renault_entry.state.value,
                "vehicles": [_vehicle(vin, proxy, devices.get(vin)) for vin, proxy in hub.vehicles.items()],
            }
        )
    return async_redact_data(
        {
            "entry": {
                "title": entry.title,
                "version": entry.version,
                "data": dict(entry.data),
                "options": dict(entry.options),
            },
            "renault_entries": renault_entries,
        },
        TO_REDACT,
    )
