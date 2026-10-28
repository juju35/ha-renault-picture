"""Fixtures for Renault Picture tests: a stand-in for the Renault hub.

The real ``renault`` integration imports ``renault_api``, which is not a test
dependency here, so instead of registering a real ``renault`` config entry we
make ``hass.config_entries.async_entries('renault')`` return a lightweight
stand-in. Nothing to unload at teardown, nothing to import.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.renault_picture.const import RENAULT_DOMAIN

VIN = "VF1TESTVIN0000001"

PICTURE_ASSETS = [
    {
        "assetType": "PICTURE",
        "renditions": [
            {"resolutionType": "ONE_MYRENAULT_LARGE", "url": "https://img.renault/large.png"},
            {"resolutionType": "ONE_MYRENAULT_SMALL", "url": "https://img.renault/small.png"},
        ],
    },
    {"assetType": "VIDEO", "renditions": [{"resolutionType": "OTHER", "url": "https://x/v.mp4"}]},
]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load custom_components/ in every test."""
    yield


def add_renault(
    hass: HomeAssistant,
    monkeypatch: pytest.MonkeyPatch,
    assets: list[dict],
    vin: str = VIN,
) -> SimpleNamespace:
    """Make a loaded 'renault' entry (with one vehicle and its device) visible to the integration.

    The real entry is registered but never set up (so teardown has nothing of the
    'renault' integration to unload); the returned stand-in reports it as loaded.
    """
    vehicle = SimpleNamespace(details=SimpleNamespace(assets=assets))
    hub = SimpleNamespace(vehicles={vin: vehicle})
    real_entry = MockConfigEntry(domain=RENAULT_DOMAIN)
    real_entry.add_to_hass(hass)
    dr.async_get(hass).async_get_or_create(
        config_entry_id=real_entry.entry_id,
        identifiers={(RENAULT_DOMAIN, vin)},
        manufacturer="Renault",
        model="Espace vi",
        name="Espace",
    )
    fake_entry = SimpleNamespace(
        domain=RENAULT_DOMAIN, entry_id=real_entry.entry_id, state=ConfigEntryState.LOADED, runtime_data=hub
    )

    original = hass.config_entries.async_entries

    def patched(domain=None, *args, **kwargs):
        if domain == RENAULT_DOMAIN:
            return [fake_entry]
        return original(domain, *args, **kwargs)

    monkeypatch.setattr(hass.config_entries, "async_entries", patched)
    hass.config.components.add(RENAULT_DOMAIN)
    return fake_entry


@pytest.fixture
def fake_renault(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """A loaded Renault integration (stand-in entry) with one vehicle that has a picture."""
    return add_renault(hass, monkeypatch, PICTURE_ASSETS)
