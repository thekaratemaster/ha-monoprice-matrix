
from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_HOST

class MonopriceMatrixConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=f"Monoprice Matrix ({user_input[CONF_HOST]})",
                data=user_input,
            )
        schema = vol.Schema({ vol.Required(CONF_HOST): str })
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return MonopriceMatrixOptionsFlow(config_entry)

class MonopriceMatrixOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        data = {**self.entry.data, **(self.entry.options or {})}
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        schema = vol.Schema({ vol.Required(CONF_HOST, default=data[CONF_HOST]): str })
        return self.async_show_form(step_id="init", data_schema=schema)
