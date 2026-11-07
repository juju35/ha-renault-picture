"""Tests for the Renault Picture diagnostics."""

from __future__ import annotations

import json

from homeassistant.components.diagnostics import REDACTED
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.diagnostics import get_diagnostics_for_config_entry

from custom_components.renault_picture.const import DOMAIN

from .conftest import VIN, add_renault

SECRET_KEY = "s3cr3t-signature"
ASSETS = [
    {
        "assetType": "PICTURE",
        "renditions": [
            {
                "resolutionType": "ONE_MYRENAULT_LARGE",
                "url": f"https://user:pass@img.renault/{VIN}/large.png?key={SECRET_KEY}&vin={VIN}",
            },
            {"resolutionType": "ONE_MYRENAULT_SMALL", "url": "https://img.renault/small.png"},
        ],
    },
    {"assetType": "VIDEO", "renditions": [{"resolutionType": "OTHER", "url": f"https://x/v.mp4#{SECRET_KEY}"}]},
]


async def test_diagnostics_redacts_secrets(hass: HomeAssistant, hass_client, monkeypatch) -> None:
    add_renault(hass, monkeypatch, ASSETS)
    assert await async_setup_component(hass, "diagnostics", {})
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={"username": "me@example.com", "token": "abc"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    diag = await get_diagnostics_for_config_entry(hass, hass_client, entry)

    dumped = json.dumps(diag)
    for secret in (VIN, SECRET_KEY, "me@example.com", "abc", "user:pass"):
        assert secret not in dumped
    assert diag["entry"]["data"] == {"username": REDACTED, "token": REDACTED}
    [renault] = diag["renault_entries"]
    assert renault["state"] == "loaded"
    [vehicle] = renault["vehicles"]
    assert vehicle["vin"] == REDACTED
    assert vehicle["device"] == {"manufacturer": "Renault", "model": "Espace vi"}
    # Host and path stay readable for troubleshooting; credentials, query and fragment go.
    assert vehicle["picture_large"] == f"https://img.renault/{REDACTED}/large.png?{REDACTED}"
    assert vehicle["picture_small"] == "https://img.renault/small.png"
    assert [r["url"] for r in vehicle["available_renditions"]] == [
        f"https://img.renault/{REDACTED}/large.png?{REDACTED}",
        "https://img.renault/small.png",
        f"https://x/v.mp4?{REDACTED}",
    ]
