"""Light support for switch entities."""
from __future__ import annotations
import logging
import asyncio
import time
from typing import (
    Any,
    Callable,
    Optional,
    Sequence,
    cast
)
from .. import RfxtrxCommandEntity
from homeassistant.components.cover import (
    DEVICE_CLASS_BLIND,
    ATTR_POSITION
)
from homeassistant.components.cover import CoverEntity
from homeassistant.const import (
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING
)
from homeassistant.core import callback

from .const import (
    CONF_CLOSE_SECONDS,
    CONF_OPEN_SECONDS,
    CONF_SYNC_SECONDS,
    CONF_CUSTOM_ICON,
    CONF_COLOUR_ICON,
    CONF_PARTIAL_CLOSED,
    CONF_SIGNAL_REPETITIONS,
    CONF_SIGNAL_REPETITIONS_DELAY_MS,
    DEF_CLOSE_SECONDS,
    DEF_OPEN_SECONDS,
    DEF_SYNC_SECONDS,
    DEF_CUSTOM_ICON,
    DEF_COLOUR_ICON,
    DEF_PARTIAL_CLOSED,
    DEF_SIGNAL_REPETITIONS_DELAY_MS,
    SUPPORT_OPEN,
    SUPPORT_CLOSE,
    SUPPORT_SET_POSITION,
    SUPPORT_STOP,
    ATTR_MOVEMENT_ALLOWED

)

ICON_PATH = "/local/rfxtrx/roller"

CMD_SOMFY_STOP = 0x00
CMD_SOMFY_UP = 0x01
CMD_SOMFY_DOWN = 0x03

# mypy: allow-untyped-calls, allow-untyped-defs, no-check-untyped-defs

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Blinds Control"
DEVICE_TYPE = "Somfy Roller"

AUTO_STEP_CLICK_SEC = 2
COMMAND_DEBOUNCE_SEC = 0.5

# Values returned for blind position in various states
BLIND_POS_OPEN = 100
BLIND_POS_STOPPED = 50
BLIND_POS_CLOSED = 0

# Represents a cover entity that has slats - either vertical or horizontal. Thios differs from a cover in that:
# - Opening the blind tilts the slats to allow light. Not moving the blind out of the window
# - Closing the blind requires the blind to be fully lowered into the window and the slats to be in a tilted position
#
# Properties:
#   Config:
#     _blindMaxSteps - number of steps to tilt the blind from fully tilted to the mid position
#     _blindMidSteps - number of steps to tilt the blind from fully tilted to the mid position
#     _hasMidCommand - Boolean - TRUE if the blind has an explicit command for the mid position
#     _syncMidPos - boolean - TRUE if we should send a "mid" position command each time we cross the mid position
#     _blindCloseSecs - number of seconds to wait for the blind to fully close from fully open position
#     _blindOpenSecs - number of seconds to wait for the blind to fully open from fully closed position
#   State:
#     _lift_position - reported position of the blind
#     _tilt_step - step posiotion of the tilt - related to the _tilt_step
#     _state - what the blind is curfrently doing - STATE_OPEN/STATE_OPENING/STATE_CLOSED/STATE_CLOSING
#


class SomfyRollerBlind(RfxtrxCommandEntity, CoverEntity):
    """Representation of a RFXtrx cover supporting tilt and, optionally, lift."""

    def __init__(self, device, device_id, entity_info, event=None):
        self._blindCloseSecs = entity_info.get(
            CONF_CLOSE_SECONDS, DEF_CLOSE_SECONDS)
        self._blindOpenSecs = entity_info.get(
            CONF_OPEN_SECONDS, DEF_OPEN_SECONDS)
        self._blindSyncSecs = entity_info.get(
            CONF_SYNC_SECONDS, DEF_SYNC_SECONDS)
        self._signalRepetitions = entity_info[CONF_SIGNAL_REPETITIONS]
        self._signalRepetitionsDelay = entity_info.get(
            CONF_SIGNAL_REPETITIONS_DELAY_MS, DEF_SIGNAL_REPETITIONS_DELAY_MS) / 1000
        self._customIcon = entity_info.get(CONF_CUSTOM_ICON, DEF_CUSTOM_ICON)
        self._colourIcon = entity_info.get(CONF_COLOUR_ICON, DEF_COLOUR_ICON)
        self._partialClosed = entity_info.get(
            CONF_PARTIAL_CLOSED, DEF_PARTIAL_CLOSED)
        self._allowMovement = True

        super().__init__(device, device_id, event)

        _LOGGER.info("New somfy roller cover config," +
                     " signal_repetitions=" + str(self._signalRepetitions) +
                     " signal_repetitions_delay=" + str(self._signalRepetitionsDelay) +
                     " openSecs=" + str(self._blindOpenSecs) +
                     " closeSecs=" + str(self._blindCloseSecs) +
                     " syncSecs=" + str(self._blindSyncSecs))

    async def async_added_to_hass(self):
        """Restore device state."""
        _LOGGER.debug("Called async_added_to_hass")

        self._lift_position = BLIND_POS_OPEN
        self._state = STATE_OPEN
        self._lastClosed = False
        self._lastCommandTime = time.time()

        await super().async_added_to_hass()

        if self._event is None:
            old_state = await self.async_get_last_state()
            if old_state is not None:
                if 'current_position' in old_state.attributes:
                    _LOGGER.info("State = " + str(old_state))
                    self._lift_position = old_state.attributes['current_position']
                    if self._lift_position >= BLIND_POS_OPEN:
                        self._state = STATE_OPEN
                        self._lift_position = BLIND_POS_OPEN
                        self._lastClosed = False
                    elif self._lift_position <= BLIND_POS_CLOSED:
                        self._state = STATE_CLOSED
                        self._lift_position = BLIND_POS_CLOSED
                        self._lastClosed = True
                    else:
                        self._state = STATE_OPEN
                        self._lift_position = BLIND_POS_STOPPED
                        self._lastClosed = False

                    _LOGGER.info("Recovered state=" + str(self._state) +
                                 " position=" + str(self._lift_position))

    @ property
    def available(self) -> bool:
        """Return true if device is available - not sure what makes it unavailable."""
        return True

    @ property
    def current_cover_position(self):
        """Return the current cover position property."""
        if self._lift_position <= BLIND_POS_CLOSED:
            position = BLIND_POS_CLOSED
        elif self._lift_position >= BLIND_POS_OPEN:
            position = BLIND_POS_OPEN
        else:
            position = BLIND_POS_STOPPED

        _LOGGER.debug(
            "Returned current_cover_position attribute = " + str(position))
        return position

    @ property
    def is_opening(self):
        """Return the is_opening property."""
        opening = self._state == STATE_OPENING
        _LOGGER.debug("Returned is_opening attribute = " + str(opening))
        return opening

    @ property
    def is_closing(self):
        """Return the is_closing property."""
        closing = self._state == STATE_CLOSING
        _LOGGER.debug("Returned is_closing attribute = " + str(closing))
        return closing

    @ property
    def is_closed(self):
        """Return the is_closed property."""
        closed = self._state == STATE_CLOSED
        _LOGGER.debug("Returned is_closed attribute = " + str(closed))
        return closed

    @ property
    def device_class(self):
        """Return the device class."""
        _LOGGER.debug("Returned device_class attribute")
        return DEVICE_CLASS_BLIND

    @ property
    def supported_features(self):
        """Flag supported features."""
        _LOGGER.debug("Returned supported_features attribute")
        features = SUPPORT_CLOSE | SUPPORT_OPEN | SUPPORT_STOP | SUPPORT_SET_POSITION
        return features

    @ property
    def should_poll(self):
        """No polling needed for a RFXtrx switch."""
        return False

    @ property
    def assumed_state(self):
        """Return true if unable to access real state of entity."""
        return False

    @property
    def entity_picture(self):
        """Return the icon property."""
        if self._customIcon:
            if self.is_opening or self.is_closing:
                icon = "move.svg"
                closed = self._lastClosed
            else:
                pos = self._lift_position
                if pos <= BLIND_POS_CLOSED:
                    icon = "00.svg"
                    closed = True
                elif pos >= BLIND_POS_OPEN:
                    icon = "99.svg"
                    closed = False
                else:
                    icon = "50.svg"
                    closed = self._partialClosed
            if self._colourIcon and not(closed):
                icon = ICON_PATH + "/active/" + icon
            else:
                icon = ICON_PATH + "/inactive/" + icon
            self._lastClosed = closed
            _LOGGER.debug("Returned icon attribute = " + icon)
        else:
            icon = None
        return icon

    # Service operations

    # Requests to open the blind. In practice we do not open then blind, we will instead tilt to the
    # mid position. If the blind is in motion then is ignored.

    async def async_open_cover(self, **kwargs):
        """Open the cover by selecting the mid position."""
        _LOGGER.info("Invoked async_open_cover")

        await self._async_set_cover_position(BLIND_POS_OPEN)

    # Requests to close the blind. If the blind is in motion then is ignored. Otherwise always close the blind so
    # that we can be sure the blind is closed.

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        _LOGGER.info("Invoked async_close_cover")

        await self._async_set_cover_position(BLIND_POS_CLOSED)

    # Requests to stop the blind. If the blind is not in motion then is ignored. Otherwise assume the blind
    # is in a mid position.

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        _LOGGER.info("Invoked async_stop_cover")

        if self._state == STATE_CLOSING or self._state == STATE_OPENING:
            # Stop the blind
            _LOGGER.info("Blind is in motion - marking as partially closed")
            await self._async_do_stop_blind()
            await self._set_state(STATE_OPEN, BLIND_POS_STOPPED)
        else:
            _LOGGER.info("Blind is stationary - ignoring the request")

    # Requests to set the position of the blind. If the blind is in motion then is ignored. We will use this
    # to allow the blind to actually be opened. If the position is after the mid point then change into a close
    # command which will ensure the blind is closed. Otherwise set he state to OPENING and open the blind.
    # Then after a delay and marks as OPEN if the blind is still OPENING.

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        _LOGGER.info("Invoked async_set_cover_position")

        if self._ignore_bounce():
            if ATTR_POSITION in kwargs:
                await self._async_set_cover_position(kwargs[ATTR_POSITION])

    # New service operations

    async def async_update_cover_position(self, **kwargs):
        """Update the internal position."""
        _LOGGER.info("Invoked async_update_cover_position")

        if ATTR_POSITION in kwargs:
            self._lift_position = kwargs[ATTR_POSITION]

            if self._lift_position < BLIND_POS_STOPPED:
                self._lift_position = BLIND_POS_CLOSED
                state = STATE_CLOSED
            elif self._lift_position > BLIND_POS_STOPPED:
                self._lift_position = BLIND_POS_OPEN
                state = STATE_CLOSED
            else:
                self._lift_position = BLIND_POS_STOPPED
                state = STATE_OPEN

        await self._set_state(state, self._lift_position)

    # Action functions

    async def _async_set_cover_position(self, position):
        """Move the cover to a specific position."""
        _LOGGER.info("Invoked _async_set_cover_position")

        if self._blind_is_stationary():
            if position <= BLIND_POS_CLOSED:
                _LOGGER.info("Closing blind with a delay...")
                await self._async_do_close_blind()
                await self._wait_and_set_state(self._blindCloseSecs, STATE_CLOSING, STATE_CLOSED, BLIND_POS_CLOSED)
            elif position >= BLIND_POS_OPEN:
                _LOGGER.info("Opening blind with a delay...")
                await self._async_do_open_blind()
                await self._wait_and_set_state(self._blindOpenSecs, STATE_OPENING, STATE_OPEN, BLIND_POS_OPEN)
            else:
                _LOGGER.info("Setting home pos on blind with a delay...")
                await self._async_do_set_to_mid()
                await self._wait_and_set_state(self._blindOpenSecs, STATE_OPENING, STATE_OPEN, BLIND_POS_STOPPED)

    # Helper functions

    async def async_set_movement_allowed(self, **kwargs):
        """Set whether or not updates are allowed"""
        _LOGGER.info("Invoked async_set_movement_allowed")

        if ATTR_MOVEMENT_ALLOWED in kwargs:
            self._allowMovement = kwargs[ATTR_MOVEMENT_ALLOWED]
            _LOGGER.info("Movement allowed = " + str(self._allowMovement))

    async def _set_state(self, newState, newLift):
        self._state = newState
        self._lift_position = newLift
        self.async_write_ha_state()

    async def _wait_and_set_state(self, delay, state, newState, newLift):
        if delay > 0:
            _LOGGER.info("Waiting secs = " + str(delay))
            await asyncio.sleep(delay)

        # If the blind is still moving then we have finished. Otherwise assume we were interrupted
        if self._state == state:
            _LOGGER.info("Finished blind action, setting state = " + newState)
            await self._set_state(newState, newLift)
        else:
            _LOGGER.info(
                "Finished blind action, state not as expected; " + self._state)

    def _ignore_bounce(self):
        last = self._lastCommandTime
        self._lastCommandTime = time.time()
        if (self._lastCommandTime - last) <= COMMAND_DEBOUNCE_SEC:
            _LOGGER.info("Duplicate command - will ignore request")
            return False
        else:
            return True

    def _blind_is_stationary(self):
        if self._state == STATE_OPENING or self._state == STATE_CLOSING:
            _LOGGER.info("Blind is in motion - will ignore request")
            return False
        else:
            return True

    def _motion_allowed(self):
        if self._allowMovement:
            return True
        else:
            _LOGGER.debug("Blind motion is disabled")
            return False

    async def _async_send_command(self, cmd):
        """Send a command to the blind"""
        _LOGGER.info("LOW-LEVEL SENDING BLIND COMMAND - " + str(cmd))
        if self._signalRepetitions >= 2:
            for _ in range(self._signalRepetitions - 1):
                await self._async_send(self._device.send_command, cmd)
                await asyncio.sleep(self._signalRepetitionsDelay)
        await self._async_send(self._device.send_command, cmd)

    # Handle updates from cover device

    async def async_update(self):
        """Query the switch in this light switch and determine the state."""
        _LOGGER.debug("Invoked async_update")

    def _apply_event(self, event):
        """Apply command from rfxtrx."""
        _LOGGER.debug("Invoked _apply_event")
        super()._apply_event(event)

    @ callback
    def _handle_event(self, event, device_id):
        """Check if event applies to me and update."""
        _LOGGER.debug("Invoked _handle_event")
        if device_id != self._device_id:
            return

        self._apply_event(event)
        self.async_write_ha_state()

    # --------------------------------------------------------------------------------
    # Implementations for device specific actions

    # Replace with action to close blind
    async def _async_do_close_blind(self):
        """Callback to close the blind"""
        _LOGGER.info("LOW-LEVEL CLOSING BLIND")
        await self._set_state(STATE_CLOSING, BLIND_POS_STOPPED)
        await self._async_send_command(CMD_SOMFY_DOWN)

    # Replace with action to open blind
    async def _async_do_open_blind(self):
        """Callback to open the blind"""
        _LOGGER.info("LOW-LEVEL OPENING BLIND")
        await self._set_state(STATE_OPENING, BLIND_POS_STOPPED)
        await self._async_send_command(CMD_SOMFY_UP)

    # Replace with action to stop blind
    async def _async_do_stop_blind(self):
        """Callback to stop the blind"""
        _LOGGER.info("LOW-LEVEL STOPPING BLIND")
        await self._async_send_command(CMD_SOMFY_STOP)

    # Replace with action to tilt blind to mid position
    async def _async_do_set_to_mid(self):
        """Callback to tilt the blind to mid"""
        _LOGGER.info("LOW-LEVEL SETTING BLIND TO MID")
        await self._set_state(STATE_OPENING, BLIND_POS_STOPPED)
        await self._async_send_command(CMD_SOMFY_STOP)
