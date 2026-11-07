"""Base entity shared by the picture sensor and the picture image."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import SIGNAL_CONFIG_ENTRY_CHANGED, ConfigEntry, ConfigEntryChange, ConfigEntryState
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity


class RenaultPictureEntity(Entity):
    """Attached to a vehicle's Renault device; available while its 'renault' entry is loaded."""

    _attr_has_entity_name = True
    # Also gives the translated entity name ("Espace Photo" in French).
    _attr_translation_key = "picture"
    # The assets never change for the lifetime of the hub (a 'renault' reload
    # rebuilds the entities), so nothing is polled.
    _attr_should_poll = False

    def __init__(self, renault_entry: ConfigEntry, hub: Any, vin: str, device: dr.DeviceEntry | None) -> None:
        """Remember the 'renault' entry and hub the data comes from, and attach to the vehicle's device."""
        self._renault_entry = renault_entry
        self._hub = hub
        self._vin = vin
        self._attr_unique_id = f"{vin}_picture"
        if device is not None:
            # Same pattern as core helpers (switch_as_x, template): link to a device
            # owned by another integration, so the entity is "<vehicle> <translated name>".
            # entity_platform only honors a pre-set device_entry since HA 2025.8,
            # hence the minimum version in hacs.json.
            self.device_entry = device
        else:
            # No device to be named after: untranslated fallback that tells vehicles
            # apart by the last 4 VIN characters only (the full VIN stays out of the UI).
            self._attr_name = f"Renault {vin[-4:]} Picture"

    @property
    def available(self) -> bool:
        """Unavailable once the 'renault' entry is no longer loaded or no longer holds this hub (stale data)."""
        return (
            self._renault_entry.state is ConfigEntryState.LOADED
            and getattr(self._renault_entry, "runtime_data", None) is self._hub
        )

    async def async_added_to_hass(self) -> None:
        """Follow the state of the 'renault' entry the data comes from."""
        await super().async_added_to_hass()
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_ENTRY_CHANGED, self._entry_changed))

    @callback
    def _entry_changed(self, _change: ConfigEntryChange, changed_entry: ConfigEntry) -> None:
        """Write the state again when that 'renault' entry changes (unloaded, reloading, back)."""
        if changed_entry.entry_id == self._renault_entry.entry_id:
            self.async_write_ha_state()
