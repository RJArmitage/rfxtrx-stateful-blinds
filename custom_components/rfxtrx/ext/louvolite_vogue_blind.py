"""Support for RFXtrx covers."""
from __future__ import annotations

import logging
from typing import Any

import RFXtrx as rfxtrxmod

from .. import DeviceTuple

from .abs_tilting_cover import (
    AbstractTiltingCover,
    TILT_MAX_STEP,
    TILT_MID_STEP,
    TILT_MIN_STEP
)

_LOGGER = logging.getLogger(__name__)

ICON_PATH = "/local/rfxtrx/vertical"

DEVICE_TYPE = "Vogue Vertical"

CMD_VOGUE_CLOSE_CW = 0x00
CMD_VOGUE_CLOSE_CCW = 0x01
CMD_VOGUE_45_DEGREES = 0x02
CMD_VOGUE_90_DEGREES = 0x03
CMD_VOGUE_135_DEGREES = 0x04


# Event 0919130400A1DB010000 Patio Window

class LouvoliteVogueBlind(AbstractTiltingCover):
    """Representation of a LouvoliteVogueBlind RFXtrx cover."""

    def __init__(
        self,
        device: rfxtrxmod.RFXtrxDevice,
        device_id: DeviceTuple,
        entity_info: dict[str, Any],
        event: rfxtrxmod.RFXtrxEvent = None,
    ) -> None:
        """Initialize the LouvoliteVogueBlind RFXtrx cover device."""

        device.type_string = DEVICE_TYPE
        
        super().__init__(
            device=device,
            device_id=device_id,
            entity_info=entity_info,
            event=event
        )


    @property
    def _entity_picture(self) -> str | None:
        """Return the icon property."""
        if self._is_moving:
            icon = "move.svg"
            closed = False
        elif self._myattr_is_raised:
            icon = "open.svg"
            closed = False
        elif self._myattr_tilt_step == TILT_MIN_STEP:
            icon = "00.svg"
            closed = True
        elif self._myattr_tilt_step == 1:
            icon = "25.svg"
            closed = self._myattr_partial_is_closed
        elif self._myattr_tilt_step == TILT_MID_STEP:
            icon = "50.svg"
            closed = False
        elif self._myattr_tilt_step == 3:
            icon = "75.svg"
            closed = self._myattr_partial_is_closed
        elif self._myattr_tilt_step == TILT_MAX_STEP:
            icon = "99.svg"
            closed = True
        else:
            icon = "mid.svg"
            closed = False

        if self._myattr_colour_open and not(closed):
            icon = ICON_PATH + "/active/" + icon
        else:
            icon = ICON_PATH + "/inactive/" + icon

        return icon


    async def _async_raise_blind(self) -> None:
        """Lift the cover."""
        _LOGGER.info("Invoked _async_raise_blind")
        await self._async_tilt_blind_to_step(TILT_MID_STEP)


    async def _async_lower_blind(self) -> None:
        """Lower the cover."""
        _LOGGER.info("Invoked _async_lower_blind")
        await self._async_tilt_blind_to_step(TILT_MIN_STEP)


    async def _async_stop_blind(self) -> None:
        """Stop the cover."""
        _LOGGER.info("Invoked _async_stop_blind")


    async def _async_tilt_blind_to_step(self, tilt_step) -> None:
        """Move the cover tilt to a preset position."""
        _LOGGER.info("Invoked _async_tilt_blind_to_mid_step; tilt_step = " + str(tilt_step))

        if tilt_step == 0:
            self._attr_is_closing = True
            self.async_write_ha_state()

            _LOGGER.debug("_async_tilt_blind_to_step; tilting CMD_VOGUE_CLOSE_CCW and waiting")
            await self._async_send_repeat(self._device.send_command, CMD_VOGUE_CLOSE_CCW)
            await self._async_wait_and_set_position(self._myattr_close_secs, False, tilt_step)

        elif tilt_step == 1:
            self._attr_is_opening = True
            self.async_write_ha_state()

            _LOGGER.debug("_async_tilt_blind_to_step; tilting CMD_VOGUE_45_DEGREES and waiting " + str(self._myattr_tilt_pos1_secs))
            await self._async_send_repeat(self._device.send_command, CMD_VOGUE_45_DEGREES)
            await self._async_wait_and_set_position(self._myattr_open_secs, False, tilt_step)

        elif tilt_step == 2:
            self._attr_is_opening = True
            self.async_write_ha_state()

            _LOGGER.debug("_async_tilt_blind_to_step; tilting CMD_VOGUE_90_DEGREES and waiting " + str(self._myattr_tilt_pos2_secs))
            await self._async_send_repeat(self._device.send_command, CMD_VOGUE_90_DEGREES)
            await self._async_wait_and_set_position(self._myattr_open_secs, False, tilt_step)

        elif tilt_step == 3:
            self._attr_is_opening = True
            self.async_write_ha_state()

            _LOGGER.debug("_async_tilt_blind_to_step; tilting CMD_VOGUE_135_DEGREES and waiting " + str(self._myattr_tilt_pos2_secs))
            await self._async_send_repeat(self._device.send_command, CMD_VOGUE_135_DEGREES)
            await self._async_wait_and_set_position(self._myattr_open_secs, False, tilt_step)

        else:
            self._attr_is_opening = True
            self.async_write_ha_state()

            _LOGGER.debug("_async_tilt_blind_to_step; tilting CMD_VOGUE_CLOSE_CW and waiting " + str(self._myattr_tilt_pos2_secs))
            await self._async_send_repeat(self._device.send_command, CMD_VOGUE_CLOSE_CW)
            await self._async_wait_and_set_position(self._myattr_close_secs, False, tilt_step)
