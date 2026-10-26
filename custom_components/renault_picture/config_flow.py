"""Config flow for Renault Picture (single instance, no options)."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN, RENAULT_DOMAIN


class RenaultPictureConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Renault Picture."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if RENAULT_DOMAIN not in self.hass.config.components:
            return self.async_abort(reason="renault_not_loaded")
        if user_input is not None:
            return self.async_create_entry(title="Renault Picture", data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))
