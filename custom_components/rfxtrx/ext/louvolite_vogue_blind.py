import logging
from homeassistant.components.rfxtrx import CONF_SIGNAL_REPETITIONS
from .abs_tilting_cover import (
    AbstractTiltingCover,
    BLIND_POS_CLOSED
)
from homeassistant.const import (
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPENING
)
from .const import (
    CONF_CLOSE_SECONDS,
    CONF_OPEN_SECONDS,
    CONF_CUSTOM_ICON,
    DEF_CLOSE_SECONDS,
    DEF_OPEN_SECONDS,
    DEF_CUSTOM_ICON,
)

_LOGGER = logging.getLogger(__name__)

DEVICE_TYPE = "Vogue Vertical"

CMD_VOGUE_CLOSE_CW = 0x00
CMD_VOGUE_CLOSE_CCW = 0x01
CMD_VOGUE_45_DEGREES = 0x02
CMD_VOGUE_90_DEGREES = 0x03
CMD_VOGUE_135_DEGREES = 0x04

ICON_PATH = "/local/rfxtrx/vertical"

# Event 0919130400A1DB010000


class LouvoliteVogueBlind(AbstractTiltingCover):
    """Representation of a RFXtrx cover."""

    def __init__(self, device, device_id, entity_info, event=None):
        device.type_string = DEVICE_TYPE

        openSecs = entity_info.get(CONF_OPEN_SECONDS, DEF_OPEN_SECONDS)
        closeSecs = entity_info.get(CONF_CLOSE_SECONDS, DEF_CLOSE_SECONDS)

        super().__init__(device, device_id,
                         entity_info[CONF_SIGNAL_REPETITIONS], event,
                         2,  #  2 steps to mid point
                         True,  # Supports mid point
                         False,  # Does not support lift
                         entity_info.get(CONF_CUSTOM_ICON,
                                         DEF_CUSTOM_ICON),  # Use custom icon
                         False,  # Do not lift on open
                         False,  # Does not require sync on mid point
                         min(openSecs, closeSecs),  # Open time
                         max(openSecs, closeSecs),  # Close time
                         max(openSecs, closeSecs),  # Sync time ms
                         2000  # Ms for each step
                         )
        _LOGGER.info("Create Louvolite Vogue tilting blind " + str(device_id))

    @property
    def entity_picture(self):
        """Return the icon property."""
        if self._customIcon:
            if self.is_opening or self.is_closing:
                icon = ICON_PATH + "/move.png"
            else:
                tilt = self._steps_to_tilt(self._tilt_step)
                if tilt <= 15:
                    icon = ICON_PATH + "/00.png"
                elif tilt <= 40:
                    icon = ICON_PATH + "/25.png"
                elif tilt <= 60:
                    icon = ICON_PATH + "/50.png"
                elif tilt <= 85:
                    icon = ICON_PATH + "/75.png"
                else:
                    icon = ICON_PATH + "/99.png"
            _LOGGER.debug("Returned icon attribute = " + icon)
        else:
            icon = None
        return icon

    async def _async_tilt_blind_to_step(self, steps, target):
        """Callback to tilt the blind to some position"""
        _LOGGER.info("LOUVOLITE TILTING BLIND")
        if target == 0:
            movement = STATE_CLOSING
            command = CMD_VOGUE_CLOSE_CCW
        elif target == 1:
            movement = STATE_OPENING
            command = CMD_VOGUE_45_DEGREES
        elif target == 2:
            movement = STATE_OPENING
            command = CMD_VOGUE_90_DEGREES
        elif target == 3:
            movement = STATE_OPENING
            command = CMD_VOGUE_135_DEGREES
        else:
            movement = STATE_CLOSING
            command = CMD_VOGUE_CLOSE_CW

        delay = self._blindOpenSecs if steps <= 2 else self._blindCloseSecs

        await self._set_state(movement, BLIND_POS_CLOSED, self._tilt_step)
        await self._async_send(self._device.send_command, command)
        await self._wait_and_set_state(delay, movement, STATE_CLOSED, BLIND_POS_CLOSED, target)
        return target

    async def _async_do_close_blind(self):
        """Callback to close the blind"""
        _LOGGER.info("LOUVOLITE CLOSING BLIND")
        await self._set_state(STATE_CLOSING, BLIND_POS_CLOSED, self._tilt_step)
        await self._async_send(self._device.send_command, CMD_VOGUE_CLOSE_CCW)
        return self._blindCloseSecs

    async def _async_do_open_blind(self):
        """Callback to open the blind"""
        _LOGGER.info("LOUVOLITE OPENING BLIND")
        await self._set_state(STATE_OPENING, BLIND_POS_CLOSED, self._tilt_step)
        await self._async_send(self._device.send_command, CMD_VOGUE_90_DEGREES)
        return self._blindOpenSecs

    async def _async_do_tilt_blind_to_mid(self):
        """Callback to tilt the blind to mid"""
        _LOGGER.info("LOUVOLITE TILTING BLIND TO MID")
        await self._set_state(STATE_OPENING, BLIND_POS_CLOSED, self._tilt_step)
        await self._async_send(self._device.send_command, CMD_VOGUE_90_DEGREES)
        return self._blindOpenSecs
