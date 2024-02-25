"""Support for RFXtrx covers."""
from __future__ import annotations

import logging
from typing import Any
import asyncio
from collections.abc import Callable

import RFXtrx as rfxtrxmod

from homeassistant.core import callback
from homeassistant.const import (
    ATTR_STATE,
    STATE_CLOSING,
    STATE_OPENING
)
from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature,
    CoverDeviceClass,
    ATTR_POSITION,
    ATTR_TILT_POSITION
)

from .. import DeviceTuple, RfxtrxCommandEntity, _Ts
from ..const import CONF_VENETIAN_BLIND_MODE

from .const import (
    CONF_CLOSE_SECONDS,
    CONF_COLOUR_ICON,
    CONF_CUSTOM_ICON,
    CONF_OPEN_SECONDS,
    CONF_PARTIAL_CLOSED,
    CONF_SIGNAL_REPETITIONS,
    CONF_SIGNAL_REPETITIONS_DELAY_MS,
    CONF_SYNC_SECONDS,
    CONF_TILT_POS1_MS,
    CONF_TILT_POS2_MS,
    DEF_CLOSE_SECONDS,
    DEF_COLOUR_ICON,
    DEF_CUSTOM_ICON,
    DEF_OPEN_SECONDS,
    DEF_PARTIAL_CLOSED,
    DEF_SIGNAL_REPETITIONS_DELAY_MS,
    DEF_SYNC_SECONDS,
    DEF_TILT_POS1_MS,
    DEF_TILT_POS2_MS,
)

_LOGGER = logging.getLogger(__name__)

TILT_MIN_STEP = 0
TILT_MID_STEP = 2
TILT_MAX_STEP = 4


class AbstractTiltingCover(RfxtrxCommandEntity, CoverEntity):
    """Representation of a RFXtrx cover supporting tilt and, optionally, lift."""

    _device: rfxtrxmod.RollerTrolDevice | rfxtrxmod.RfyDevice | rfxtrxmod.LightingDevice

    def __init__(
        self,
        device: rfxtrxmod.RFXtrxDevice,
        device_id: DeviceTuple,
        entity_info: dict[str, Any],
        event: rfxtrxmod.RFXtrxEvent = None,
    ) -> None:
        """Initialize the AbstractTiltingCover RFXtrx cover device."""

        super().__init__(device, device_id, event)

        self._venetian_blind_mode = entity_info.get(CONF_VENETIAN_BLIND_MODE)
        self._attr_is_closed: bool | None = True
        self._attr_device_class = CoverDeviceClass.BLIND

        self._attr_current_cover_tilt_position = 0
        self._attr_current_cover_position = 0

        self._attr_supported_features = (
            CoverEntityFeature.OPEN |
            CoverEntityFeature.CLOSE |
            CoverEntityFeature.SET_POSITION |
            CoverEntityFeature.STOP
        )

        self._attr_supported_features |= (
            CoverEntityFeature.OPEN_TILT
            | CoverEntityFeature.CLOSE_TILT
            | CoverEntityFeature.SET_TILT_POSITION
            | CoverEntityFeature.STOP_TILT
        )

        self._myattr_is_lift_on_open = False
        self._myattr_repetitions = entity_info.get(CONF_SIGNAL_REPETITIONS, 1)
        self._myattr_repetition_delay = entity_info.get(CONF_SIGNAL_REPETITIONS_DELAY_MS, DEF_SIGNAL_REPETITIONS_DELAY_MS) / 1000
        self._myattr_close_secs = entity_info.get(CONF_CLOSE_SECONDS, DEF_CLOSE_SECONDS)
        self._myattr_open_secs = entity_info.get(CONF_OPEN_SECONDS, DEF_OPEN_SECONDS)
        self._myattr_sync_secs = entity_info.get(CONF_SYNC_SECONDS, DEF_SYNC_SECONDS) / 1000
        self._myattr_custom_icon = entity_info.get(CONF_CUSTOM_ICON, DEF_CUSTOM_ICON)
        self._myattr_colour_open = entity_info.get(CONF_COLOUR_ICON, DEF_COLOUR_ICON)
        self._myattr_partial_is_closed = entity_info.get(CONF_PARTIAL_CLOSED, DEF_PARTIAL_CLOSED)

        self._myattr_tilt_pos1_secs = entity_info.get(CONF_TILT_POS1_MS, DEF_TILT_POS1_MS) / 1000
        self._myattr_tilt_pos2_secs = entity_info.get(CONF_TILT_POS2_MS, DEF_TILT_POS2_MS) / 1000

        self._myattr_is_raised = True
        self._myattr_tilt_step = TILT_MIN_STEP


    async def async_added_to_hass(self) -> None:
        """Restore device state."""
        await super().async_added_to_hass()

        if self._event is None:
            old_state = await self.async_get_last_state()
            if old_state is not None:
                old_pos = old_state.attributes['current_position']
                old_tilt_pos = old_state.attributes['current_tilt_position']
                _LOGGER.info("async_added_to_hass: old_pos = " + str(old_pos) + " old_tilt = " + str(old_tilt_pos))

                if old_pos < 50:
                    self._set_position(False, self._tilt_to_steps(old_tilt_pos))
                else:
                    self._set_position(True, 0)


    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        if not(self._is_moving):
            if ATTR_POSITION in kwargs:
                position = kwargs[ATTR_POSITION]
                if position > 85:
                    _LOGGER.debug("async_set_cover_position: RAISING cover")
                    await self._async_raise_blind()
                    await self._async_wait_and_set_position(self._myattr_open_secs, True, TILT_MIN_STEP)
                elif position < 15:
                    _LOGGER.debug("async_set_cover_position: closing cover to CLOSED")
                    await self._async_tilt_blind_to_step(TILT_MIN_STEP)
                else:
                    _LOGGER.debug("async_set_cover_position: closing cover to OPEN")
                    await self._async_tilt_blind_to_step(TILT_MID_STEP)
        else:
            _LOGGER.debug("async_set_cover_position: cover is in motion - ignoring")


    async def async_toggle(self, **kwargs: Any) -> None:
        """Toggle the entity."""
        if self._is_moving:
            _LOGGER.debug("toggle: cover is in motion - ignoring")
        else:
            if self._myattr_is_raised or self._myattr_tilt_step != TILT_MIN_STEP:
                await self._async_tilt_blind_to_step(TILT_MIN_STEP)
            else:
                await self._async_tilt_blind_to_step(TILT_MID_STEP)


    async def async_open_cover(self, **kwargs: Any) -> None:
        """Move the cover up."""
        if not(self._is_moving):
            _LOGGER.debug("async_open_cover: tilting cover to open")
            await self._async_tilt_blind_to_step(TILT_MID_STEP)
        else:
            _LOGGER.debug("async_open_cover: cover is in motion - ignoring")


    async def async_close_cover(self, **kwargs: Any) -> None:
        """Move the cover down."""
        if not(self._is_moving):
            _LOGGER.debug("async_close_cover: tilting cover to closed")
            await self._async_tilt_blind_to_step(TILT_MIN_STEP)
        else:
            _LOGGER.debug("async_close_cover: cover is in motion - ignoring")


    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        if not(self._is_moving):
            _LOGGER.debug("async_stop_cover: cover is not in motion - ignoring")
        else:
            _LOGGER.debug("async_stop_cover: stopping cover")
            self._attr_is_closing = False
            self._attr_is_opening = False
            self.async_write_ha_state()


    async def async_toggle_tilt(self, **kwargs: Any) -> None:
        """Toggle the entity."""
        await self.async_toggle(**kwargs)


    async def async_open_cover_tilt(self, **kwargs: Any) -> None:
        """Tilt the cover up."""
        if not(self._is_moving):
            _LOGGER.debug("async_open_cover_tilt: increasing tilt pos")
            await self._async_tilt_blind_to_step(self._myattr_tilt_step + 1)
        else:
            _LOGGER.debug("async_open_cover_tilt: cover is in motion - ignoring")


    async def async_close_cover_tilt(self, **kwargs: Any) -> None:
        """Tilt the cover down."""
        if not(self._is_moving):
            _LOGGER.debug("async_close_cover_tilt: decreasing tilt pos")
            await self._async_tilt_blind_to_step(self._myattr_tilt_step - 1)
        else:
            _LOGGER.debug("async_close_cover_tilt: cover is in motion - ignoring")


    async def async_set_cover_tilt_position(self, **kwargs: Any) -> None:
        """Move the cover tilt to a specific position."""
        if not(self._is_moving):
            if ATTR_TILT_POSITION in kwargs:
                tilt_position = self._tilt_to_steps(kwargs[ATTR_TILT_POSITION])

                _LOGGER.debug("async_set_cover_tilt_position: setting position " + str(tilt_position))
                await self._async_tilt_blind_to_step(tilt_position)
        else:
            _LOGGER.debug("async_set_cover_tilt_position: cover is in motion - ignoring")


    async def async_stop_cover_tilt(self, **kwargs: Any) -> None:
        """Stop the cover tilt."""
        if not(self._is_moving):
            _LOGGER.debug("async_stop_cover_tilt: cover is not in motion - ignoring")
        else:
            _LOGGER.debug("async_stop_cover_tilt: stopping cover tilt")
            self._attr_is_closing = False
            self._attr_is_opening = False
            self.async_write_ha_state()


    async def async_update_cover_position(self, **kwargs) -> None:
        """Update the internal position."""
        _LOGGER.info("Invoked async_update_cover_position")

        old_cover_position = self._attr_current_cover_position
        old_cover_tilt_position = self._attr_current_cover_tilt_position
        old_is_closing = self._attr_is_closing
        old_is_opening = self._attr_is_opening

        if ATTR_POSITION in kwargs:
            self._attr_current_cover_position = kwargs[ATTR_POSITION]
            self._myattr_is_raised = self._attr_current_cover_position > 80

        if ATTR_TILT_POSITION in kwargs:
            self._attr_current_cover_tilt_position = kwargs[ATTR_TILT_POSITION]
            self._myattr_tilt_step = self._tilt_to_steps(self._attr_current_cover_tilt_position)

        self._set_position(self._myattr_is_raised, self._myattr_tilt_step)

        if ATTR_STATE in kwargs:
            state = kwargs[ATTR_STATE]
            if state == STATE_CLOSING:
                self._attr_is_closing = True
            elif state == STATE_OPENING:
                self._attr_is_opening = True

        if old_cover_position != self._attr_current_cover_position or \
                old_cover_tilt_position != self._attr_current_cover_tilt_position or \
                old_is_closing != self._attr_is_closing or \
                old_is_opening != self._attr_is_opening:
            _LOGGER.debug("async_update_cover_position: written new state")
            self.async_write_ha_state()


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
    def entity_picture(self):
        if self._myattr_custom_icon:
            icon = self._entity_picture

            _LOGGER.debug("Returned icon attribute = " + icon)
            return icon
    
        return None
    

    @property
    def _is_moving(self) -> bool | None:
        return self._attr_is_opening or self._attr_is_closing


    def _tilt_to_steps(self, tilt_position) -> int:
        return int(round(tilt_position/ (100 / TILT_MAX_STEP)))
    

    def _steps_to_tilt(self, tilt_position) -> int:
        return int(round((tilt_position / TILT_MAX_STEP) * 100))


    def _set_position(self, is_raised, tilt_step) -> None:
        self._myattr_is_raised = is_raised

        if tilt_step < TILT_MIN_STEP:       
            self._myattr_tilt_step = TILT_MIN_STEP
        elif tilt_step >= TILT_MAX_STEP:       
            self._myattr_tilt_step = TILT_MAX_STEP
        else:       
            self._myattr_tilt_step = tilt_step

        """Translate my lift position to HA position
        None is unknown, 0 is closed, 100 is fully open."""

        """Translate my tilt position to HA position
        None is unknown, 0 is closed, 100 is fully open."""

        if self._myattr_is_raised:
            self._attr_is_closed = False
            self._attr_current_cover_position = 100
            self._attr_current_cover_tilt_position = 100
        elif self._myattr_tilt_step == TILT_MIN_STEP or self._myattr_tilt_step >= TILT_MAX_STEP:
            self._attr_is_closed = True
            self._attr_current_cover_position = 0
            self._attr_current_cover_tilt_position = 0
        elif self._myattr_tilt_step == TILT_MID_STEP:
            self._attr_is_closed = False
            self._attr_current_cover_position = 30
            self._attr_current_cover_tilt_position = self._steps_to_tilt(self._myattr_tilt_step)
        else:
            self._attr_is_closed = self._myattr_partial_is_closed
            self._attr_current_cover_position = 15
            self._attr_current_cover_tilt_position = self._steps_to_tilt(self._myattr_tilt_step)

        self._attr_is_opening = False
        self._attr_is_closing = False

        _LOGGER.debug("_set_position; set new position - raised = " + str(self._myattr_is_raised) + " tilt = " + str(self._myattr_tilt_step))


    async def _async_wait_and_set_position(self, delay, is_raised, tilt_step) -> None:
        if delay > 0:
            _LOGGER.info("_async_wait_and_set_position: Waiting secs = " + str(delay))

            if is_raised and not(self._myattr_is_raised):
                self._attr_is_opening = True
            elif not(is_raised) and self._myattr_is_raised:
                self._attr_is_closing = True
            elif tilt_step == 0 or tilt_step >= TILT_MAX_STEP:
                self._attr_is_closing = True
            else:
                self._attr_is_opening = True
            self.async_write_ha_state()

            await asyncio.sleep(delay)

        # If the blind is still closing then we have finished. Otherwise assume we were interrupted
        if self._is_moving:
            _LOGGER.info("_async_wait_and_set_position: Finished blind action, setting state")
            self._set_position(is_raised, tilt_step)
            self.async_write_ha_state()
        else:
            _LOGGER.info(
                "_async_wait_and_set_position: Finished blind action, state not as expected - not saving new state")


    @property
    def _entity_picture(self) -> str | None:
        """Return the icon property."""
        raise Exception("_entity_picture has not been implemented")


    async def _async_raise_blind(self):
        """Lift the cover."""
        _LOGGER.info("Invoked _async_raise_blind")
        raise Exception("_async_raise_blind has not been implemented")


    async def _async_lower_blind(self):
        """Lower the cover."""
        _LOGGER.info("Invoked _async_lower_blind")
        raise Exception("_async_lower_blind has not been implemented")


    async def _async_stop_blind(self):
        """Stop the cover."""
        _LOGGER.info("Invoked _async_stop_blind")
        raise Exception("_async_stop_blind has not been implemented")
    

    async def _async_tilt_blind_to_step(self, tilt_step):
        """Move the cover tilt to a preset position."""
        _LOGGER.info("Invoked _async_tilt_blind_to_mid_step; tilt_step = " + str(tilt_step))
        raise Exception("_async_tilt_blind_to_mid_step has not been implemented")


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