"""Expose the official MyRenault vehicle picture URL as a sensor.

The picture URL already lives in the data the core ``renault`` integration
loads from Kamereon (``vehicle.details.get_picture()``); this integration only
reads it and publishes it, so it needs no credentials and no network calls of
its own.
"""

from __future__ import annotations

from homeassistant.config_entries import (
    SIGNAL_CONFIG_ENTRY_CHANGED,
    ConfigEntry,
    ConfigEntryChange,
    ConfigEntryState,
)
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import RENAULT_DOMAIN
from .sensor import renault_hubs

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Renault Picture from a config entry."""
    hubs = renault_hubs(hass)
    if not hubs:
        # Startup race, reauth in progress, or 'renault' loaded after us (or removed):
        # HA shows "Retrying setup" and retries the whole entry with a backoff.
        raise ConfigEntryNotReady("No loaded 'renault' integration with vehicles found")

    # Hub each 'renault' entry had when the sensors were built: a reload is only
    # needed when it changes (or the entry goes away), not on every UPDATED signal.
    known_hubs: dict[str, object] = {renault_entry.entry_id: hub for renault_entry, hub in hubs}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    @callback
    def _renault_entry_changed(change: ConfigEntryChange, changed_entry: ConfigEntry) -> None:
        """Reload this entry when a 'renault' entry gets a new hub, appears or goes away.

        The sensors hold a reference to the hub of the moment they were created:
        after a reload of the 'renault' entry (reauth, reconfiguration, vehicle
        added) that hub is stale, so rebuild them from the fresh one. Plain entry
        updates (rename, options, reauth data before its reload) keep the same hub
        and are ignored.
        """
        if changed_entry.domain != RENAULT_DOMAIN:
            return
        if change is ConfigEntryChange.REMOVED:
            if changed_entry.entry_id in known_hubs:
                hass.config_entries.async_schedule_reload(entry.entry_id)
            return
        if changed_entry.state is not ConfigEntryState.LOADED:
            return  # Wait for the end state; intermediate states would reload us several times.
        hub = getattr(changed_entry, "runtime_data", None)
        if hub is None or known_hubs.get(changed_entry.entry_id) is hub:
            return
        known_hubs[changed_entry.entry_id] = hub
        hass.config_entries.async_schedule_reload(entry.entry_id)

    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_CONFIG_ENTRY_CHANGED, _renault_entry_changed))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
