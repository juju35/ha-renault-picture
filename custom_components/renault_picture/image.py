"""Image entity serving the official MyRenault picture of each vehicle through Home Assistant."""

from __future__ import annotations

from typing import Any

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import RenaultPictureEntity
from .sensor import _SIZE_LARGE, _picture, vehicles


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one picture image per Renault vehicle, on that vehicle's device."""
    async_add_entities(RenaultPictureImage(hass, *vehicle) for vehicle in vehicles(hass))


class RenaultPictureImage(RenaultPictureEntity, ImageEntity):
    """The large MyRenault picture, downloaded once by Home Assistant and served from /api/image_proxy."""

    def __init__(
        self,
        hass: HomeAssistant,
        renault_entry: ConfigEntry,
        hub: Any,
        vin: str,
        proxy: Any,
        device: dr.DeviceEntry | None,
    ) -> None:
        """Read the picture URL once; ImageEntity fetches and caches the bytes on the first request."""
        RenaultPictureEntity.__init__(self, renault_entry, hub, vin, device)
        ImageEntity.__init__(self, hass, verify_ssl=True)
        self._attr_image_url = _picture(proxy, _SIZE_LARGE)
        # The picture is fixed for the lifetime of the hub: its "last updated" is when it was read.
        self._attr_image_last_updated = dt_util.utcnow()

    @property
    def available(self) -> bool:
        """Also unavailable when the vehicle exposes no picture (nothing to serve)."""
        return super().available and self._attr_image_url is not None
