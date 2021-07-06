"""Light support for switch entities."""
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
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_OPEN_TILT,
    SUPPORT_CLOSE_TILT,
    SUPPORT_STOP_TILT,
    SUPPORT_STOP,
    SUPPORT_SET_POSITION,
    SUPPORT_SET_TILT_POSITION,
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverEntity
)
from homeassistant.const import (
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING
)
from homeassistant.core import callback
from .const import ATTR_AUTO_REPEAT

# Values returned for blind position in various states
BLIND_POS_OPEN = 100
BLIND_POS_TILTED_MAX = 99
BLIND_POS_STOPPED = 50
BLIND_POS_TILTED_MIN = 1
BLIND_POS_CLOSED = 0

# Values returned for tilt position in various states
TILT_POS_CLOSED_MAX = 100
TILT_POS_OPEN = 50
TILT_POS_CLOSED_MIN = 0


# mypy: allow-untyped-calls, allow-untyped-defs, no-check-untyped-defs

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Blinds Control"

AUTO_STEP_CLICK_SEC = 2
COMMAND_DEBOUNCE_SEC = 0.5


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
class AbstractTiltingCover(RfxtrxCommandEntity, CoverEntity):
    """Representation of a RFXtrx cover supporting tilt and, optionally, lift."""

    def __init__(self, device, device_id, signal_repetitions, event, midSteps, hasMid, hasLift, liftOnOpen, syncMid, openSecs, closeSecs, syncMs, repeatStepMs):
        self._syncMidPos = syncMid
        self._hasMidCommand = hasMid
        self._hasLift = hasLift
        self._liftOnOpen = liftOnOpen
        self._blindMidSteps = midSteps
        self._blindCloseSecs = closeSecs
        self._blindOpenSecs = openSecs
        self._blindSyncSecs = syncMs / 1000
        self._blindRepeatStepSecs = repeatStepMs / 1000
        self._blindMaxSteps = int(self._blindMidSteps * 2)

        super().__init__(device, device_id, signal_repetitions, event)

        _LOGGER.info("New tilting cover config," +
                     " signal_repetitions=" + str(signal_repetitions) +
                     " midSteps=" + str(self._blindMidSteps) +
                     " maxSteps=" + str(self._blindMaxSteps) +
                     " openSecs=" + str(self._blindOpenSecs) +
                     " closeSecs=" + str(self._blindCloseSecs) +
                     " syncSecs=" + str(self._blindSyncSecs) +
                     " stepSecs=" + str(self._blindRepeatStepSecs) +
                     " hasLift=" + str(self._hasLift) +
                     " liftOnOpen=" + str(self._liftOnOpen) +
                     " hasMidCommand=" + str(self._hasMidCommand) +
                     " syncMidPos=" + str(self._syncMidPos))

    async def async_added_to_hass(self):
        """Restore device state."""
        _LOGGER.debug("Called async_added_to_hass")

        self._lift_position = BLIND_POS_OPEN
        self._tilt_step = 0
        self._state = STATE_OPEN
        self._autoStepActive = False
        self._autoStepDirection = 0
        self._lastCommandTime = time.time()

        await super().async_added_to_hass()

        if self._event is None:
            old_state = await self.async_get_last_state()
            if old_state is not None:
                if 'current_tilt_position' in old_state.attributes:
                    _LOGGER.info("State = " + str(old_state))
                    self._lift_position = old_state.attributes['current_position']
                    tilt = old_state.attributes['current_tilt_position']
                    if not(self._hasLift) or self._lift_position <= BLIND_POS_TILTED_MAX:
                        self._state = STATE_CLOSED
                        self._lift_position = BLIND_POS_CLOSED
                        self._tilt_step = self._tilt_to_steps(tilt)
                    else:
                        self._state = STATE_OPEN
                        self._lift_position = BLIND_POS_OPEN
                        self._tilt_step = self._blindMidSteps

                    _LOGGER.info("Recovered state=" + str(self._state) +
                                 " position=" + str(self._lift_position) +
                                 " tilt=" + str(self._tilt_step))

    @ property
    def available(self) -> bool:
        """Return true if device is available - not sure what makes it unavailable."""
        return True

    @ property
    def current_cover_tilt_position(self):
        """Return the current tilt position property."""
        if self._state == STATE_OPEN:
            tilt = TILT_POS_OPEN
        elif self._tilt_step == 0:
            tilt = TILT_POS_CLOSED_MIN
        elif self._tilt_step == self._blindMidSteps:
            tilt = TILT_POS_OPEN
        elif self._tilt_step >= self._blindMaxSteps:
            tilt = TILT_POS_CLOSED_MAX
        else:
            tilt = self._steps_to_tilt(self._tilt_step)

        _LOGGER.debug(
            "Returned current_cover_tilt_step attribute = " + str(tilt))
        return tilt

    @ property
    def current_cover_position(self):
        """Return the current cover position property."""
        if self._lift_position == BLIND_POS_CLOSED:
            if self._tilt_step <= 0 or self._tilt_step >= self._blindMaxSteps:
                position = BLIND_POS_CLOSED
            else:
                position = BLIND_POS_TILTED_MIN
        elif self._lift_position == BLIND_POS_OPEN:
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
        closed = self._state == STATE_CLOSED and (
            self._tilt_step <= 0 or self._tilt_step >= self._blindMaxSteps)
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
        features = SUPPORT_CLOSE | SUPPORT_OPEN | SUPPORT_STOP | SUPPORT_OPEN_TILT | SUPPORT_CLOSE_TILT | SUPPORT_STOP_TILT | SUPPORT_SET_TILT_POSITION | SUPPORT_SET_POSITION
        return features

    @ property
    def should_poll(self):
        """No polling needed for a RFXtrx switch."""
        return False

    @ property
    def assumed_state(self):
        """Return true if unable to access real state of entity."""
        return False

    # Service operations

    # Requests to open the blind. In practice we do not open then blind, we will instead tilt to the
    # mid position. If the blind is in motion then is ignored.

    async def async_open_cover(self, **kwargs):
        """Open the cover by selecting the mid position."""
        _LOGGER.info("Invoked async_open_cover")

        if self._liftOnOpen:
            await self._async_set_cover_position(BLIND_POS_OPEN)
        else:
            await self._async_tilt_blind_to_mid_step()

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

        if not self._hasLift:
            _LOGGER.info("Blind does not lift - ignoring the request")
        elif self._state == STATE_CLOSING or self._state == STATE_OPENING:
            # Stop the blind
            _LOGGER.info("Blind is in motion - marking as partially closed")
            await self._async_do_stop_blind()
            await self._set_state(STATE_OPEN, BLIND_POS_STOPPED, 0)
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

    # Request to open the blind with a tilt

    async def async_open_cover_tilt(self, **kwargs):
        """Open the cover tilt."""
        _LOGGER.info("Invoked async_open_cover_tilt")

        if self._hasMidCommand:
            await self._async_tilt_blind_to_mid_step()
        else:
            await self._async_set_cover_tilt_step(self._blindMidSteps)

    async def async_close_cover_tilt(self, **kwargs):
        """Close the cover tilt."""
        _LOGGER.info("Invoked async_close_cover_tilt")

        await self._async_set_cover_tilt_step(0)

    async def async_stop_cover_tilt(self, **kwargs):
        """Stop the cover."""
        _LOGGER.info("Invoked async_stop_cover_tilt")

        if self._autoStepActive:
            _LOGGER.info("Disabled auto advance of cover_tilt")
            self._autoStepDirection = 0
            self._autoStepActive = False

    async def async_set_cover_tilt_position(self, **kwargs):
        """Move the cover tilt to a specific position."""
        _LOGGER.info("Invoked async_set_cover_tilt_position")

        if self._blind_is_stationary() and self._ignore_bounce():
            if ATTR_TILT_POSITION in kwargs:
                tilt_position = kwargs[ATTR_TILT_POSITION]
            else:
                tilt_position = TILT_POS_OPEN

            if self._state != STATE_CLOSED or self._lift_position != BLIND_POS_CLOSED:
                if tilt_position == 0:
                    _LOGGER.info(
                        "Blind is not closed - switching to close operation")
                    await self._async_set_cover_tilt_step(0)
                else:
                    _LOGGER.info(
                        "Blind is not closed - switching to mid position operation")
                    await self._async_tilt_blind_to_mid_step()
            else:
                tilt = self._tilt_to_steps(tilt_position)
                if tilt == self._blindMidSteps:
                    _LOGGER.info(
                        "Tilt is to mid point - switching to mid position operation")
                    await self._async_tilt_blind_to_mid_step()
                else:
                    await self._async_set_cover_tilt_step(tilt)

    # New service operations

    async def async_update_cover_position(self, **kwargs):
        """Update the internal position."""
        _LOGGER.info("Invoked async_update_cover_position")

        if ATTR_POSITION in kwargs:
            self._lift_position = kwargs[ATTR_POSITION]

        if ATTR_TILT_POSITION in kwargs:
            self._tilt_step = self._tilt_to_steps(kwargs[ATTR_TILT_POSITION])

        if self._lift_position <= BLIND_POS_TILTED_MIN:
            self._lift_position = BLIND_POS_CLOSED
            state = STATE_CLOSED
        else:
            state = STATE_OPEN

        await self._set_state(state, self._lift_position, self._tilt_step)

    async def async_increase_cover_tilt(self, **kwargs):
        """Increase the cover tilt step."""
        _LOGGER.info("Invoked async_increase_cover_tilt")

        repeating = kwargs[ATTR_AUTO_REPEAT] if ATTR_AUTO_REPEAT in kwargs else False
        if repeating:
            await self._async_repeat_tilt(1, self._blindMaxSteps)
        else:
            await self._async_repeat_tilt(1)

    async def async_decrease_cover_tilt(self, **kwargs):
        """Decrease the cover tilt step."""
        _LOGGER.info("Invoked async_decrease_cover_tilt")

        repeating = kwargs[ATTR_AUTO_REPEAT] if ATTR_AUTO_REPEAT in kwargs else False
        if repeating:
            await self._async_repeat_tilt(-1, self._blindMaxSteps)
        else:
            await self._async_repeat_tilt(-1)

    # Action functions

    async def _async_set_cover_position(self, position):
        """Move the cover to a specific position."""
        _LOGGER.info("Invoked _async_set_cover_position")

        if self._blind_is_stationary():
            if position < BLIND_POS_STOPPED:
                if self._state != STATE_CLOSED or self._lift_position != BLIND_POS_CLOSED:
                    delay = self._blindCloseSecs
                    await self._set_state(STATE_CLOSING, BLIND_POS_STOPPED, 0)
                else:
                    delay = self._blindSyncSecs / 2
                    self._state = STATE_CLOSING

                _LOGGER.info("Closing blind with a delay...")
                newDelay = await self._async_do_close_blind()
                if newDelay is not None:
                    delay = newDelay
                await self._wait_and_set_state(delay, STATE_CLOSING, STATE_CLOSED, BLIND_POS_CLOSED, 0)
            else:
                _LOGGER.info("Opening blind with a delay...")
                await self._set_state(STATE_OPENING, BLIND_POS_STOPPED, 0)
                newDelay = await self._async_do_open_blind()
                if newDelay is not None:
                    delay = newDelay
                await self._wait_and_set_state(self._blindOpenSecs, STATE_OPENING, STATE_OPEN, BLIND_POS_OPEN, self._blindMaxSteps)

    async def _async_set_cover_tilt_step(self, tilt_step, syncMidPos=True):
        """Move the cover tilt to a specific step."""
        _LOGGER.info("Invoked _async_set_cover_tilt_step")

        if self._blind_is_stationary():
            # If the tilt step is 0 or the blind is not already clopsed then close it
            if tilt_step == 0 or self._state != STATE_CLOSED or self._lift_position != BLIND_POS_CLOSED:
                await self._async_set_cover_position(BLIND_POS_CLOSED)
            else:
                steps = tilt_step - self._tilt_step

                _LOGGER.info(
                    "Tilting to required position;" +
                    " target=" + str(tilt_step) +
                    " from=" + str(self._tilt_step) +
                    " steps=" + str(steps))

                if steps != 0:
                    if self._syncMidPos and syncMidPos:
                        if steps < 0 and tilt_step < self._blindMidSteps and self._tilt_step > self._blindMidSteps:
                            steps = steps + \
                                (self._tilt_step - self._blindMidSteps)
                            _LOGGER.info(
                                "Tilt crosses mid point from high - syncing mid position; steps remaining=" + str(steps))
                            await self._async_tilt_blind_to_mid_step()
                        elif steps > 0 and tilt_step > self._blindMidSteps and self._tilt_step < self._blindMidSteps:
                            steps = steps - \
                                (self._blindMidSteps - self._tilt_step)
                            _LOGGER.info(
                                "Tilt crosses mid point from low - syncing mid position; steps remaining=" + str(steps))
                            await self._async_tilt_blind_to_mid_step()
                    self._tilt_step = await self._async_tilt_blind_to_step(steps, tilt_step)

                self.async_write_ha_state()

    async def _async_tilt_blind_to_mid_step(self):
        """Move the cover tilt to a preset position."""
        _LOGGER.info("Invoked _async_tilt_blind_to_mid_step")

        if not self._hasMidCommand:
            _LOGGER.error("Blind does not support a mid step command")
            raise Exception("tilt_blind_to_mid_step")
        elif self._blind_is_stationary():
            if self._state != STATE_CLOSED or self._lift_position != BLIND_POS_CLOSED:
                await self._set_state(STATE_OPENING, BLIND_POS_STOPPED, 0)
                delay = self._blindCloseSecs
            else:
                self._state = STATE_OPENING
                delay = self._blindSyncSecs

            _LOGGER.info("Setting mid position")
            newDelay = await self._async_do_tilt_blind_to_mid()
            if newDelay is not None:
                delay = newDelay
            await self._wait_and_set_state(delay, STATE_OPENING, STATE_CLOSED, BLIND_POS_CLOSED, self._blindMidSteps)

    async def _async_repeat_tilt(self, direction, maxSteps=0):
        if maxSteps <= 1:
            self._autoStepDirection = 0
            self._autoStepActive = False
            newTilt = self._tilt_step + direction
            if newTilt >= 0 and newTilt <= self._blindMaxSteps:
                await self._async_set_cover_tilt_step(newTilt)
        else:
            if not(self._autoStepActive) and self._autoStepDirection != direction:
                _LOGGER.info(
                    "Starting auto repeating tilt, direction=" + str(direction))
                self._autoStepDirection = direction
                self._autoStepActive = True
                steps = maxSteps
                while steps > 0 and self._autoStepActive and self._autoStepDirection == direction:
                    newTilt = self._tilt_step + self._autoStepDirection
                    if newTilt < 0 or newTilt > self._blindMaxSteps:
                        self._autoStepDirection = 0
                        self._autoStepActive = False
                    else:
                        await self._async_set_cover_tilt_step(newTilt)
                        _LOGGER.info("Waiting repeast secs = " +
                                     str(self._blindRepeatStepSecs))
                        await asyncio.sleep(self._blindRepeatStepSecs)
                        steps = steps - 1
                _LOGGER.info("Finished auto repeating tilt")
            else:
                _LOGGER.info("Ignoring duplicate auto repeating tilt")

    # Helper functions

    async def _set_state(self, newState, newLift, newTilt):
        self._state = newState
        self._lift_position = newLift
        self._tilt_step = newTilt
        self.async_write_ha_state()

    async def _wait_and_set_state(self, delay, state, newState, newLift, newTilt):
        if delay > 0:
            _LOGGER.info("Waiting secs = " + str(delay))
            await asyncio.sleep(delay)

        # If the blind is still closing then we have finished. Otherwise assume we were interrupted
        if self._state == state:
            _LOGGER.info("Finished blind action, setting state = " + newState)
            await self._set_state(newState, newLift, newTilt)
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

    def _tilt_to_steps(self, tilt):
        steps = min(round(tilt / 50 * self._blindMidSteps),
                    self._blindMaxSteps)
        return steps

    def _steps_to_tilt(self, steps):
        tilt = min(round(steps / self._blindMidSteps * 50), 100)
        return tilt

    async def _async_send_command(self, cmd):
        """Send a command to the blind"""
        _LOGGER.info("LOW-LEVEL SENDING BLIND COMMAND - " + str(cmd))
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

    # Replace this function if stepping the slats is not a linear operation
    async def _async_tilt_blind_to_step(self, steps, target):
        # Tilt blind
        for step in range(abs(steps)):
            if steps > 0:
                delay = await self._async_do_tilt_blind_forward()
            else:
                delay = await self._async_do_tilt_blind_back()

            if delay is not None:
                _LOGGER.info("Delaying for " + str(delay))
                await asyncio.sleep(delay)

        return target

    # Replace with action to close blind
    async def _async_do_close_blind(self):
        """Callback to close the blind"""
        _LOGGER.info("LOW-LEVEL CLOSING BLIND")

    # Replace with action to open blind
    async def _async_do_open_blind(self):
        """Callback to open the blind"""
        _LOGGER.info("LOW-LEVEL OPENING BLIND")

    # Replace with action to stop blind
    async def _async_do_stop_blind(self):
        """Callback to stop the blind"""
        _LOGGER.info("LOW-LEVEL STOPPING BLIND")

    # Replace with action to tilt blind to mid position
    async def _async_do_tilt_blind_to_mid(self):
        """Callback to tilt the blind to mid"""
        _LOGGER.info("LOW-LEVEL TILTING BLIND TO MID")

    # Replace with action to tilt blind forward one step
    async def _async_do_tilt_blind_forward(self):
        """Callback to tilt the blind forward"""
        _LOGGER.info("LOW-LEVEL TILTING BLIND FORWARD")

    # Replace with action to tilt blind backward one step
    async def _async_do_tilt_blind_back(self):
        """Callback to tilt the blind backward"""
        _LOGGER.info("LOW-LEVEL TILTING BLIND BACKWARD")
