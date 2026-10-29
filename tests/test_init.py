"""Tests for the Renault Picture integration."""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

from homeassistant.config_entries import SIGNAL_CONFIG_ENTRY_CHANGED, ConfigEntryChange, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from custom_components.renault_picture.const import DOMAIN, RENAULT_DOMAIN

from .conftest import PICTURE_ASSETS, VIN, add_renault


async def _setup(hass: HomeAssistant, *, expect_loaded: bool = True) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id) is expect_loaded
    await hass.async_block_till_done()
    return entry


def _count_reloads(hass: HomeAssistant, monkeypatch) -> list[str]:
    """Record the reloads scheduled from now on (and still perform them)."""
    calls: list[str] = []
    original = hass.config_entries.async_schedule_reload

    def recording(entry_id: str) -> None:
        calls.append(entry_id)
        original(entry_id)

    monkeypatch.setattr(hass.config_entries, "async_schedule_reload", recording)
    return calls


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


async def test_entry_retries_until_renault_loaded(hass: HomeAssistant, monkeypatch) -> None:
    """Without a loaded 'renault' entry the setup raises ConfigEntryNotReady and HA retries it."""
    entry = await _setup(hass, expect_loaded=False)
    assert entry.state is ConfigEntryState.SETUP_RETRY  # visible as "Retrying setup", not "Loaded"
    assert _picture_entity(hass) is None
    # 'renault' finishes loading later (startup race): the scheduled retry finds it.
    add_renault(hass, monkeypatch, PICTURE_ASSETS)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=60))
    await hass.async_block_till_done(wait_background_tasks=True)
    assert entry.state is ConfigEntryState.LOADED
    assert _picture_entity(hass) is not None


async def test_no_reload_when_renault_hub_unchanged(hass: HomeAssistant, fake_renault, monkeypatch) -> None:
    """A plain UPDATED signal (rename, options, reauth before its reload) keeps the same hub: no reload."""
    await _setup(hass)
    reloads = _count_reloads(hass, monkeypatch)
    async_dispatcher_send(hass, SIGNAL_CONFIG_ENTRY_CHANGED, ConfigEntryChange.UPDATED, fake_renault)
    await hass.async_block_till_done()
    assert reloads == []


async def test_reload_when_renault_removed(hass: HomeAssistant, fake_renault, monkeypatch) -> None:
    """Removing the 'renault' entry reloads us, and the entry then waits in setup retry."""
    entry = await _setup(hass)
    reloads = _count_reloads(hass, monkeypatch)
    fake_renault.state = ConfigEntryState.NOT_LOADED  # no loaded 'renault' entry any more
    async_dispatcher_send(hass, SIGNAL_CONFIG_ENTRY_CHANGED, ConfigEntryChange.REMOVED, fake_renault)
    await hass.async_block_till_done()
    assert reloads == [entry.entry_id]
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_reload_on_renault_reload(hass: HomeAssistant, fake_renault, monkeypatch) -> None:
    """A reload of the 'renault' entry rebuilds the sensors from the fresh hub."""
    entry = await _setup(hass)
    reloads = _count_reloads(hass, monkeypatch)
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
    assert reloads == [entry.entry_id]
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
