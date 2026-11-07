"""Recorder behaviour of the picture sensor (its own module: the recorder must start before hass)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from homeassistant.components.recorder import Recorder, history
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.recorder.common import async_wait_recording_done

from custom_components.renault_picture.const import DOMAIN

from .conftest import VIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(recorder_mock, enable_custom_integrations):
    """Start the recorder before hass, then load custom_components/."""
    yield


async def test_vin_and_urls_not_recorded(recorder_mock: Recorder, hass: HomeAssistant, fake_renault) -> None:
    """The VIN stays in the live state for consumers, but never reaches the recorder history."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{VIN}_picture")
    assert hass.states.get(entity_id).attributes["vin"] == VIN
    await async_wait_recording_done(hass)
    states = await recorder_mock.async_add_executor_job(
        history.get_significant_states, hass, dt_util.utcnow() - timedelta(minutes=5), None, [entity_id]
    )
    recorded = states[entity_id][0].attributes
    assert recorded["friendly_name"] == "Espace Picture"
    for attribute in ("vin", "picture_large", "picture_small", "available_renditions"):
        assert attribute not in recorded
