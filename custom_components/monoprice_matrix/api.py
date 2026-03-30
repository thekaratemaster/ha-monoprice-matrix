from __future__ import annotations

import asyncio
import logging
import re
from typing import Sequence, List

from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import AUDIO_SET_FRAMES

_LOGGER = logging.getLogger(__name__)


def _sanitize_host(raw: str) -> str:
    h = (raw or "").strip().strip("/")
    h = re.sub(r"^https?://", "", h, flags=re.I)
    return h


def _frame_with_checksum(frame_wo_checksum: Sequence[int]) -> List[int]:
    """Append checksum byte (two's complement of sum) to the frame."""
    chk = (0x100 - (sum(frame_wo_checksum) & 0xFF)) & 0xFF
    return list(frame_wo_checksum) + [chk]


class MatrixAPI:
    def __init__(self, hass: HomeAssistant, host: str):
        self._hass = hass
        self._host = _sanitize_host(host)
        self._available: bool = True

    @property
    def host(self) -> str:
        return self._host

    @property
    def available(self) -> bool:
        return self._available

    @property
    def submit_url(self) -> str:
        return f"http://{self._host}/cgi-bin/submit"

    async def send_hex(self, hex_text: str) -> bool:
        """
        Send a hex(...) frame via GET.
        Returns True on HTTP success; marks availability False on network issues.
        """
        session = async_get_clientsession(self._hass)
        try:
            async with session.get(
                self.submit_url,
                params={"cmd": hex_text},
                timeout=5,
                ssl=False,
            ) as resp:
                body = (await resp.text()).strip()

                if resp.status != 200:
                    self._available = False
                    _LOGGER.warning("Matrix HTTP %s: %s", resp.status, body)
                    return False

                low = body.lower()
                if "submit failed" in low or "error" in low:
                    # Host is reachable, command rejected
                    self._available = True
                    _LOGGER.warning("Matrix rejected command: %s", body)
                    return False

                self._available = True
                _LOGGER.debug("Matrix submit ok: %s", body or "<empty>")
                return True

        except (ClientError, asyncio.TimeoutError) as exc:
            self._available = False
            _LOGGER.warning("Matrix unreachable (%s): %s", self._host, exc)
            return False

    @staticmethod
    def build_video_route_hex(input_idx: int, output_idx: int) -> str:
        """
        Build a matrix route command in hex(...) format.
        """
        base = [
            0xA5, 0x5B, 0x02, 0x03,
            input_idx & 0xFF, 0x00,
            output_idx & 0xFF,
            0x00, 0x00, 0x00, 0x00, 0x00,
        ]
        frame = _frame_with_checksum(base)
        return "hex(" + ",".join(f"{b:02x}" for b in frame) + ")"

    @staticmethod
    def build_audio_set_hex(letter: str) -> str:
        """
        Build audio set A/B/C/D command in hex(...) format.
        """
        frame = _frame_with_checksum(AUDIO_SET_FRAMES[letter.upper()])
        return "hex(" + ",".join(f"{b:02x}" for b in frame) + ")"
