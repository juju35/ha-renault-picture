"""Config flow for Renault Picture (single instance, no options)."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN
from .sensor import renault_hubs


class RenaultPictureConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Renault Picture."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        # single_config_entry in the manifest already blocks a second entry upstream.
        if not renault_hubs(self.hass):
            # Loaded component is not enough: without a LOADED entry with vehicles
            # the created entry would silently produce no sensor.
            return self.async_abort(reason="renault_not_loaded")
        if user_input is not None:
            return self.async_create_entry(title="Renault Picture", data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))
