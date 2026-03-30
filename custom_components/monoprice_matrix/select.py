from __future__ import annotations

import logging
import re

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .api import MatrixAPI
from .const import DOMAIN, CONF_HOST, FIXED_INPUTS, FIXED_OUTPUTS

_LOGGER = logging.getLogger(__name__)


# Hard-stable entity IDs so your packages never break
ENTITY_ID_AUDIO_SET = "select.monoprice_matrix_audio_set"
ENTITY_ID_OUTPUT_FMT = "select.monoprice_matrix_output_{n}"


async def _ensure_stable_entity_id(
    hass: HomeAssistant,
    *,
    domain: str,
    platform: str,
    entry_id: str,
    unique_id: str,
    desired_entity_id: str,
) -> None:
    """Rename entity_id in the entity registry to a stable one, if possible."""
    registry = er.async_get(hass)
    reg_entry = registry.async_get(platform, domain, unique_id)  # may be None if not created yet

    # If entity is already created, we can rename it immediately.
    if reg_entry and reg_entry.entity_id != desired_entity_id:
        # Only rename if desired ID is free
        if registry.async_get(desired_entity_id) is None:
            _LOGGER.info("Renaming %s -> %s", reg_entry.entity_id, desired_entity_id)
            registry.async_update_entity(reg_entry.entity_id, new_entity_id=desired_entity_id)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    host = data[CONF_HOST]

    api = MatrixAPI(hass, host=host)

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Monoprice HDBaseT 4x4 Matrix",
        manufacturer="Monoprice",
        model="HDBaseT 4x4 2.0",
        configuration_url=f"http://{host}/",
    )

    entities: list[SelectEntity] = []

    # Outputs
    for out_idx in range(1, FIXED_OUTPUTS + 1):
        unique_id = f"{entry.entry_id}_out_{out_idx}"
        entities.append(
            MatrixOutputSelect(
                api=api,
                name=f"Output {out_idx}",
                unique_id=unique_id,
                inputs=FIXED_INPUTS,
                output_idx=out_idx,
                device_info=device_info,
                desired_entity_id=ENTITY_ID_OUTPUT_FMT.format(n=out_idx),
            )
        )

    # Audio Set
    unique_id_audio = f"{entry.entry_id}_audio_set"
    entities.append(
        MatrixAudioSetSelect(
            api=api,
            unique_id=unique_id_audio,
            device_info=device_info,
            desired_entity_id=ENTITY_ID_AUDIO_SET,
        )
    )

    async_add_entities(entities, update_before_add=False)

    # After entities exist in registry, enforce stable entity IDs (best-effort).
    # (Registry entries exist after add_entities; rename if IDs are free.)
    await hass.async_add_executor_job(lambda: None)  # yield once
    for out_idx in range(1, FIXED_OUTPUTS + 1):
        await _rename_by_unique_id(
            hass,
            unique_id=f"{entry.entry_id}_out_{out_idx}",
            desired_entity_id=ENTITY_ID_OUTPUT_FMT.format(n=out_idx),
        )
    await _rename_by_unique_id(
        hass,
        unique_id=unique_id_audio,
        desired_entity_id=ENTITY_ID_AUDIO_SET,
    )


async def _rename_by_unique_id(hass: HomeAssistant, unique_id: str, desired_entity_id: str) -> None:
    registry = er.async_get(hass)
    # Find registry entry by unique_id
    for ent_id, reg_entry in registry.entities.items():
        if reg_entry.unique_id == unique_id and reg_entry.platform == DOMAIN:
            if reg_entry.entity_id != desired_entity_id and registry.async_get(desired_entity_id) is None:
                _LOGGER.info("Renaming %s -> %s", reg_entry.entity_id, desired_entity_id)
                registry.async_update_entity(reg_entry.entity_id, new_entity_id=desired_entity_id)
            return


class _BaseSelect(SelectEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, *, api: MatrixAPI, device_info: DeviceInfo, desired_entity_id: str):
        self._api = api
        self._attr_device_info = device_info
        self._desired_entity_id = desired_entity_id
        self._current_option: str | None = None

    @property
    def available(self) -> bool:
        # If we've never tried, assume available; after first failure, it will flip false.
        return self._api.available

    @property
    def current_option(self) -> str | None:
        return self._current_option

    async def async_added_to_hass(self) -> None:
        # Restore last option across HA restarts (even if matrix doesn’t report state)
        last = await self.async_get_last_state()
        if last and last.state not in (None, "", "unknown", "unavailable"):
            # For SelectEntity, last.state is the selected option string
            self._current_option = last.state
            self.async_write_ha_state()

    def _parse_option_to_index(self, option: str) -> int | None:
        m = re.search(r"(\d+)$", (option or "").strip())
        if not m:
            return None
        try:
            return int(m.group(1))
        except ValueError:
            return None


class MatrixOutputSelect(_BaseSelect):
    def __init__(
        self,
        *,
        api: MatrixAPI,
        name: str,
        unique_id: str,
        inputs: int,
        output_idx: int,
        device_info: DeviceInfo,
        desired_entity_id: str,
    ):
        super().__init__(api=api, device_info=device_info, desired_entity_id=desired_entity_id)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_options = [f"Input {i}" for i in range(1, inputs + 1)]
        self._output_idx = output_idx

    async def async_select_option(self, option: str) -> None:
        in_idx = self._parse_option_to_index(option)
        if not in_idx:
            _LOGGER.error("Invalid option: %s", option)
            return

        hex_text = self._api.build_video_route_hex(in_idx, self._output_idx)
        ok = await self._api.send_hex(hex_text)
        if not ok:
            _LOGGER.warning("Matrix command failed (Output %s -> Input %s)", self._output_idx, in_idx)
            self.async_write_ha_state()  # update availability
            return

        self._current_option = f"Input {in_idx}"
        self.async_write_ha_state()


class MatrixAudioSetSelect(_BaseSelect):
    def __init__(self, *, api: MatrixAPI, unique_id: str, device_info: DeviceInfo, desired_entity_id: str):
        super().__init__(api=api, device_info=device_info, desired_entity_id=desired_entity_id)
        self._attr_name = "Audio Set"
        self._attr_unique_id = unique_id
        self._attr_options = ["A", "B", "C", "D"]

    async def async_select_option(self, option: str) -> None:
        letter = (option or "").strip().upper()
        if letter not in {"A", "B", "C", "D"}:
            _LOGGER.error("Invalid audio set: %s", option)
            return

        hex_text = self._api.build_audio_set_hex(letter)
        ok = await self._api.send_hex(hex_text)
        if not ok:
            _LOGGER.warning("Matrix command failed (Audio Set %s)", letter)
            self.async_write_ha_state()
            return

        self._current_option = letter
        self.async_write_ha_state()
