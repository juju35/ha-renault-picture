"""Tests for the Renault Picture integration."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.renault_picture.const import DOMAIN

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
