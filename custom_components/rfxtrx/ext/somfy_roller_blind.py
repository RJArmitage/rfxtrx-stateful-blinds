"""Support for RFXtrx covers."""
from __future__ import annotations

import logging
from typing import Any
import asyncio
from collections.abc import Callable

import RFXtrx as rfxtrxmod

from homeassistant.core import callback
from homeassistant.components.cover import (
    CoverEntity, 
    CoverEntityFeature,
    CoverDeviceClass,
    ATTR_POSITION
)

from .. import DeviceTuple, RfxtrxCommandEntity, _Ts

from .const import (
    CONF_CLOSE_SECONDS,
    CONF_COLOUR_ICON,
    CONF_CUSTOM_ICON,
    CONF_OPEN_SECONDS,
    CONF_PARTIAL_CLOSED,
    CONF_ROLLER_MID_ON_CLOSE,
    CONF_SIGNAL_REPETITIONS,
    CONF_SIGNAL_REPETITIONS_DELAY_MS,
    CONF_SYNC_SECONDS,
    DEF_CLOSE_SECONDS,
    DEF_COLOUR_ICON,
    DEF_CUSTOM_ICON,
    DEF_OPEN_SECONDS,
    DEF_PARTIAL_CLOSED,
    DEF_ROLLER_MID_ON_CLOSE,
    DEF_SIGNAL_REPETITIONS_DELAY_MS,
    DEF_SYNC_SECONDS,
)

_LOGGER = logging.getLogger(__name__)

ICON_PATH = "/hacsfiles/rfxtrx-stateful-blinds-icons/icons/roller"

LIFT_POS_CLOSED = 0
LIFT_POS_MID = 1
LIFT_POS_OPEN = 2

# Event 071a000002010101 Kitchen


class SomfyRollerBlind(RfxtrxCommandEntity, CoverEntity):
    """Representation of a SomfyRollerBlind RFXtrx cover supporting lift."""

    _device: rfxtrxmod.RollerTrolDevice | rfxtrxmod.RfyDevice | rfxtrxmod.LightingDevice

    def __init__(
        self,
        device: rfxtrxmod.RFXtrxDevice,
        device_id: DeviceTuple,
        entity_info: dict[str, Any],
        event: rfxtrxmod.RFXtrxEvent = None,
    ) -> None:
        """Initialize the SomfyRollerBlind RFXtrx cover device."""

        super().__init__(device, device_id, event)

        self._attr_is_closed: bool | None = True
        self._attr_current_cover_position = 0
        self._attr_device_class = CoverDeviceClass.SHADE

        self._attr_supported_features = (
            CoverEntityFeature.OPEN |
            CoverEntityFeature.CLOSE |
            CoverEntityFeature.SET_POSITION |
            CoverEntityFeature.STOP
        )

        self._myattr_repetitions = entity_info.get(CONF_SIGNAL_REPETITIONS, 1)
        self._myattr_repetition_delay = entity_info.get(CONF_SIGNAL_REPETITIONS_DELAY_MS, DEF_SIGNAL_REPETITIONS_DELAY_MS) / 1000
        self._myattr_close_secs = entity_info.get(CONF_CLOSE_SECONDS, DEF_CLOSE_SECONDS)
        self._myattr_open_secs = entity_info.get(CONF_OPEN_SECONDS, DEF_OPEN_SECONDS)
        self._myattr_sync_secs = entity_info.get(CONF_SYNC_SECONDS, DEF_SYNC_SECONDS) / 1000
        self._myattr_custom_icon = entity_info.get(CONF_CUSTOM_ICON, DEF_CUSTOM_ICON)
        self._myattr_colour_open = entity_info.get(CONF_COLOUR_ICON, DEF_COLOUR_ICON)
        self._myattr_partial_is_closed = entity_info.get(CONF_PARTIAL_CLOSED, DEF_PARTIAL_CLOSED)
        self._myattr_close_to_mid = entity_info.get(CONF_ROLLER_MID_ON_CLOSE, DEF_ROLLER_MID_ON_CLOSE)

        self._myattr_lift_step = LIFT_POS_CLOSED


    async def async_added_to_hass(self) -> None:
        """Restore device state."""
        await super().async_added_to_hass()

        if self._event is None:
            old_state = await self.async_get_last_state()
            if old_state is not None:
                old_pos = old_state.attributes['current_position']
                _LOGGER.info("async_added_to_hass: old_pos = " + str(old_pos))

                self._set_position(self._pos_to_steps(old_pos))


    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        if not(self._is_moving):
            if ATTR_POSITION in kwargs:
                position = kwargs[ATTR_POSITION]
                if position > 85:
                    _LOGGER.debug("async_set_cover_position: opening cover")
                    await self._async_move_blind_to_step(LIFT_POS_OPEN)
                elif position < 15:
                    _LOGGER.debug("async_set_cover_position: closing cover")
                    await self._async_move_blind_to_step(LIFT_POS_CLOSED)
                else:
                    _LOGGER.debug("async_set_cover_position: closing cover to PARTIAL")
                    await self._async_move_blind_to_step(LIFT_POS_MID)
        else:
            _LOGGER.debug("async_set_cover_position: cover is in motion - ignoring")


    async def async_toggle(self, **kwargs: Any) -> None:
        """Toggle the entity."""
        if self._is_moving:
            _LOGGER.debug("async_toggle: cover is in motion - ignoring")
        else:
            if self._myattr_lift_step == LIFT_POS_OPEN:
                await self.async_close_cover(**kwargs)
            else:
                await self.async_open_cover(**kwargs)


    async def async_open_cover(self, **kwargs: Any) -> None:
        """Move the cover up."""
        if not(self._is_moving):
            _LOGGER.debug("async_open_cover: RAISING cover")
            await self._async_move_blind_to_step(LIFT_POS_OPEN)
        else:
            _LOGGER.debug("async_open_cover: cover is in motion - ignoring")


    async def async_close_cover(self, **kwargs: Any) -> None:
        """Move the cover down."""
        if not(self._is_moving):
            if self._myattr_close_to_mid:
                _LOGGER.debug("async_close_cover: closing cover to PARTIAL")
                await self._async_move_blind_to_step(LIFT_POS_MID)
            else:
                _LOGGER.debug("async_close_cover: closing cover to CLOSED")
                await self._async_move_blind_to_step(LIFT_POS_CLOSED)
        else:
            _LOGGER.debug("async_close_cover: cover is in motion - ignoring")


    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        if not(self._is_moving):
            _LOGGER.debug("async_stop_cover: cover is not in motion - ignoring")
        else:
            _LOGGER.debug("async_stop_cover: stopping cover")
            self._attr_is_closing = False
            self._attr_is_open = False
            self.async_write_ha_state()

            await self._async_stop_blind()


    async def async_update_cover_position(self, **kwargs) -> None:
        """Update the internal position."""
        _LOGGER.info("Invoked async_update_cover_position")


    def _apply_event(self, event: rfxtrxmod.RFXtrxEvent) -> None:
        """Apply command from rfxtrx."""
        assert isinstance(event, rfxtrxmod.ControlEvent)
        super()._apply_event(event)


    @callback
    def _handle_event(self, event: rfxtrxmod.RFXtrxEvent, device_id: DeviceTuple) -> None:
        """Check if event applies to me and update."""
        if device_id != self._device_id:
            return

        self._apply_event(event)
        self.async_write_ha_state()


    @property
    def _is_moving(self) -> bool | None:
        return self._attr_is_opening or self._attr_is_closing


    @property
    def entity_picture(self):
        """Return the icon property."""

        if self._myattr_custom_icon:
            if self._is_moving:
                icon = "move.svg"
                closed = False
            elif self._myattr_lift_step == LIFT_POS_OPEN:
                icon = "99.svg"
                closed = False
            elif self._myattr_lift_step == LIFT_POS_MID:
                icon = "50.svg"
                closed = self._myattr_partial_is_closed
            elif self._myattr_lift_step == LIFT_POS_CLOSED:
                icon = "00.svg"
                closed = True

            if self._myattr_colour_open and not(closed):
                icon = ICON_PATH + "/active/" + icon
            else:
                icon = ICON_PATH + "/inactive/" + icon

            _LOGGER.debug("Returned icon attribute = " + icon)
            return icon
    
        return None


    def _pos_to_steps(self, position) -> int:
        return int(round(position/ (100 / LIFT_POS_OPEN)))
    

    def _steps_to_pos(self, steps) -> int:
        return int(round((steps / LIFT_POS_OPEN) * 100))


    def _set_position(self, step) -> None:
        if step < LIFT_POS_CLOSED:       
            self._myattr_lift_step = LIFT_POS_CLOSED
        elif step >= LIFT_POS_OPEN:       
            self._myattr_lift_step = LIFT_POS_OPEN
        else:       
            self._myattr_lift_step = step

        """Translate my lift position to HA position
        None is unknown, 0 is closed, 100 is fully open."""

        if self._myattr_lift_step == LIFT_POS_CLOSED:
            self._attr_is_closed = True
            self._attr_current_cover_position = 0
        elif self._myattr_lift_step == LIFT_POS_MID:
            self._attr_is_closed = self._myattr_partial_is_closed
            self._attr_current_cover_position = 50
        else:
            self._attr_is_closed = False
            self._attr_current_cover_position = 100

        self._attr_is_opening = False
        self._attr_is_closing = False

        _LOGGER.debug("_set_position; set new position - closed = " + str(self._attr_is_closed) + " pos = " + str(self._attr_current_cover_position))


    async def _async_wait_and_set_position(self, delay, step) -> None:
        if delay > 0:
            _LOGGER.info("_async_wait_and_set_position: Waiting secs = " + str(delay))

            if step == LIFT_POS_OPEN:
                self._attr_is_opening = True
            elif step == LIFT_POS_CLOSED:
                self._attr_is_closing = True
            elif self._myattr_partial_is_closed:
                self._attr_is_closing = True
            else:
                self._attr_is_opening = True
            self.async_write_ha_state()

            await asyncio.sleep(delay)

        # If the blind is still closing then we have finished. Otherwise assume we were interrupted
        if self._is_moving:
            _LOGGER.info("_async_wait_and_set_position: Finished blind action, setting state")
            self._set_position(step)
            self.async_write_ha_state()
        else:
            _LOGGER.info(
                "_async_wait_and_set_position: Finished blind action, state not as expected - not saving new state")


    async def _async_raise_blind(self) -> None:
        """Lift the cover."""
        _LOGGER.info("Invoked _async_raise_blind")
        await self._async_move_blind_to_step(LIFT_POS_OPEN)


    async def _async_lower_blind(self) -> None:
        """Lower the cover."""
        _LOGGER.info("Invoked _async_lower_blind")
        await self._async_move_blind_to_step(LIFT_POS_CLOSED)


    async def _async_stop_blind(self) -> None:
        """Stop the cover."""
        _LOGGER.info("Invoked _async_stop_blind")
    
        await self._async_send(self._device.send_stop)


    async def _async_move_blind_to_step(self, step) -> None:
        """Move the cover to a preset position."""
        _LOGGER.info("Invoked _async_move_blind_to_step; step = " + str(step))

        if step == LIFT_POS_OPEN:
            self._attr_is_opening = True
            self._attr_current_cover_position = 50
            self.async_write_ha_state()

            _LOGGER.debug("_async_move_blind_to_step; sending UP and waiting")
            await self._async_send(self._device.send_up05sec)
            await self._async_wait_and_set_position(self._myattr_open_secs, LIFT_POS_OPEN)

        elif step == LIFT_POS_MID:
            self._attr_is_closing = self._myattr_partial_is_closed
            self._attr_is_opening = not(self._myattr_partial_is_closed)
            self._attr_current_cover_position = 50
            self.async_write_ha_state()

            _LOGGER.debug("_async_move_blind_to_step; sending STOP and waiting")
            await self._async_send(self._device.send_stop)
            await self._async_wait_and_set_position(self._myattr_open_secs, LIFT_POS_MID)

        elif step == LIFT_POS_CLOSED:
            self._attr_is_closing = True
            self._attr_current_cover_position = 50
            self.async_write_ha_state()

            _LOGGER.debug("_async_move_blind_to_step; sending DOWN and waiting")
            await self._async_send(self._device.send_down05sec)
            await self._async_wait_and_set_position(self._myattr_close_secs, LIFT_POS_CLOSED)


    async def _async_send(self, fun: Callable[[rfxtrxmod.PySerialTransport, *_Ts], None], *args: *_Ts) -> None:
        """Send a command to the motor."""
        _LOGGER.info("Invoked _async_send; command = " + fun.__name__)
        await super()._async_send(fun, *args)


    async def _async_send_repeat(self, fun: Callable[[rfxtrxmod.PySerialTransport, *_Ts], None], *args: *_Ts) -> None:
        """Repeating send a command to the motor."""
        _LOGGER.info("Invoked _async_send_repeat; command = " + fun.__name__)

        if self._myattr_repetitions >= 2:
            for _ in range(self._myattr_repetitions - 1):
                await self._async_send(fun, *args)
                await asyncio.sleep(self._myattr_repetition_delay)
        await self._async_send(fun, *args)
