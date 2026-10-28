"""Tests for the Renault Picture integration."""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

from homeassistant.config_entries import SIGNAL_CONFIG_ENTRY_CHANGED, ConfigEntryChange
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from custom_components.renault_picture.const import DOMAIN, RENAULT_DOMAIN

from .conftest import PICTURE_ASSETS, VIN, add_renault


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
    assert state.attributes["device_class"] == "enum"
    assert state.attributes["options"] == ["available", "no_picture"]
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


async def test_sensor_reports_no_picture(hass: HomeAssistant, monkeypatch) -> None:
    add_renault(hass, monkeypatch, [{"assetType": "VIDEO", "renditions": []}])
    await _setup(hass)
    entity_id = _picture_entity(hass)
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state.state == "no_picture"
    assert state.attributes.get("entity_picture") is None
    assert state.attributes["picture_large"] is None


async def test_platform_retries_until_renault_loaded(hass: HomeAssistant, monkeypatch) -> None:
    """Without a loaded 'renault' entry the platform raises PlatformNotReady and retries."""
    await _setup(hass)
    assert _picture_entity(hass) is None
    # 'renault' finishes loading later (startup race): the scheduled retry finds it.
    add_renault(hass, monkeypatch, PICTURE_ASSETS)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=60))
    await hass.async_block_till_done()
    assert _picture_entity(hass) is not None


async def test_reload_on_renault_reload(hass: HomeAssistant, fake_renault) -> None:
    """A reload of the 'renault' entry rebuilds the sensors from the fresh hub."""
    await _setup(hass)
    assert _picture_entity(hass) is not None
    new_vin = "VF1TESTVIN0000002"
    # The reloaded 'renault' entry carries a new hub with an extra vehicle.
    fake_renault.runtime_data = SimpleNamespace(
        vehicles={
            VIN: SimpleNamespace(details=SimpleNamespace(assets=PICTURE_ASSETS)),
            new_vin: SimpleNamespace(details=SimpleNamespace(assets=PICTURE_ASSETS)),
        }
    )
    async_dispatcher_send(hass, SIGNAL_CONFIG_ENTRY_CHANGED, ConfigEntryChange.UPDATED, fake_renault)
    await hass.async_block_till_done()
    assert _picture_entity(hass) is not None
    assert _picture_entity(hass, new_vin) is not None


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
