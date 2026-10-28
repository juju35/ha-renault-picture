"""Sensor exposing the official MyRenault picture URL for each vehicle."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import RENAULT_DOMAIN

_LOGGER = logging.getLogger(__name__)

# Kamereon exposes each picture under a PICTURE asset, as renditions whose
# resolutionType is ONE_MYRENAULT_LARGE or ONE_MYRENAULT_SMALL.
_PICTURE_ASSET = "PICTURE"
_SIZE_LARGE = "LARGE"
_SIZE_SMALL = "SMALL"


def _renault_hubs(hass: HomeAssistant) -> list[tuple[ConfigEntry, Any]]:
    """Return (entry, hub) for every loaded core 'renault' config entry."""
    hubs: list[tuple[ConfigEntry, Any]] = []
    for entry in hass.config_entries.async_entries(RENAULT_DOMAIN):
        if entry.state is not ConfigEntryState.LOADED:
            continue
        hub = getattr(entry, "runtime_data", None)
        if hub is not None and getattr(hub, "vehicles", None):
            hubs.append((entry, hub))
    return hubs


def _vehicle_devices(dev_reg: dr.DeviceRegistry, renault_entry: ConfigEntry) -> dict[str, dr.DeviceEntry]:
    """Map VIN -> the device the 'renault' integration created for that vehicle."""
    devices: dict[str, dr.DeviceEntry] = {}
    for device in dr.async_entries_for_config_entry(dev_reg, renault_entry.entry_id):
        for domain, identifier in device.identifiers:
            if domain == RENAULT_DOMAIN:
                devices[identifier] = device
    return devices


def _assets(proxy: Any) -> list[dict[str, Any]]:
    """Return the raw Kamereon assets of a vehicle, or an empty list."""
    try:
        return list(getattr(proxy.details, "assets", None) or [])
    except Exception:  # noqa: BLE001 - details may be missing or partial
        return []


def _picture(proxy: Any, size: str) -> str | None:
    """Return the vehicle picture URL for a size, read straight from the assets."""
    want = f"ONE_MYRENAULT_{size}"
    for asset in _assets(proxy):
        if asset.get("assetType") != _PICTURE_ASSET:
            continue
        for rendition in asset.get("renditions") or []:
            if rendition.get("resolutionType") == want:
                return rendition.get("url")
    return None


def _renditions(proxy: Any) -> list[dict[str, Any]]:
    """Flatten every asset rendition, for diagnostics when no picture matches."""
    return [
        {
            "assetType": asset.get("assetType"),
            "resolutionType": rendition.get("resolutionType"),
            "url": rendition.get("url"),
        }
        for asset in _assets(proxy)
        for rendition in asset.get("renditions") or []
    ]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one picture sensor per Renault vehicle, on that vehicle's device."""
    dev_reg = dr.async_get(hass)
    # This integration owns no device: its sensors join the Renault ones. Drop the
    # devices 0.1.0 created by mistake (HA removes a device left with no entry).
    for device in dr.async_entries_for_config_entry(dev_reg, entry.entry_id):
        dev_reg.async_update_device(device.id, remove_config_entry_id=entry.entry_id)

    hubs = _renault_hubs(hass)
    if not hubs:
        # Startup race, reauth in progress, or 'renault' simply loaded after us:
        # let HA retry the platform setup instead of staying empty until a restart.
        raise PlatformNotReady("No loaded 'renault' integration found")

    entities: list[RenaultPictureSensor] = []
    for renault_entry, hub in hubs:
        devices = _vehicle_devices(dev_reg, renault_entry)
        entities.extend(RenaultPictureSensor(vin, proxy, devices.get(vin)) for vin, proxy in hub.vehicles.items())
    async_add_entities(entities)


class RenaultPictureSensor(SensorEntity):
    """Publishes the official vehicle picture URL (state kept short)."""

    _attr_has_entity_name = True
    _attr_name = "Picture"
    _attr_icon = "mdi:car-side"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, vin: str, proxy: Any, device: dr.DeviceEntry | None) -> None:
        """Initialise the sensor and attach it to the vehicle's Renault device."""
        self._vin = vin
        self._proxy = proxy
        self._attr_unique_id = f"{vin}_picture"
        if device is not None:
            # Same pattern as core helpers (switch_as_x, template): link to a device
            # owned by another integration, so the sensor is "<vehicle> Picture".
            self.device_entry = device
        else:
            self._attr_name = f"{vin} Picture"

    @property
    def native_value(self) -> str:
        """Short state (<=255 chars): whether a picture is available."""
        return "available" if _picture(self._proxy, _SIZE_LARGE) else "unavailable"

    @property
    def entity_picture(self) -> str | None:
        """Large picture URL, used by the frontend as the entity thumbnail."""
        return _picture(self._proxy, _SIZE_LARGE)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the picture URLs, the VIN and the raw renditions."""
        return {
            "vin": self._vin,
            "picture_large": _picture(self._proxy, _SIZE_LARGE),
            "picture_small": _picture(self._proxy, _SIZE_SMALL),
            "available_renditions": _renditions(self._proxy),
        }
