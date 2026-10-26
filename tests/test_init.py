"""Tests for the Renault Picture integration."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.renault_picture.const import DOMAIN, RENAULT_DOMAIN

from .conftest import VIN, add_renault


async def _setup(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _picture_entity(hass: HomeAssistant, vin: str = VIN) -> str | None:
    return er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{vin}_picture")


async def test_config_flow_aborts_without_renault(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "renault_not_loaded"


async def test_config_flow_creates_entry(hass: HomeAssistant, fake_renault) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_sensor_exposes_picture(hass: HomeAssistant, fake_renault) -> None:
    await _setup(hass)
    entity_id = _picture_entity(hass)
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state.state == "available"
    # Attached to the vehicle's Renault device, and named after it.
    device = dr.async_get(hass).async_get(er.async_get(hass).async_get(entity_id).device_id)
    assert device.name == "Espace"
    assert (RENAULT_DOMAIN, VIN) in device.identifiers
    assert state.attributes["friendly_name"] == "Espace Picture"
    assert state.attributes["entity_picture"] == "https://img.renault/large.png"
    assert state.attributes["picture_large"] == "https://img.renault/large.png"
    assert state.attributes["picture_small"] == "https://img.renault/small.png"
    assert state.attributes["vin"] == VIN
    # Only the PICTURE asset's two renditions plus the VIDEO one are listed.
    assert len(state.attributes["available_renditions"]) == 3


async def test_sensor_unavailable_without_picture(hass: HomeAssistant, monkeypatch) -> None:
    add_renault(hass, monkeypatch, [{"assetType": "VIDEO", "renditions": []}])
    await _setup(hass)
    entity_id = _picture_entity(hass)
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state.state == "unavailable"
    assert state.attributes.get("entity_picture") is None
    assert state.attributes["picture_large"] is None


async def test_no_entity_without_renault(hass: HomeAssistant) -> None:
    await _setup(hass)
    assert _picture_entity(hass) is None


async def test_stale_devices_of_this_integration_removed(hass: HomeAssistant, fake_renault) -> None:
    """Devices 0.1.0 created under this integration are dropped; the Renault one stays."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    dev_reg = dr.async_get(hass)
    stale = dev_reg.async_get_or_create(config_entry_id=entry.entry_id, identifiers={(DOMAIN, "legacy")})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert dev_reg.async_get(stale.id) is None
    assert not dr.async_entries_for_config_entry(dev_reg, entry.entry_id)
    entity = er.async_get(hass).async_get(_picture_entity(hass))
    assert dev_reg.async_get(entity.device_id).name == "Espace"
