"""Support for RFXtrx covers."""
from __future__ import annotations

import logging
from typing import Any
import asyncio

import RFXtrx as rfxtrxmod

from .. import DeviceTuple

from .abs_tilting_cover import (
    AbstractTiltingCover,
    TILT_MAX_STEP,
    TILT_MID_STEP,
    TILT_MIN_STEP
)

_LOGGER = logging.getLogger(__name__)

ICON_PATH = "/local/rfxtrx/venetian"

DEVICE_TYPE = "Somfy Venetian"

# Event 071a000001010101 Office
# Event 071a000001020101 Front
# Event 071a000001030101 Back
# Event 071a000001060101 Living 1
# Event 071a000001060201 Living 2
# Event 071a000001060301 Living 3
# Event 071a000001060401 Living 4
# Event 071a000001060501 Living 5
# Event 071a00000106ff01 Living all


class SomfyVenetianBlind(AbstractTiltingCover):
    """Representation of a SomfyVenetianBlind RFXtrx cover."""

    def __init__(
        self,
        device: rfxtrxmod.RFXtrxDevice,
        device_id: DeviceTuple,
        entity_info: dict[str, Any],
        event: rfxtrxmod.RFXtrxEvent = None,
    ) -> None:
        """Initialize the SomfyVenetianBlind RFXtrx cover device."""

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
            icon = "up.svg"
            closed = False
        elif self._myattr_tilt_step == TILT_MIN_STEP:
            icon = "10.svg"
            closed = True
        elif self._myattr_tilt_step == 1:
            icon = "20.svg"
            closed = self._myattr_partial_is_closed
        elif self._myattr_tilt_step == TILT_MID_STEP:
            icon = "50.svg"
            closed = False
        elif self._myattr_tilt_step == 3:
            icon = "80.svg"
            closed = self._myattr_partial_is_closed
        elif self._myattr_tilt_step == TILT_MAX_STEP:
            icon = "90.svg"
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


    async def _async_lower_blind(self) -> None:
        """Lower the cover."""
        _LOGGER.info("Invoked _async_lower_blind")

        sync_time = self._myattr_sync_secs if not(self._myattr_is_raised) else self._myattr_close_secs
        await self._async_send_repeat(self._device.send_down05sec)
        await self._async_wait_and_set_position(sync_time, False, 0)


    async def _async_stop_blind(self) -> None:
        """Stop the cover."""
        _LOGGER.info("Invoked _async_stop_blind")
        await self._async_send(self._device.send_stop)


    async def _async_tilt_blind_to_step(self, tilt_step) -> None:
        """Move the cover tilt to a preset position."""
        _LOGGER.info("Invoked _async_tilt_blind_to_mid_step; tilt_step = " + str(tilt_step))

        # Somfy cannot tilt fully up so instead switch to full down
        if tilt_step >= TILT_MAX_STEP:
            tilt_step = TILT_MIN_STEP

        if tilt_step == TILT_MIN_STEP:
            _LOGGER.debug("_async_tilt_blind_to_step; tilting to CLOSED and waiting")
            await self._async_lower_blind()
        else:
            # Move to mid point if not already there or if we've been told to go there
            if tilt_step == TILT_MID_STEP or self._myattr_tilt_step != TILT_MID_STEP:
                sync_time = self._myattr_sync_secs if not(self._myattr_is_raised) else self._myattr_close_secs

                _LOGGER.debug("_async_tilt_blind_to_step; tilting to MID and waiting " + str(sync_time))
                await self._async_send(self._device.send_stop)
                await self._async_wait_and_set_position(sync_time, False, TILT_MID_STEP)

            if tilt_step == 1:
                self._attr_is_opening = True
                self.async_write_ha_state()

                _LOGGER.debug("_async_tilt_blind_to_step; tilting DOWN and waiting " + str(self._myattr_tilt_pos1_secs))
                await self._async_send(self._device.send_down05sec)
                await asyncio.sleep(self._myattr_tilt_pos1_secs)

                await self._async_send(self._device.send_stop)
                self._set_position(False, tilt_step)
                self.async_write_ha_state()
            elif tilt_step == 3:
                self._attr_is_opening = True
                self.async_write_ha_state()

                _LOGGER.debug("_async_tilt_blind_to_step; tilting UP and waiting " + str(self._myattr_tilt_pos2_secs))
                await self._async_send(self._device.send_up05sec)
                await asyncio.sleep(self._myattr_tilt_pos2_secs)

                await self._async_send(self._device.send_stop)
                self._set_position(False, tilt_step)
                self.async_write_ha_state()
