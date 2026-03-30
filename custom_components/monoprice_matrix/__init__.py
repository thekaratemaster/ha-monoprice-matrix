from __future__ import annotations

import asyncio
import logging

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_HOST

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SELECT]


def _get_host(entry: ConfigEntry) -> str:
    # UI Options should win over entry.data
    host = (entry.options.get(CONF_HOST) or entry.data.get(CONF_HOST) or "").strip()
    return host


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def _async_test_reachable(hass: HomeAssistant, host: str) -> None:
    """Cheap reachability test (does not change device state)."""
    session = async_get_clientsession(hass)
    try:
        async with session.get(f"http://{host}/", timeout=5, ssl=False) as resp:
            _LOGGER.debug("Matrix reachability %s -> HTTP %s", host, resp.status)
    except (ClientError, asyncio.TimeoutError) as exc:
        raise ConfigEntryNotReady(f"Matrix not reachable at {host}: {exc}") from exc


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    host = _get_host(entry)
    if not host:
        raise ConfigEntryNotReady("Matrix host is empty; check integration options")

    await _async_test_reachable(hass, host)

    hass.data[DOMAIN][entry.entry_id] = {
        CONF_HOST: host,
        "unsub_update_listener": entry.add_update_listener(_async_entry_updated),
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_entry_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    # Reload when host changes in Options
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data[DOMAIN].get(entry.entry_id, {})
    unsub = data.get("unsub_update_listener")
    if unsub:
        unsub()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
